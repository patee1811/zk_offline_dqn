use std::fs;
use std::path::{Path, PathBuf};
use std::process::Command;
use std::time::Instant;

use anyhow::{anyhow, Context, Result};
use clap::Parser;
use serde_json::json;
use sp1_sdk::{
    include_elf, HashableKey, ProveRequest, Prover, ProverClient, ProvingKey, SP1Proof,
    SP1ProofWithPublicValues, SP1Stdin, SP1VerifyingKey,
};
use training_aggregation_shared::{
    verify_training_aggregation, TrainingAggregationInput, TrainingAggregationOutput,
};

#[derive(Debug, Parser)]
struct Args {
    #[arg(long, value_name = "PATH")]
    case: Option<PathBuf>,
    #[arg(long)]
    execute: bool,
    #[arg(long)]
    prove: bool,
    #[arg(long, value_name = "DIR")]
    out_dir: Option<PathBuf>,
    #[arg(long, default_value = "proof_manifest_chain")]
    mode: String,
    #[arg(long)]
    child_proof_mode: Option<String>,
    #[arg(long)]
    topology: Option<String>,
    #[arg(long)]
    skip_host_precheck: bool,
}

#[tokio::main]
async fn main() -> Result<()> {
    let args = Args::parse();
    if !matches!(args.mode.as_str(), "proof_manifest_chain" | "recursive_sp1") {
        return Err(anyhow!(
            "unsupported --mode {}; expected proof_manifest_chain or recursive_sp1",
            args.mode
        ));
    }
    let case_path = resolve_case_path(args.case.clone())?;
    let input = load_input(&case_path)?;
    if input.public_inputs.aggregation_mode != args.mode {
        return Err(anyhow!("--mode does not match case aggregation_mode"));
    }
    if let Some(child_proof_mode) = args.child_proof_mode.as_deref() {
        if input.public_inputs.child_proof_mode.as_deref() != Some(child_proof_mode) {
            return Err(anyhow!(
                "--child-proof-mode does not match case child_proof_mode"
            ));
        }
    }
    if let Some(topology) = args.topology.as_deref() {
        if input.public_inputs.aggregation_topology.as_deref() != Some(topology) {
            return Err(anyhow!(
                "--topology does not match case aggregation_topology"
            ));
        }
    }
    println!("case_path = {}", case_path.display());
    let expected = verify_training_aggregation(&input);
    if !args.skip_host_precheck {
        println!("host_precheck = true");
        println!("aggregation_mode = {}", expected.aggregation_mode);
        println!("chunk_count = {}", expected.chunk_count);
        println!("step_end = {}", expected.step_end);
        println!("aggregate_root = {}", expected.aggregate_root);
    } else {
        println!("host_precheck = skipped");
    }

    // CPU stays the default so every committed provenance number keeps the
    // prover it was measured on. SP1_CUDA=1 opts into the GPU prover, which is
    // the open question for native recursion: the 615M-cycle aggregate ran out
    // of memory at both 30 GB and 61 GB of host RAM. The GPU path needs CUDA
    // compute capability >= 8.0 and 24 GB VRAM, so it is not a drop-in swap.
    let use_cuda = std::env::var("SP1_CUDA").map(|v| v == "1").unwrap_or(false);
    if use_cuda {
        println!("prover = cuda");
        let client = ProverClient::builder().cuda().build().await;
        run_with_prover(client, &args, &input, &expected, &case_path).await
    } else {
        println!("prover = cpu");
        let client = ProverClient::builder().cpu().build().await;
        run_with_prover(client, &args, &input, &expected, &case_path).await
    }
}

/// Execute and optionally prove with whichever prover was selected.
///
/// CPU and CUDA build different concrete types and `Prover` has associated
/// types, so this cannot be a boxed trait object -- the selection has to be a
/// generic call from each branch.
async fn run_with_prover<P: Prover>(
    client: P,
    args: &Args,
    input: &TrainingAggregationInput,
    expected: &TrainingAggregationOutput,
    case_path: &Path,
) -> Result<()> {
    let elf = include_elf!("training-aggregation-guest");
    let mut cycle_count: Option<u64> = None;

    if args.execute || args.prove || !args.prove {
        let stdin = build_stdin(input)?;
        let start = Instant::now();
        let (mut public_values, report) = client
            .execute(elf.clone(), stdin)
            .await
            .context("SP1 execution failed")?;
        let output = public_values.read::<TrainingAggregationOutput>();
        if output != *expected {
            return Err(anyhow!("SP1 public output did not match expected output"));
        }
        cycle_count = Some(report.total_instruction_count());
        println!("execution_ok = true");
        println!("execution_time_sec = {:.6}", start.elapsed().as_secs_f64());
        println!("cycle_count = {}", report.total_instruction_count());
        println!("exit_code = {}", report.exit_code);
        if report.exit_code != 0 {
            return Err(anyhow!("SP1 execution rejected case"));
        }
    }

    if args.prove {
        let out_dir = args.out_dir.clone().unwrap_or_else(|| {
            PathBuf::from(
                if input.public_inputs.aggregation_topology.as_deref() == Some("binary_tree") {
                    format!(
                        "artifacts/reports/provenance/sp1/training_aggregation_binary_native_t{}",
                        input.public_inputs.step_end
                    )
                } else if input.public_inputs.aggregation_mode == "recursive_sp1" {
                    format!(
                        "artifacts/reports/provenance/sp1/training_aggregation_recursive_t{}",
                        input.public_inputs.step_end
                    )
                } else {
                    format!(
                        "artifacts/reports/provenance/sp1/training_aggregation_t{}",
                        input.public_inputs.step_end
                    )
                },
            )
        });
        fs::create_dir_all(&out_dir)
            .with_context(|| format!("failed to create {}", out_dir.display()))?;
        let stdin = build_stdin(input)?;
        let pk = client.setup(elf).await.map_err(|e| anyhow!("SP1 setup failed: {e}"))?;
        let prove_start = Instant::now();
        let proof = if input.public_inputs.aggregation_mode == "recursive_sp1"
            && input.public_inputs.child_proof_mode.as_deref() == Some("native_sp1")
        {
            client
                .prove(&pk, stdin)
                .compressed()
                .await
                .map_err(|e| anyhow!("SP1 recursive aggregate proof generation failed: {e}"))?
        } else {
            client
                .prove(&pk, stdin)
                .await
                .map_err(|e| anyhow!("SP1 proof generation failed: {e}"))?
        };
        let proving_time_sec = prove_start.elapsed().as_secs_f64();
        let verify_start = Instant::now();
        client
            .verify(&proof, pk.verifying_key(), None)
            .context("SP1 proof verification failed")?;
        let verification_time_sec = verify_start.elapsed().as_secs_f64();
        let proof_path = out_dir.join("proof.bin");
        proof
            .save(&proof_path)
            .with_context(|| format!("failed to save {}", proof_path.display()))?;
        let proof_size_bytes = fs::metadata(&proof_path)?.len();
        if input.public_inputs.aggregation_topology.as_deref() == Some("binary_tree")
            && input.public_inputs.child_proof_mode.as_deref() == Some("native_sp1")
            && input.public_inputs.node_id.as_deref() != Some("root")
        {
            write_native_recursive_child_material(&out_dir, &proof, &pk, expected)?;
        }
        write_provenance(
            &out_dir,
            input,
            expected,
            proving_time_sec,
            verification_time_sec,
            proof_size_bytes,
            cycle_count,
            case_path,
        )?;
        println!("proof_generated = true");
        println!("proof_verified = true");
        println!("proving_time_sec = {:.6}", proving_time_sec);
        println!("verification_time_sec = {:.6}", verification_time_sec);
        println!("proof_size_bytes = {}", proof_size_bytes);
    }
    Ok(())
}

fn write_native_recursive_child_material(
    out_dir: &Path,
    proof: &SP1ProofWithPublicValues,
    pk: &impl ProvingKey,
    expected: &TrainingAggregationOutput,
) -> Result<()> {
    if !matches!(&proof.proof, SP1Proof::Compressed(_)) {
        return Err(anyhow!(
            "native recursive aggregation child material requires a compressed SP1 proof"
        ));
    }
    write_json(
        out_dir.join("recursive_child_proof_material.json"),
        &json!({
            "proof_mode": "native_sp1",
            "proof_bytes": hex::encode(bincode::serialize(proof)?),
            "public_values_bytes": hex::encode(proof.public_values.to_vec()),
            "vkey_hash": pk.verifying_key().bytes32(),
            "vkey_digest_words": pk.verifying_key().hash_u32(),
            "vkey_bytes": hex::encode(bincode::serialize(pk.verifying_key())?),
            "public_output": expected,
        }),
    )
}

fn build_stdin(input: &TrainingAggregationInput) -> Result<SP1Stdin> {
    let mut stdin = SP1Stdin::new();
    stdin.write(input);
    if input.public_inputs.aggregation_mode == "recursive_sp1" {
        for child in &input.private_witness.child_proofs {
            if child.proof_mode != "native_sp1" {
                continue;
            }
            let proof_bytes = hex::decode(&child.proof_bytes)
                .context("failed to decode native child proof bytes")?;
            let proof: SP1ProofWithPublicValues = bincode::deserialize(&proof_bytes)
                .context("failed to decode native child SP1 proof")?;
            let recursion_proof = match proof.proof {
                SP1Proof::Compressed(proof) => *proof,
                _ => return Err(anyhow!("native child proof is not compressed")),
            };
            let vkey_bytes =
                hex::decode(&child.vkey_bytes).context("failed to decode child vkey bytes")?;
            let vkey: SP1VerifyingKey =
                bincode::deserialize(&vkey_bytes).context("failed to decode child vkey")?;
            if child.vkey_hash != vkey.bytes32() {
                return Err(anyhow!("child vkey hash does not match vkey bytes"));
            }
            if child.vkey_digest_words.as_slice() != vkey.hash_u32().as_slice() {
                return Err(anyhow!("child vkey digest does not match vkey bytes"));
            }
            if proof.public_values.to_vec() != hex::decode(&child.public_values_bytes)? {
                return Err(anyhow!(
                    "child public values do not match compressed proof material"
                ));
            }
            stdin.write_proof(recursion_proof, vkey.vk);
        }
    }
    Ok(stdin)
}

fn load_input(path: &Path) -> Result<TrainingAggregationInput> {
    let text =
        fs::read_to_string(path).with_context(|| format!("failed to read {}", path.display()))?;
    serde_json::from_str(&text).with_context(|| format!("failed to parse {}", path.display()))
}

fn resolve_case_path(case: Option<PathBuf>) -> Result<PathBuf> {
    if let Some(path) = case {
        return Ok(path);
    }
    let candidates = [
        PathBuf::from("../../test_vectors/training_aggregation_t32_case_0.json"),
        PathBuf::from("zk_backend/test_vectors/training_aggregation_t32_case_0.json"),
    ];
    for candidate in candidates {
        if candidate.exists() {
            return Ok(candidate);
        }
    }
    Err(anyhow!(
        "could not find training_aggregation_t32_case_0.json"
    ))
}

#[allow(clippy::too_many_arguments)]
fn write_provenance(
    out_dir: &Path,
    input: &TrainingAggregationInput,
    expected: &TrainingAggregationOutput,
    proving_time_sec: f64,
    verification_time_sec: f64,
    proof_size_bytes: u64,
    cycle_count: Option<u64>,
    case_path: &Path,
) -> Result<()> {
    let recursive = input.public_inputs.aggregation_mode == "recursive_sp1";
    let binary = input.public_inputs.aggregation_topology.as_deref() == Some("binary_tree");
    write_json(out_dir.join("public_inputs.json"), &input.public_inputs)?;
    write_json(
        out_dir.join("witness_schema.json"),
        &witness_schema(recursive),
    )?;
    write_json(
        out_dir.join("metrics.json"),
        &json!({
            "relation": "training_aggregation",
            "aggregation_mode": input.public_inputs.aggregation_mode,
            "aggregation_topology": input.public_inputs.aggregation_topology,
            "child_proof_mode": input.public_inputs.child_proof_mode,
            "chunk_size": input.public_inputs.chunk_size,
            "chunk_count": input.public_inputs.chunk_count,
            "leaf_chunk_count": input.public_inputs.leaf_chunk_count,
            "tree_depth": input.public_inputs.node_depth,
            "step_start": input.public_inputs.step_start,
            "step_end": input.public_inputs.step_end,
            "proof_generated": true,
            "proof_verified": true,
            "prove_time_seconds": proving_time_sec,
            "verify_time_seconds": verification_time_sec,
            "proof_size_bytes": proof_size_bytes,
            "cycle_count": cycle_count,
            "backend_version": env!("CARGO_PKG_VERSION"),
            "sp1_version": "6.1.0",
            "git_commit": git_commit(),
            "test_vector_sha256": sha256_file(case_path)?,
            "public_inputs_sha256": sha256_json(&input.public_inputs)?,
            "child_proof_count": input.private_witness.child_proofs.len(),
            "child_proof_verification_inside_guest": recursive,
            "binary_tree_internal_node_count": if binary {
                input.public_inputs.leaf_chunk_count.unwrap_or(0).saturating_sub(1)
            } else {
                0
            },
            "notes": [if recursive {
                format!(
                    "SP1 true recursive aggregation; {} child training-fragment proofs are verified inside the aggregate guest.",
                    input.public_inputs.child_proof_mode.as_deref().unwrap_or("unknown")
                )
            } else {
                "SP1 proof-backed proof-manifest chunk-chain aggregation; child proof cryptography is not recursively verified inside SP1.".to_owned()
            }]
        }),
    )?;
    write_json(
        out_dir.join("verify_report.json"),
        &json!({
            "relation": "training_aggregation",
            "aggregation_mode": input.public_inputs.aggregation_mode,
            "aggregation_topology": input.public_inputs.aggregation_topology,
            "chunk_size": input.public_inputs.chunk_size,
            "chunk_count": input.public_inputs.chunk_count,
            "step_start": input.public_inputs.step_start,
            "step_end": input.public_inputs.step_end,
            "proof_generated": true,
            "proof_verified": true,
            "public_output_matches_expected": true,
            "child_proof_verification_inside_guest": recursive,
            "computation_covered": {
                "chunk_ordering": true,
                "checkpoint_chaining": true,
                "target_checkpoint_chaining": true,
                "dataset_config_consistency": true,
                "aggregate_root_binding": true,
                "proof_provenance_hash_binding": true,
                "recursive_child_proof_verification": recursive
            },
            "public_output": expected,
        }),
    )?;
    write_json(
        out_dir.join("proof_artifact_policy.json"),
        &json!({
            "proof_binary_committed": false,
            "reason": "proof binary is generated artifact and may be large",
            "expected_runtime_location": if recursive {
                recursive_proof_runtime_location(input)
            } else {
                format!("artifacts/kaggle_phase7_outputs/extracted/phase7_outputs/sp1/training_aggregation_t{}/proof.bin", input.public_inputs.step_end)
            }
        }),
    )?;
    write_json(
        out_dir.join("aggregation_manifest.json"),
        &json!({
            "relation": "training_aggregation",
            "aggregation_mode": input.public_inputs.aggregation_mode,
            "aggregation_topology": input.public_inputs.aggregation_topology,
            "chunk_relation_id": input.public_inputs.chunk_relation_id,
            "chunk_size": input.public_inputs.chunk_size,
            "chunk_count": input.public_inputs.chunk_count,
            "step_start": input.public_inputs.step_start,
            "step_end": input.public_inputs.step_end,
            "aggregate_root": input.public_inputs.aggregate_root,
            "chunk_public_inputs_root": input.public_inputs.chunk_public_inputs_root,
            "chunk_proof_root": input.public_inputs.chunk_proof_root,
            "chunk_verify_report_root": input.public_inputs.chunk_verify_report_root,
            "chunk_vkey_root": input.public_inputs.chunk_vkey_root,
            "child_proof_mode": input.public_inputs.child_proof_mode,
            "expected_child_vkey_hash": input.public_inputs.expected_child_vkey_hash,
            "expected_child_vkey_digest_words": input.public_inputs.expected_child_vkey_digest_words,
            "tree_root_hash": input.public_inputs.tree_root_hash,
            "child_proof_verification_inside_guest": recursive,
            "claim_scope": input.public_inputs.claim_scope,
            "proof_hash_note": if recursive {
                "chunk child_proof_hash values bind recursive child proof material verified inside the aggregate guest."
            } else {
                "chunk proof_hash values bind child proof-manifest metadata derived from externally verified k=8 proof provenance; proof bytes are not recursively verified here."
            }
        }),
    )?;
    write_json(
        out_dir.join("chunk_manifest.json"),
        &json!({
            "relation": "training_aggregation",
            "aggregation_mode": input.public_inputs.aggregation_mode,
            "chunks": input.private_witness.chunks,
        }),
    )?;
    if recursive {
        write_json(
            out_dir.join("recursive_child_proof_manifest.json"),
            &json!({
                "relation": "training_aggregation",
                "aggregation_mode": "recursive_sp1",
                "child_proof_mode": input.public_inputs.child_proof_mode,
                "expected_child_vkey_hash": input.public_inputs.expected_child_vkey_hash,
                "child_proof_count": input.private_witness.child_proofs.len(),
                "children": input.private_witness.chunks.iter().map(|chunk| json!({
                    "chunk_id": chunk.chunk_id,
                    "step_start": chunk.step_start,
                    "step_end": chunk.step_end,
                    "child_public_inputs_hash": chunk.child_public_inputs_hash,
                    "child_vkey_hash": chunk.child_vkey_hash,
                    "child_proof_hash": chunk.child_proof_hash,
                    "proof_bytes_committed": false
                })).collect::<Vec<_>>()
            }),
        )?;
    }
    if binary {
        write_json(
            out_dir.join("binary_tree_manifest.json"),
            &json!({
                "relation": "training_aggregation",
                "aggregation_mode": "recursive_sp1",
                "aggregation_topology": "binary_tree",
                "child_proof_mode": "native_sp1",
                "node_id": input.public_inputs.node_id,
                "node_depth": input.public_inputs.node_depth,
                "node_range_start": input.public_inputs.node_range_start,
                "node_range_end": input.public_inputs.node_range_end,
                "leaf_chunk_count": input.public_inputs.leaf_chunk_count,
                "binary_tree_fan_in": 2,
                "tree_root_hash": input.public_inputs.tree_root_hash,
                "children": input.private_witness.chunks.iter().map(|chunk| json!({
                    "chunk_id": chunk.chunk_id,
                    "relation_id": chunk.relation_id,
                    "step_start": chunk.step_start,
                    "step_end": chunk.step_end,
                    "child_public_inputs_hash": chunk.child_public_inputs_hash,
                    "child_proof_hash": chunk.child_proof_hash,
                    "child_vkey_hash": chunk.child_vkey_hash
                })).collect::<Vec<_>>()
            }),
        )?;
    }
    Ok(())
}

fn witness_schema(recursive: bool) -> serde_json::Value {
    if recursive {
        return json!({
            "schema_version": "sp1_training_aggregation_recursive_witness_schema_v1",
            "relation": "training_aggregation",
            "aggregation_mode": "recursive_sp1",
            "aggregation_topology": "recursive aggregate cases may opt into binary_tree",
            "private_witness": {
                "chunks": [{
                    "chunk_id": "sequential k=8 child chunk id checked by guest",
                    "step_start": "must match child training-fragment public global_step_start",
                    "step_end": "must match child training-fragment public span",
                    "input_checkpoint_hash": "must match child public start checkpoint",
                    "output_checkpoint_hash": "must match child public final checkpoint",
                    "child_public_inputs_hash": "sha256 of child public-values bytes",
                    "child_vkey_hash": "SP1 training-fragment vkey hash checked by the child verifier",
                    "child_proof_hash": "sha256 of recursive child proof bytes"
                }],
                "child_proofs": [{
                    "proof_bytes": "private native compressed, Groth16, or Plonk SP1 proof bytes",
                    "public_values_bytes": "private SP1 public values hashed, verified, and decoded in guest",
                    "vkey_hash": "private proof vkey hash checked against aggregation public input",
                    "vkey_digest_words": "native SP1 only: vkey digest passed to verify_sp1_proof",
                    "vkey_bytes": "native SP1 only: serialized child verifying key used by the host to attach the child proof"
                }]
            },
            "public_inputs": "aggregate boundaries, recursive child roots, and expected child vkey material",
            "notes": ["The aggregate guest verifies each recursive child proof and the online/target checkpoint chain."]
        });
    }
    json!({
        "schema_version": "sp1_training_aggregation_witness_schema_v1",
        "relation": "training_aggregation",
        "aggregation_mode": "proof_manifest_chain",
        "private_witness": {
            "chunks": [{
                "chunk_id": "sequential k=8 child chunk id checked by guest",
                "step_start": "chunk start step",
                "step_end": "chunk end step",
                "input_checkpoint_hash": "online checkpoint entering the child chunk",
                "output_checkpoint_hash": "online checkpoint leaving the child chunk",
                "input_target_checkpoint_hash": "target checkpoint entering the child chunk",
                "output_target_checkpoint_hash": "target checkpoint leaving the child chunk",
                "dataset_root": "must equal aggregation public dataset_root",
                "config_hash": "must equal aggregation public config_hash",
                "proof_hash": "child proof-manifest hash bound by aggregation, not recursively verified proof bytes",
                "public_inputs_hash": "child public-input record hash",
                "verify_report_hash": "externally verified child proof report hash"
            }],
            "child_proofs": "empty in proof_manifest_chain mode"
        },
        "public_inputs": "aggregate boundaries, provenance/config hashes, chunk roots, and honest claim scope",
        "notes": ["The guest enforces ordering and checkpoint links across k=8 chunk manifests. It does not verify child proof cryptography."]
    })
}

fn write_json<T: serde::Serialize>(path: PathBuf, value: &T) -> Result<()> {
    fs::write(&path, format!("{}\n", serde_json::to_string_pretty(value)?))
        .with_context(|| format!("failed to write {}", path.display()))
}

fn sha256_json<T: serde::Serialize>(value: &T) -> Result<String> {
    Ok(hex_sha256(&serde_json::to_vec(value)?))
}

fn sha256_file(path: &Path) -> Result<String> {
    Ok(hex_sha256(&fs::read(path)?))
}

fn hex_sha256(bytes: &[u8]) -> String {
    use sha2::{Digest, Sha256};
    hex::encode(Sha256::digest(bytes))
}

fn git_commit() -> Option<String> {
    let output = Command::new("git")
        .args(["rev-parse", "HEAD"])
        .output()
        .ok()?;
    if !output.status.success() {
        return None;
    }
    Some(String::from_utf8_lossy(&output.stdout).trim().to_owned())
}

fn recursive_proof_runtime_location(input: &TrainingAggregationInput) -> String {
    match input.public_inputs.child_proof_mode.as_deref() {
        Some("groth16_bn254") => format!(
            "artifacts/kaggle_phase7_groth16_t16_t32_outputs/extracted/phase7_groth16_t16_t32_outputs/sp1/training_aggregation_groth16_t{}/proof.bin",
            input.public_inputs.step_end
        ),
        Some("plonk_bn254") => format!(
            "artifacts/kaggle_phase7_plonk_t16_t32_outputs/extracted/phase7_plonk_t16_t32_outputs/sp1/training_aggregation_plonk_t{}/proof.bin",
            input.public_inputs.step_end
        ),
        Some("native_sp1")
            if input.public_inputs.aggregation_topology.as_deref() == Some("binary_tree") =>
        {
            format!(
                "artifacts/kaggle_phase7_binary_native_outputs/extracted/phase7_binary_native_outputs/sp1/training_aggregation_binary_native_t{}/proof.bin",
                input.public_inputs.step_end
            )
        }
        _ => format!(
            "artifacts/kaggle_phase7_recursive_outputs/extracted/phase7_recursive_outputs/sp1/training_aggregation_recursive_t{}/proof.bin",
            input.public_inputs.step_end
        ),
    }
}

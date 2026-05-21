use std::fs;
use std::path::{Path, PathBuf};
use std::process::Command;
use std::time::Instant;

use anyhow::{anyhow, Context, Result};
use clap::Parser;
use serde_json::json;
use sp1_sdk::{include_elf, Prover, ProverClient, ProvingKey, SP1Stdin};
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
    skip_host_precheck: bool,
}

#[tokio::main]
async fn main() -> Result<()> {
    let args = Args::parse();
    if args.mode != "proof_manifest_chain" {
        return Err(anyhow!(
            "recursive_sp1 mode is unavailable because child proofs are not verified inside the guest"
        ));
    }
    let case_path = resolve_case_path(args.case)?;
    let input = load_input(&case_path)?;
    if input.public_inputs.aggregation_mode != args.mode {
        return Err(anyhow!("--mode does not match case aggregation_mode"));
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

    let client = ProverClient::builder().cpu().build().await;
    let elf = include_elf!("training-aggregation-guest");
    let mut cycle_count: Option<u64> = None;

    if args.execute || args.prove || !args.prove {
        let stdin = build_stdin(&input);
        let start = Instant::now();
        let (mut public_values, report) = client
            .execute(elf.clone(), stdin)
            .await
            .context("SP1 execution failed")?;
        let output = public_values.read::<TrainingAggregationOutput>();
        if output != expected {
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
            PathBuf::from(format!(
                "artifacts/reports/provenance/sp1/training_aggregation_t{}",
                input.public_inputs.step_end
            ))
        });
        fs::create_dir_all(&out_dir)
            .with_context(|| format!("failed to create {}", out_dir.display()))?;
        let stdin = build_stdin(&input);
        let pk = client.setup(elf).await.context("SP1 setup failed")?;
        let prove_start = Instant::now();
        let proof = client
            .prove(&pk, stdin)
            .await
            .context("SP1 proof generation failed")?;
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
        write_provenance(
            &out_dir,
            &input,
            &expected,
            proving_time_sec,
            verification_time_sec,
            proof_size_bytes,
            cycle_count,
            &case_path,
        )?;
        println!("proof_generated = true");
        println!("proof_verified = true");
        println!("proving_time_sec = {:.6}", proving_time_sec);
        println!("verification_time_sec = {:.6}", verification_time_sec);
        println!("proof_size_bytes = {}", proof_size_bytes);
    }
    Ok(())
}

fn build_stdin(input: &TrainingAggregationInput) -> SP1Stdin {
    let mut stdin = SP1Stdin::new();
    stdin.write(input);
    stdin
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
    write_json(out_dir.join("public_inputs.json"), &input.public_inputs)?;
    write_json(out_dir.join("witness_schema.json"), &witness_schema())?;
    write_json(
        out_dir.join("metrics.json"),
        &json!({
            "relation": "training_aggregation",
            "aggregation_mode": input.public_inputs.aggregation_mode,
            "chunk_size": input.public_inputs.chunk_size,
            "chunk_count": input.public_inputs.chunk_count,
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
            "child_proof_count": input.public_inputs.chunk_count,
            "child_proof_verification_inside_guest": false,
            "notes": ["SP1 proof-backed proof-manifest chunk-chain aggregation; child proof cryptography is not recursively verified inside SP1."]
        }),
    )?;
    write_json(
        out_dir.join("verify_report.json"),
        &json!({
            "relation": "training_aggregation",
            "aggregation_mode": input.public_inputs.aggregation_mode,
            "chunk_size": input.public_inputs.chunk_size,
            "chunk_count": input.public_inputs.chunk_count,
            "step_start": input.public_inputs.step_start,
            "step_end": input.public_inputs.step_end,
            "proof_generated": true,
            "proof_verified": true,
            "public_output_matches_expected": true,
            "child_proof_verification_inside_guest": false,
            "computation_covered": {
                "chunk_ordering": true,
                "checkpoint_chaining": true,
                "target_checkpoint_chaining": true,
                "dataset_config_consistency": true,
                "aggregate_root_binding": true,
                "proof_provenance_hash_binding": true,
                "recursive_child_proof_verification": false
            },
            "public_output": expected,
        }),
    )?;
    write_json(
        out_dir.join("proof_artifact_policy.json"),
        &json!({
            "proof_binary_committed": false,
            "reason": "proof binary is generated artifact and may be large",
            "expected_runtime_location": format!("artifacts/kaggle_phase7_outputs/extracted/phase7_outputs/sp1/training_aggregation_t{}/proof.bin", input.public_inputs.step_end)
        }),
    )?;
    write_json(
        out_dir.join("aggregation_manifest.json"),
        &json!({
            "relation": "training_aggregation",
            "aggregation_mode": "proof_manifest_chain",
            "chunk_relation_id": input.public_inputs.chunk_relation_id,
            "chunk_size": input.public_inputs.chunk_size,
            "chunk_count": input.public_inputs.chunk_count,
            "step_start": input.public_inputs.step_start,
            "step_end": input.public_inputs.step_end,
            "aggregate_root": input.public_inputs.aggregate_root,
            "chunk_public_inputs_root": input.public_inputs.chunk_public_inputs_root,
            "chunk_proof_root": input.public_inputs.chunk_proof_root,
            "chunk_verify_report_root": input.public_inputs.chunk_verify_report_root,
            "child_proof_verification_inside_guest": false,
            "claim_scope": input.public_inputs.claim_scope,
            "proof_hash_note": "chunk proof_hash values bind child proof-manifest metadata derived from externally verified k=8 proof provenance; proof bytes are not recursively verified here."
        }),
    )?;
    write_json(
        out_dir.join("chunk_manifest.json"),
        &json!({
            "relation": "training_aggregation",
            "aggregation_mode": "proof_manifest_chain",
            "chunks": input.private_witness.chunks,
        }),
    )?;
    Ok(())
}

fn witness_schema() -> serde_json::Value {
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

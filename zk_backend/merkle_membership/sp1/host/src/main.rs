use std::fs;
use std::path::{Path, PathBuf};
use std::process::Command;
use std::time::Instant;

use anyhow::{anyhow, Context, Result};
use clap::Parser;
use merkle_membership_shared::{
    expected_public_output, verify_merkle_membership, MerkleMembershipInput,
    MerkleMembershipOutput, MerkleMembershipPublicInputs,
};
use serde_json::json;
use sp1_sdk::{include_elf, Prover, ProverClient, ProvingKey, SP1Stdin};

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

    #[arg(long, value_name = "PATH")]
    expected_public_inputs: Option<PathBuf>,

    #[arg(long)]
    skip_host_precheck: bool,
}

#[tokio::main]
async fn main() -> Result<()> {
    let args = Args::parse();
    let case_path = resolve_case_path(args.case)?;
    let input = load_input(&case_path)?;

    println!("case_path = {}", case_path.display());
    if !args.skip_host_precheck {
        let expected = verify_merkle_membership(&input);
        println!("host_precheck = true");
        println!("dataset_root = {}", expected.dataset_root);
        println!("leaf_hash = {}", expected.leaf_hash);
    } else {
        println!("host_precheck = skipped");
    }

    let client = ProverClient::builder().cpu().build().await;
    let elf = include_elf!("merkle-membership-guest");
    let expected = if let Some(path) = &args.expected_public_inputs {
        expected_public_output_from_public_inputs(&load_public_inputs(path)?)
    } else {
        expected_public_output(&input)
    };
    let mut cycle_count: Option<u64> = None;

    if args.execute || !args.prove {
        let stdin = build_stdin(&input);
        let start = Instant::now();
        let (mut public_values, report) = client
            .execute(elf.clone(), stdin)
            .await
            .context("SP1 execution failed")?;
        let output = public_values.read::<MerkleMembershipOutput>();
        if output != expected {
            return Err(anyhow!(
                "SP1 public output did not match expected public inputs"
            ));
        }
        cycle_count = Some(report.total_instruction_count());
        println!("execution_ok = true");
        println!("execution_time_sec = {:.6}", start.elapsed().as_secs_f64());
        println!("cycle_count = {}", report.total_instruction_count());
        println!("exit_code = {}", report.exit_code);
        if report.exit_code != 0 {
            return Err(anyhow!(
                "SP1 execution rejected case with exit_code={}",
                report.exit_code
            ));
        }
    }

    if args.prove {
        let out_dir = args
            .out_dir
            .clone()
            .unwrap_or_else(|| PathBuf::from("artifacts/reports/provenance/sp1/merkle_membership"));
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
        let proof_size_bytes = fs::metadata(&proof_path)
            .with_context(|| format!("failed to stat {}", proof_path.display()))?
            .len();

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

fn build_stdin(input: &MerkleMembershipInput) -> SP1Stdin {
    let mut stdin = SP1Stdin::new();
    stdin.write(input);
    stdin
}

fn load_input(path: &Path) -> Result<MerkleMembershipInput> {
    let text =
        fs::read_to_string(path).with_context(|| format!("failed to read {}", path.display()))?;
    serde_json::from_str(&text).with_context(|| format!("failed to parse {}", path.display()))
}

fn load_public_inputs(path: &Path) -> Result<MerkleMembershipPublicInputs> {
    let text =
        fs::read_to_string(path).with_context(|| format!("failed to read {}", path.display()))?;
    serde_json::from_str(&text).with_context(|| format!("failed to parse {}", path.display()))
}

fn expected_public_output_from_public_inputs(
    public_inputs: &MerkleMembershipPublicInputs,
) -> MerkleMembershipOutput {
    MerkleMembershipOutput {
        schema_version: "sp1_merkle_membership_public_v1".to_owned(),
        dataset_id: public_inputs.dataset_id.clone(),
        dataset_type: public_inputs.dataset_type.clone(),
        dataset_root: public_inputs.dataset_root.clone(),
        manifest_hash: public_inputs.manifest_hash.clone(),
        audit_report_hash: public_inputs.audit_report_hash.clone(),
        collection_log_final_hash: public_inputs.collection_log_final_hash.clone(),
        raw_trajectory_hash: public_inputs.raw_trajectory_hash.clone(),
        leaf_hash: public_inputs.leaf_hash.clone(),
        leaf_index: public_inputs.leaf_index,
    }
}

fn resolve_case_path(case: Option<PathBuf>) -> Result<PathBuf> {
    if let Some(path) = case {
        return Ok(path);
    }
    let candidates = [
        PathBuf::from("zk_backend/test_vectors/merkle_membership_case_0.json"),
        PathBuf::from("../../test_vectors/merkle_membership_case_0.json"),
        PathBuf::from("../../../test_vectors/merkle_membership_case_0.json"),
        PathBuf::from("../test_vectors/merkle_membership_case_0.json"),
    ];
    for candidate in candidates {
        if candidate.exists() {
            return Ok(candidate);
        }
    }
    Err(anyhow!(
        "could not find merkle_membership_case_0.json; pass --case explicitly"
    ))
}

fn write_provenance(
    out_dir: &Path,
    input: &MerkleMembershipInput,
    expected: &MerkleMembershipOutput,
    proving_time_sec: f64,
    verification_time_sec: f64,
    proof_size_bytes: u64,
    cycle_count: Option<u64>,
    case_path: &Path,
) -> Result<()> {
    write_json(out_dir.join("public_inputs.json"), &input.public_inputs)?;
    write_json(out_dir.join("witness_schema.json"), &witness_schema())?;
    let git_commit = git_commit();
    let test_vector_sha256 = sha256_file(case_path)?;
    let public_inputs_sha256 = sha256_json(&input.public_inputs)?;
    write_json(
        out_dir.join("metrics.json"),
        &json!({
            "relation": "merkle_membership",
            "proof_generated": true,
            "proof_verified": true,
            "prove_time_seconds": proving_time_sec,
            "verify_time_seconds": verification_time_sec,
            "proof_size_bytes": proof_size_bytes,
            "cycle_count": cycle_count,
            "backend_version": env!("CARGO_PKG_VERSION"),
            "sp1_version": "6.1.0",
            "git_commit": git_commit,
            "test_vector_sha256": test_vector_sha256,
            "public_inputs_sha256": public_inputs_sha256,
        }),
    )?;
    write_json(
        out_dir.join("verify_report.json"),
        &json!({
            "relation": "merkle_membership",
            "proof_generated": true,
            "proof_verified": true,
            "public_output_matches_expected": true,
            "public_output": expected,
        }),
    )?;
    write_json(
        out_dir.join("proof_artifact_policy.json"),
        &json!({
            "proof_binary_committed": false,
            "reason": "proof binary is generated artifact and may be large",
            "expected_runtime_location": "artifacts/kaggle_phase4_outputs/extracted/phase4_outputs/sp1/merkle_membership/proof.bin",
        }),
    )?;
    Ok(())
}

fn witness_schema() -> serde_json::Value {
    json!({
        "schema_version": "sp1_merkle_membership_witness_schema_v1",
        "relation": "merkle_membership",
        "claim": "canonical leaf hash authenticates to provenance-bound dataset_root",
        "private_witness": {
            "merkle_path": [
                {
                    "level": "u64",
                    "current_index": "u64",
                    "sibling_index": "u64",
                    "sibling_hash": "32-byte hex string",
                    "current_is_left": "bool"
                }
            ]
        },
        "public_inputs": {
            "dataset_id": "string",
            "dataset_type": "self_collected_replay_audited | public_benchmark",
            "dataset_root": "32-byte hex string",
            "manifest_hash": "32-byte hex string",
            "audit_report_hash": "32-byte hex string",
            "collection_log_final_hash": "nullable 32-byte hex string",
            "raw_trajectory_hash": "32-byte hex string",
            "leaf_hash": "32-byte hex string",
            "leaf_index": "u64"
        },
        "notes": [
            "Python computes the canonical transition hash for this phase.",
            "The SP1 guest proves leaf_hash/path membership and commits provenance public inputs."
        ]
    })
}

fn write_json<T: serde::Serialize>(path: PathBuf, value: &T) -> Result<()> {
    let text = serde_json::to_string_pretty(value)?;
    fs::write(&path, format!("{text}\n"))
        .with_context(|| format!("failed to write {}", path.display()))
}

fn sha256_json<T: serde::Serialize>(value: &T) -> Result<String> {
    let bytes = serde_json::to_vec(value)?;
    Ok(hex_sha256(&bytes))
}

fn sha256_file(path: &Path) -> Result<String> {
    let bytes = fs::read(path).with_context(|| format!("failed to read {}", path.display()))?;
    Ok(hex_sha256(&bytes))
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

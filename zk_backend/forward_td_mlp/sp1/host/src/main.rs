use std::fs;
use std::path::{Path, PathBuf};
use std::process::Command;
use std::time::Instant;

use anyhow::{anyhow, Context, Result};
use clap::Parser;
use forward_td_mlp_shared::{verify_forward_td_mlp, ForwardTdMlpOutput};
use serde_json::json;
use sp1_sdk::{include_elf, Prover, ProverClient, ProvingKey, SP1Stdin};
use td_mvp_shared::TdMvpInput;

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
    #[arg(long)]
    skip_host_precheck: bool,
}

#[tokio::main]
async fn main() -> Result<()> {
    let args = Args::parse();
    let case_path = resolve_case_path(args.case.clone())?;
    let input = load_input(&case_path)?;

    println!("case_path = {}", case_path.display());
    let expected = verify_forward_td_mlp(&input);
    if !args.skip_host_precheck {
        println!("host_precheck = true");
        println!("dataset_root = {}", expected.dataset_root);
        println!("claimed_batch_loss_fp = {}", expected.claimed_batch_loss_fp);
    } else {
        println!("host_precheck = skipped");
    }

    // CPU stays the default so every committed provenance number keeps the
    // prover it was measured on. SP1_CUDA=1 opts into the GPU prover, and the
    // row records which one produced it.
    let use_cuda = std::env::var("SP1_CUDA").map(|v| v == "1").unwrap_or(false);
    if use_cuda {
        println!("prover = cuda");
        let client = ProverClient::builder().cuda().build().await;
        run_with_prover(client, &args, &input, &expected, &case_path, "cuda").await
    } else {
        println!("prover = cpu");
        let client = ProverClient::builder().cpu().build().await;
        run_with_prover(client, &args, &input, &expected, &case_path, "cpu").await
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
    input: &TdMvpInput,
    expected: &ForwardTdMlpOutput,
    case_path: &Path,
    prover_label: &str,
) -> Result<()> {
    let elf = include_elf!("forward-td-mlp-guest");
    let guest_elf_sha256 = hex_sha256(&elf);
    let mut cycle_count: Option<u64> = None;

    if args.execute || args.prove || !args.prove {
        let stdin = build_stdin(input);
        let start = Instant::now();
        let (mut public_values, report) = client
            .execute(elf.clone(), stdin)
            .await
            .context("SP1 execution failed")?;
        let output = public_values.read::<ForwardTdMlpOutput>();
        if serde_json::to_value(&output)? != serde_json::to_value(expected)? {
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
        let out_dir = args
            .out_dir
            .clone()
            .unwrap_or_else(|| PathBuf::from("artifacts/reports/provenance/sp1/forward_td_mlp"));
        fs::create_dir_all(&out_dir)
            .with_context(|| format!("failed to create {}", out_dir.display()))?;

        let stdin = build_stdin(input);
        let pk = client
            .setup(elf)
            .await
            .map_err(|e| anyhow!("SP1 setup failed: {e}"))?;
        let prove_start = Instant::now();
        let proof = client
            .prove(&pk, stdin)
            .await
            .map_err(|e| anyhow!("SP1 proof generation failed: {e}"))?;
        let proving_time_sec = prove_start.elapsed().as_secs_f64();
        let verify_start = Instant::now();
        client
            .verify(&proof, pk.verifying_key(), None)
            .context("SP1 proof verification failed")?;
        let verification_time_sec = verify_start.elapsed().as_secs_f64();
        let proof_path = out_dir.join("proof.bin");
        proof.save(&proof_path)
            .with_context(|| format!("failed to save {}", proof_path.display()))?;
        let proof_size_bytes = fs::metadata(&proof_path)?.len();
        write_provenance(
            &out_dir,
            input,
            expected,
            proving_time_sec,
            verification_time_sec,
            proof_size_bytes,
            cycle_count,
            case_path,
            &guest_elf_sha256,
            prover_label,
        )?;
        println!("proof_generated = true");
        println!("proof_verified = true");
        println!("proving_time_sec = {:.6}", proving_time_sec);
        println!("verification_time_sec = {:.6}", verification_time_sec);
        println!("proof_size_bytes = {}", proof_size_bytes);
    }

    Ok(())
}

fn build_stdin(input: &TdMvpInput) -> SP1Stdin {
    let mut stdin = SP1Stdin::new();
    stdin.write(input);
    stdin
}

fn load_input(path: &Path) -> Result<TdMvpInput> {
    let text =
        fs::read_to_string(path).with_context(|| format!("failed to read {}", path.display()))?;
    serde_json::from_str(&text).with_context(|| format!("failed to parse {}", path.display()))
}

fn resolve_case_path(case: Option<PathBuf>) -> Result<PathBuf> {
    if let Some(path) = case {
        return Ok(path);
    }
    let candidates = [
        PathBuf::from("../../test_vectors/forward_td_mlp_case_0.json"),
        PathBuf::from("zk_backend/test_vectors/forward_td_mlp_case_0.json"),
    ];
    for candidate in candidates {
        if candidate.exists() {
            return Ok(candidate);
        }
    }
    Err(anyhow!("could not find forward_td_mlp_case_0.json"))
}

fn write_provenance(
    out_dir: &Path,
    input: &TdMvpInput,
    expected: &ForwardTdMlpOutput,
    proving_time_sec: f64,
    verification_time_sec: f64,
    proof_size_bytes: u64,
    cycle_count: Option<u64>,
    case_path: &Path,
    guest_elf_sha256: &str,
    prover_label: &str,
) -> Result<()> {
    write_json(out_dir.join("public_inputs.json"), &input.public)?;
    write_json(out_dir.join("witness_schema.json"), &witness_schema())?;
    write_json(
        out_dir.join("metrics.json"),
        &json!({
            "relation": "forward_td_mlp",
            // Which prover produced this row. Without it a table mixes CPU
            // and GPU numbers with nothing on the row saying which is which.
            "prover": prover_label,
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
            "guest_elf_sha256": guest_elf_sha256,
            "public_inputs_sha256": sha256_json(&input.public)?,
            "notes": ["SP1 proof-backed fixed-point Forward-TD MLP for canonical tiny vector."]
        }),
    )?;
    write_json(
        out_dir.join("verify_report.json"),
        &json!({
            "relation": "forward_td_mlp",
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
            "expected_runtime_location": "artifacts/kaggle_phase4_complete_outputs/extracted/phase4_complete_outputs/sp1/forward_td_mlp/proof.bin"
        }),
    )?;
    Ok(())
}

fn witness_schema() -> serde_json::Value {
    json!({
        "schema_version": "sp1_forward_td_mlp_witness_schema_v1",
        "relation": "forward_td_mlp",
        "private_witness": "forward_td_mlp_v1 private section: transition, Merkle path, online/target quantized MLPs, and forward witnesses",
        "public_inputs": "forward_td_mlp_v1 public section",
        "notes": ["Mirrors td_mvp_shared forward_td_mlp_v1 arithmetic and membership checks."]
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
    let output = Command::new("git").args(["rev-parse", "HEAD"]).output().ok()?;
    if !output.status.success() {
        return None;
    }
    Some(String::from_utf8_lossy(&output.stdout).trim().to_owned())
}

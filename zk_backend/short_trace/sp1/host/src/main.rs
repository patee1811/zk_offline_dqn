use std::fs;
use std::path::{Path, PathBuf};
use std::process::Command;
use std::time::Instant;

use anyhow::{anyhow, Context, Result};
use clap::Parser;
use serde_json::json;
use short_trace_shared::{verify_short_trace, ShortTraceInput, ShortTraceOutput};
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
    #[arg(long)]
    skip_host_precheck: bool,
}

#[tokio::main]
async fn main() -> Result<()> {
    let args = Args::parse();
    let case_path = resolve_case_path(args.case)?;
    let input = load_input(&case_path)?;

    println!("case_path = {}", case_path.display());
    let expected = verify_short_trace(&input);
    if !args.skip_host_precheck {
        println!("host_precheck = true");
        println!("start_checkpoint_hash = {}", expected.start_checkpoint_hash);
        println!("final_checkpoint_hash = {}", expected.final_checkpoint_hash);
    } else {
        println!("host_precheck = skipped");
    }

    let client = ProverClient::builder().cpu().build().await;
    let elf = include_elf!("short-trace-guest");
    let mut cycle_count: Option<u64> = None;

    if args.execute || args.prove || !args.prove {
        let stdin = build_stdin(&input);
        let start = Instant::now();
        let (mut public_values, report) = client
            .execute(elf.clone(), stdin)
            .await
            .context("SP1 execution failed")?;
        let output = public_values.read::<ShortTraceOutput>();
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
        let out_dir = args
            .out_dir
            .clone()
            .unwrap_or_else(|| PathBuf::from("artifacts/reports/provenance/sp1/short_trace"));
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
        proof.save(&proof_path)
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

fn build_stdin(input: &ShortTraceInput) -> SP1Stdin {
    let mut stdin = SP1Stdin::new();
    stdin.write(input);
    stdin
}

fn load_input(path: &Path) -> Result<ShortTraceInput> {
    let text =
        fs::read_to_string(path).with_context(|| format!("failed to read {}", path.display()))?;
    serde_json::from_str(&text).with_context(|| format!("failed to parse {}", path.display()))
}

fn resolve_case_path(case: Option<PathBuf>) -> Result<PathBuf> {
    if let Some(path) = case {
        return Ok(path);
    }
    let candidates = [
        PathBuf::from("../../test_vectors/short_trace_case_0.json"),
        PathBuf::from("zk_backend/test_vectors/short_trace_case_0.json"),
    ];
    for candidate in candidates {
        if candidate.exists() {
            return Ok(candidate);
        }
    }
    Err(anyhow!("could not find short_trace_case_0.json"))
}

fn write_provenance(
    out_dir: &Path,
    input: &ShortTraceInput,
    expected: &ShortTraceOutput,
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
            "relation": "short_trace",
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
            "notes": ["SP1 proof-backed tiny checkpoint-chain validation; not full DQN training."]
        }),
    )?;
    write_json(
        out_dir.join("verify_report.json"),
        &json!({
            "relation": "short_trace",
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
            "expected_runtime_location": "artifacts/kaggle_phase4_complete_outputs/extracted/phase4_complete_outputs/sp1/short_trace/proof.bin"
        }),
    )?;
    Ok(())
}

fn witness_schema() -> serde_json::Value {
    json!({
        "schema_version": "sp1_short_trace_witness_schema_v1",
        "relation": "short_trace",
        "private_witness": {"steps": [{"old_weights": "[i64]", "gradients": "[i64]", "new_weights": "[i64]", "old_checkpoint_hash": "sha256", "new_checkpoint_hash": "sha256"}]},
        "public_inputs": {"start_checkpoint_hash": "sha256", "final_checkpoint_hash": "sha256", "num_steps": "usize", "trace_hash": "sha256"},
        "notes": ["Verifies a tiny fixed-point SGD checkpoint chain, step order, and trace hash."]
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


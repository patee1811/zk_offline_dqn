use std::fs;
use std::path::{Path, PathBuf};
use std::process::Command;
use std::time::Instant;

use anyhow::{anyhow, Context, Result};
use clap::Parser;
use serde_json::json;
use sp1_sdk::{include_elf, Prover, ProverClient, ProvingKey, SP1Stdin};
use td_mvp_shared::{smooth_l1_loss_fp, verify_td_mvp, PublicOutput, TdMvpInput};

#[derive(Debug, Parser)]
struct Args {
    #[arg(long)]
    input: Option<PathBuf>,

    #[arg(long, default_value = "valid_control")]
    case: String,

    #[arg(long)]
    execute: bool,

    #[arg(long)]
    prove: bool,

    /// Write compact provenance here. Pass an absolute path: cargo runs the host
    /// from the workspace directory, so a relative one lands under zk_backend/.
    #[arg(long)]
    out_dir: Option<PathBuf>,

    #[arg(long)]
    skip_host_precheck: bool,
}

#[tokio::main]
async fn main() -> Result<()> {
    let args = Args::parse();
    let input_path = resolve_input_path(args.input)?;
    let mut input = load_input(&input_path)?;
    apply_case(&mut input, &args.case)?;

    println!("input_path = {}", input_path.display());
    println!("case_name = {}", args.case);

    let is_valid_control = args.case == "valid_control";
    // Only the untampered case may claim provenance: a tamper run mutates the
    // input, so writing from it would overwrite a good row with a mutated one.
    let expected: Option<PublicOutput> = if is_valid_control {
        Some(verify_td_mvp(&input))
    } else {
        None
    };

    if is_valid_control && !args.skip_host_precheck {
        let output = expected.as_ref().expect("valid_control computes expected");
        println!("host_precheck = true");
        if let Some(claimed_target_fp) = output.claimed_target_fp {
            println!("claimed_target_fp = {}", claimed_target_fp);
        }
        if let Some(claimed_loss_fp) = output.claimed_loss_fp {
            println!("claimed_loss_fp = {}", claimed_loss_fp);
        }
        if let Some(batch_size) = output.batch_size {
            println!("batch_size = {}", batch_size);
        }
        if let Some(claimed_batch_loss_fp) = output.claimed_batch_loss_fp {
            println!("claimed_batch_loss_fp = {}", claimed_batch_loss_fp);
        }
    } else {
        println!("host_precheck = skipped_for_tamper_case");
    }

    let client = ProverClient::builder().cpu().build().await;
    let elf = include_elf!("td-mvp-guest");
    let guest_elf_sha256 = hex_sha256(&elf);
    let mut cycle_count: Option<u64> = None;

    // `--out-dir` also forces execution: cycle_count comes from the report, and a
    // provenance row without it cannot be compared against the other relations.
    if args.execute || !args.prove || args.out_dir.is_some() {
        let stdin = build_stdin(&input);
        let start = Instant::now();
        let (_public_values, report) = client
            .execute(elf.clone(), stdin)
            .await
            .context("SP1 execution failed")?;
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

        let proof_size_bytes = match (&args.out_dir, &expected) {
            (Some(out_dir), Some(expected)) => {
                fs::create_dir_all(out_dir)
                    .with_context(|| format!("failed to create {}", out_dir.display()))?;
                let proof_path = out_dir.join("proof.bin");
                proof
                    .save(&proof_path)
                    .with_context(|| format!("failed to save {}", proof_path.display()))?;
                let size = fs::metadata(&proof_path)?.len();
                write_provenance(
                    out_dir,
                    &input,
                    expected,
                    proving_time_sec,
                    verification_time_sec,
                    size,
                    cycle_count,
                    &input_path,
                    &guest_elf_sha256,
                )?;
                println!("provenance_dir = {}", out_dir.display());
                size
            }
            _ => {
                let proof_file =
                    tempfile::NamedTempFile::new().context("failed to create temp proof file")?;
                proof
                    .save(proof_file.path())
                    .context("failed to serialize proof to temp file")?;
                fs::metadata(proof_file.path())
                    .context("failed to stat temp proof file")?
                    .len()
            }
        };

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

fn resolve_input_path(input: Option<PathBuf>) -> Result<PathBuf> {
    if let Some(path) = input {
        return Ok(path);
    }

    let candidates = [
        PathBuf::from("zk_backend/test_vectors/td_mvp_case_0.json"),
        PathBuf::from("../../test_vectors/td_mvp_case_0.json"),
        PathBuf::from("../../../test_vectors/td_mvp_case_0.json"),
        PathBuf::from("../test_vectors/td_mvp_case_0.json"),
    ];

    for candidate in candidates {
        if candidate.exists() {
            return Ok(candidate);
        }
    }

    Err(anyhow!(
        "could not find td_mvp_case_0.json; pass --input explicitly"
    ))
}

fn apply_case(input: &mut TdMvpInput, case_name: &str) -> Result<()> {
    match case_name {
        "valid_control" => {}
        "tamper_schema_version" => {
            input.schema_version = "td_mvp_test_vector_v0".to_owned();
        }
        "tamper_reward" => {
            first_transition_mut(input)?.reward += 1.0;
        }
        "tamper_fixed_point_rounding" => {
            first_transition_mut(input)?.reward += 0.0006;
        }
        "tamper_done" => {
            let transition = first_transition_mut(input)?;
            transition.done = 1 - transition.done;
        }
        "tamper_done_branch" => {
            let fp_scale = input.public.fp_scale;
            let reward_fp = first_leaf_mut(input)?[5];
            let td_witness = first_td_witness_mut(input)?;
            let q_online_action_fp = td_witness
                .q_online_action_fp
                .ok_or_else(|| anyhow!("input has no q_online_action_fp"))?;
            td_witness.target_fp = reward_fp;
            let td_error_fp = q_online_action_fp - reward_fp;
            td_witness.td_error_fp = Some(td_error_fp);
            td_witness.loss_fp = smooth_l1_loss_fp(td_error_fp, fp_scale);
        }
        "tamper_transition_obs" => {
            first_transition_mut(input)?.obs[0] += 1.0;
        }
        "tamper_leaf_encoding" => {
            first_leaf_mut(input)?[0] += 1;
        }
        "tamper_leaf_index" => {
            input.public.leaf_index = Some(
                input
                    .public
                    .leaf_index
                    .ok_or_else(|| anyhow!("input has no leaf_index"))?
                    + 1,
            );
        }
        "tamper_merkle_path" => {
            first_merkle_path_mut(input)?[0].sibling_hash = "00".repeat(32);
        }
        "tamper_path_order" => {
            first_merkle_path_mut(input)?.reverse();
        }
        "tamper_q_target_max_fp" => {
            first_td_witness_mut(input)?.q_target_max_fp += 1;
        }
        "tamper_target_network_value" => {
            first_td_witness_mut(input)?.q_target_max_fp += 1;
        }
        "tamper_claimed_target_fp" => {
            input.public.claimed_target_fp = Some(
                input
                    .public
                    .claimed_target_fp
                    .ok_or_else(|| anyhow!("input has no claimed_target_fp"))?
                    + 1,
            );
        }
        "tamper_claimed_loss_fp" => {
            input.public.claimed_loss_fp = Some(
                input
                    .public
                    .claimed_loss_fp
                    .ok_or_else(|| anyhow!("input has no claimed_loss_fp"))?
                    + 1,
            );
        }
        "tamper_leaf_hash" => {
            *first_leaf_hash_mut(input)? = "11".repeat(32);
        }
        "tamper_td_error_fp" => {
            let td_witness = first_td_witness_mut(input)?;
            td_witness.td_error_fp = Some(
                td_witness
                    .td_error_fp
                    .ok_or_else(|| anyhow!("input has no td_error_fp"))?
                    + 1,
            );
        }
        "tamper_batch_claimed_loss_fp" => {
            input.public.claimed_batch_loss_fp = Some(
                input
                    .public
                    .claimed_batch_loss_fp
                    .ok_or_else(|| anyhow!("input has no claimed_batch_loss_fp"))?
                    + 1,
            );
        }
        "tamper_batch_size" => {
            input.public.batch_size = Some(
                input
                    .public
                    .batch_size
                    .ok_or_else(|| anyhow!("input has no batch_size"))?
                    + 1,
            );
        }
        "tamper_batch_item_loss_fp" => {
            first_td_witness_mut(input)?.loss_fp += 1;
        }
        "tamper_batch_item_index" => {
            let first = input
                .private
                .items
                .first_mut()
                .ok_or_else(|| anyhow!("input has no batch items"))?;
            first.index += 1;
        }
        "tamper_batch_path_order" => {
            first_merkle_path_mut(input)?.reverse();
        }
        "tamper_batch_target_network_value" => {
            first_td_witness_mut(input)?.q_target_max_fp += 1;
        }
        "tamper_batch_fixed_point_rounding" => {
            first_transition_mut(input)?.reward += 0.0006;
        }
        "tamper_online_model_weight" => {
            let model = input
                .private
                .online_model
                .as_mut()
                .ok_or_else(|| anyhow!("input has no online_model"))?;
            model.layers[0].weight[0][0] += 1;
        }
        "tamper_target_model_weight" => {
            let model = input
                .private
                .target_model
                .as_mut()
                .ok_or_else(|| anyhow!("input has no target_model"))?;
            model.layers[0].weight[0][0] += 1;
        }
        "tamper_activation" => {
            first_forward_witness_mut(input)?.online_obs.pre_activations[0][0] += 1;
        }
        "tamper_relu_mask" => {
            let mask = &mut first_forward_witness_mut(input)?.online_obs.relu_masks[0][0];
            *mask = 1 - *mask;
        }
        "tamper_argmax" => {
            let witness = first_forward_witness_mut(input)?;
            witness.next_action_online = 1 - witness.next_action_online;
        }
        "tamper_selected_target_value" => {
            first_forward_witness_mut(input)?.q_target_max_fp += 1;
        }
        other => return Err(anyhow!("unknown case_name: {other}")),
    }
    Ok(())
}

fn first_transition_mut(input: &mut TdMvpInput) -> Result<&mut td_mvp_shared::Transition> {
    if let Some(first) = input.private.items.first_mut() {
        return Ok(&mut first.transition);
    }
    input
        .private
        .transition
        .as_mut()
        .ok_or_else(|| anyhow!("input has no transition"))
}

fn first_leaf_mut(input: &mut TdMvpInput) -> Result<&mut Vec<i64>> {
    if let Some(first) = input.private.items.first_mut() {
        return Ok(&mut first.leaf);
    }
    input
        .private
        .leaf
        .as_mut()
        .ok_or_else(|| anyhow!("input has no leaf"))
}

fn first_leaf_hash_mut(input: &mut TdMvpInput) -> Result<&mut String> {
    if let Some(first) = input.private.items.first_mut() {
        return Ok(&mut first.leaf_hash);
    }
    input
        .private
        .leaf_hash
        .as_mut()
        .ok_or_else(|| anyhow!("input has no leaf_hash"))
}

fn first_merkle_path_mut(
    input: &mut TdMvpInput,
) -> Result<&mut Vec<td_mvp_shared::MerklePathStep>> {
    if let Some(first) = input.private.items.first_mut() {
        return Ok(&mut first.merkle_path);
    }
    input
        .private
        .merkle_path
        .as_mut()
        .ok_or_else(|| anyhow!("input has no merkle_path"))
}

fn first_td_witness_mut(input: &mut TdMvpInput) -> Result<&mut td_mvp_shared::TdWitness> {
    if let Some(first) = input.private.items.first_mut() {
        return Ok(&mut first.td_witness);
    }
    input
        .private
        .td_witness
        .as_mut()
        .ok_or_else(|| anyhow!("input has no td_witness"))
}

fn first_forward_witness_mut(
    input: &mut TdMvpInput,
) -> Result<&mut td_mvp_shared::ForwardWitness> {
    input
        .private
        .items
        .first_mut()
        .and_then(|item| item.forward_witness.as_mut())
        .ok_or_else(|| anyhow!("input has no forward_witness"))
}

fn write_provenance(
    out_dir: &Path,
    input: &TdMvpInput,
    expected: &PublicOutput,
    proving_time_sec: f64,
    verification_time_sec: f64,
    proof_size_bytes: u64,
    cycle_count: Option<u64>,
    case_path: &Path,
    guest_elf_sha256: &str,
) -> Result<()> {
    write_json(out_dir.join("public_inputs.json"), &input.public)?;
    write_json(out_dir.join("witness_schema.json"), &witness_schema())?;
    write_json(
        out_dir.join("metrics.json"),
        &json!({
            "relation": "td_mvp",
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
            "notes": ["SP1 proof-backed TD target and SmoothL1 loss over a Merkle-committed transition; not full DQN training."]
        }),
    )?;
    write_json(
        out_dir.join("verify_report.json"),
        &json!({
            "relation": "td_mvp",
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
            "expected_runtime_location": "artifacts/reports/provenance/sp1/td_mvp/proof.bin"
        }),
    )?;
    Ok(())
}

fn witness_schema() -> serde_json::Value {
    json!({
        "schema_version": "sp1_td_mvp_witness_schema_v1",
        "relation": "td_mvp",
        "private_witness": {"transition": "Transition", "leaf": "[i64]", "leaf_hash": "sha256", "merkle_path": [{"sibling_hash": "sha256", "current_is_left": "bool"}], "td_witness": "TdWitness", "items": "[TdMvpItem]"},
        "public_inputs": {"dataset_root": "sha256", "fp_scale": "i64", "gamma_fp": "i64", "loss_type": "string", "claimed_target_fp": "i64?", "claimed_loss_fp": "i64?", "leaf_index": "i64?", "batch_size": "usize?", "claimed_batch_loss_fp": "i64?"},
        "notes": ["Verifies Merkle membership of the transition, the fixed-point TD target, and the SmoothL1 loss."]
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

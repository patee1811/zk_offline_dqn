use std::fs;
use std::path::{Path, PathBuf};
use std::time::Instant;

use anyhow::{anyhow, Context, Result};
use clap::Parser;
use sp1_sdk::{include_elf, Prover, ProverClient, ProvingKey, SP1Stdin};
use td_mvp_shared::{verify_td_mvp, TdMvpInput};

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

    if args.case == "valid_control" && !args.skip_host_precheck {
        let output = verify_td_mvp(&input);
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

    if args.execute || !args.prove {
        let stdin = build_stdin(&input);
        let start = Instant::now();
        let (_public_values, report) = client
            .execute(elf.clone(), stdin)
            .await
            .context("SP1 execution failed")?;
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

        let proof_file =
            tempfile::NamedTempFile::new().context("failed to create temp proof file")?;
        proof
            .save(proof_file.path())
            .context("failed to serialize proof to temp file")?;
        let proof_size_bytes = fs::metadata(proof_file.path())
            .context("failed to stat temp proof file")?
            .len();

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
        "tamper_reward" => {
            first_transition_mut(input)?.reward += 1.0;
        }
        "tamper_done" => {
            let transition = first_transition_mut(input)?;
            transition.done = 1 - transition.done;
        }
        "tamper_transition_obs" => {
            first_transition_mut(input)?.obs[0] += 1.0;
        }
        "tamper_leaf_encoding" => {
            first_leaf_mut(input)?[0] += 1;
        }
        "tamper_merkle_path" => {
            first_merkle_path_mut(input)?[0].sibling_hash = "00".repeat(32);
        }
        "tamper_q_target_max_fp" => {
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

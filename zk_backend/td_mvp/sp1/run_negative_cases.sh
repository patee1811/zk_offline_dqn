#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

INPUT="../../test_vectors/td_mvp_case_0.json"

echo "valid_control"
cargo run --release -p td-mvp-host -- --input "$INPUT" --case valid_control --execute

cases=(
  tamper_reward
  tamper_done
  tamper_merkle_path
  tamper_claimed_target_fp
  tamper_claimed_loss_fp
)

for case_name in "${cases[@]}"; do
  echo "$case_name"
  if cargo run --release -p td-mvp-host -- --input "$INPUT" --case "$case_name" --execute; then
    echo "case unexpectedly accepted: $case_name" >&2
    exit 1
  fi
  echo "case rejected as expected: $case_name"
done

echo "all_sp1_negative_cases_passed = true"

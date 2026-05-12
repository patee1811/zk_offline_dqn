#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

INPUT="../../test_vectors/td_mvp_case_0.json"
BATCH_INPUT="/tmp/td_mvp_batch_size_2.json"

echo "valid_control"
cargo run --release -p td-mvp-host -- --input "$INPUT" --case valid_control --execute

cases=(
  tamper_schema_version
  tamper_reward
  tamper_fixed_point_rounding
  tamper_done
  tamper_done_branch
  tamper_transition_obs
  tamper_leaf_encoding
  tamper_merkle_path
  tamper_leaf_index
  tamper_path_order
  tamper_q_target_max_fp
  tamper_target_network_value
  tamper_claimed_target_fp
  tamper_claimed_loss_fp
  tamper_leaf_hash
  tamper_td_error_fp
)

for case_name in "${cases[@]}"; do
  echo "$case_name"
  if cargo run --release -p td-mvp-host -- --input "$INPUT" --case "$case_name" --execute; then
    echo "case unexpectedly accepted: $case_name" >&2
    exit 1
  fi
  echo "case rejected as expected: $case_name"
done

python3 ../../../scripts/artifacts_export/export_td_mvp_batch_test_vector.py \
  --input "$INPUT" \
  --out "$BATCH_INPUT" \
  --batch-size 2

echo "valid_batch_size_2"
cargo run --release -p td-mvp-host -- --input "$BATCH_INPUT" --case valid_control --execute

batch_cases=(
  tamper_batch_claimed_loss_fp
  tamper_batch_size
  tamper_batch_item_loss_fp
  tamper_batch_item_index
  tamper_batch_path_order
  tamper_batch_target_network_value
  tamper_batch_fixed_point_rounding
)

for case_name in "${batch_cases[@]}"; do
  echo "$case_name"
  if cargo run --release -p td-mvp-host -- --input "$BATCH_INPUT" --case "$case_name" --execute --skip-host-precheck; then
    echo "case unexpectedly accepted: $case_name" >&2
    exit 1
  fi
  echo "case rejected as expected: $case_name"
done

echo "all_sp1_negative_cases_passed = true"

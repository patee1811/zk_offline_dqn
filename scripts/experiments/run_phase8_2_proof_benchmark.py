"""Run Phase 8.2 ZK proof-cost benchmarks and export paper Table 2."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from zk_offline_dqn.proof_benchmarks.runner import run_benchmark


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--paper", action="store_true")
    mode.add_argument("--smoke", action="store_true")
    parser.add_argument("--run-sp1-execute", action="store_true")
    parser.add_argument("--run-sp1-prove", action="store_true")
    parser.add_argument("--reuse-existing-provenance", action="store_true")
    parser.add_argument("--refresh-proof-metrics", action="store_true")
    parser.add_argument("--include-execute-only", action="store_true")
    parser.add_argument("--include-known-failures", action="store_true")
    parser.add_argument("--merkle-depth-proof-scaling", action="store_true")
    parser.add_argument("--merkle-dataset-sizes", nargs="+", type=int)
    parser.add_argument("--merkle-source-dataset", default="D4RL/pointmaze/umaze-v2")
    parser.add_argument("--reuse-phase2-datasets", action="store_true")
    parser.add_argument("--regenerate-missing-merkle-datasets", action="store_true")
    parser.add_argument("--dataset-sizes", nargs="+", type=int)
    parser.add_argument("--trace-lengths", nargs="+", type=int)
    parser.add_argument("--batch-sizes", nargs="+", type=int)
    parser.add_argument("--networks", nargs="+")
    parser.add_argument("--aggregation-targets", nargs="+", type=int)
    parser.add_argument("--out-dir", default="artifacts/reports/final_ndss")
    parser.add_argument("--work-dir", default="artifacts/reports/phase8_2_proof_benchmark/work")
    parser.add_argument("--timeout-seconds", type=int, default=7200)
    parser.add_argument("--device", default="cpu")
    return parser


def _defaults(args: argparse.Namespace) -> None:
    if args.dataset_sizes is None:
        args.dataset_sizes = [1000, 10000, 100000] if args.paper else [1000]
    if args.trace_lengths is None:
        args.trace_lengths = [1, 4, 8, 16, 32, 128] if args.paper else [1]
    if args.batch_sizes is None:
        args.batch_sizes = [1, 4, 8, 16] if args.paper else [1]
    if args.networks is None:
        args.networks = ["tiny", "small"] if args.paper else ["tiny"]
    if args.aggregation_targets is None:
        args.aggregation_targets = [32, 64, 128] if args.paper else [32]
    if args.merkle_dataset_sizes is None:
        args.merkle_dataset_sizes = [1000, 10000, 100000] if args.paper else [1000]
    if args.paper:
        args.run_sp1_execute = True if not args.run_sp1_execute else args.run_sp1_execute
        args.run_sp1_prove = True if not args.run_sp1_prove else args.run_sp1_prove
        args.reuse_existing_provenance = True
        args.refresh_proof_metrics = True
        args.include_execute_only = True
        args.include_known_failures = True
        args.merkle_depth_proof_scaling = True
        args.reuse_phase2_datasets = True
    if args.smoke:
        args.reuse_existing_provenance = True
        args.include_execute_only = True


def main() -> int:
    args = build_parser().parse_args()
    _defaults(args)
    status = run_benchmark(args)
    print("phase8_2_proof_benchmark = completed")
    print(json.dumps(status, indent=2, sort_keys=True))
    return 0 if status["proof_verified_rows"] > 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

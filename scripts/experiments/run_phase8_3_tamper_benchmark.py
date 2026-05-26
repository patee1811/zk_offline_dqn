from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from zk_offline_dqn.tamper_benchmarks.runner import run_benchmark


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Phase 8.3 tamper rejection benchmark for Table 3.")
    parser.add_argument("--paper", action="store_true")
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--include-dataset-tamper", action="store_true")
    parser.add_argument("--include-merkle-tamper", action="store_true")
    parser.add_argument("--include-forward-td-tamper", action="store_true")
    parser.add_argument("--include-sgd-tamper", action="store_true")
    parser.add_argument("--include-training-update-tamper", action="store_true")
    parser.add_argument("--include-training-fragment-tamper", action="store_true")
    parser.add_argument("--include-aggregation-tamper", action="store_true")
    parser.add_argument("--include-proof-public-input-tamper", action="store_true")
    parser.add_argument("--run-python-reference", action="store_true")
    parser.add_argument("--run-rust-execute", action="store_true")
    parser.add_argument("--run-sp1-prove-for-originals", action="store_true")
    parser.add_argument("--run-sp1-verify-tampered", action="store_true")
    parser.add_argument("--reuse-existing-provenance", action="store_true")
    parser.add_argument("--timeout-seconds", type=int, default=7200)
    parser.add_argument("--out-dir", default="artifacts/reports/final_ndss")
    parser.add_argument("--work-dir", default="artifacts/reports/phase8_3_tamper_benchmark/work")
    return parser


def _includes(args: argparse.Namespace) -> dict[str, bool]:
    includes = {
        "dataset": args.include_dataset_tamper,
        "merkle": args.include_merkle_tamper,
        "forward_td": args.include_forward_td_tamper,
        "sgd": args.include_sgd_tamper,
        "training_update": args.include_training_update_tamper,
        "training_fragment": args.include_training_fragment_tamper,
        "aggregation": args.include_aggregation_tamper,
        "proof_public_input": args.include_proof_public_input_tamper,
    }
    if args.paper:
        return {key: True for key in includes}
    if not any(includes.values()):
        includes["dataset"] = True
        includes["merkle"] = True
        includes["proof_public_input"] = True
    return includes


def main() -> int:
    args = build_parser().parse_args()
    out_dir = Path(args.out_dir)
    if not out_dir.is_absolute():
        out_dir = ROOT / out_dir
    work_dir = Path(args.work_dir)
    if not work_dir.is_absolute():
        work_dir = ROOT / work_dir
    try:
        result = run_benchmark(
            paper=args.paper,
            smoke=args.smoke,
            includes=_includes(args),
            run_python_reference=args.run_python_reference or args.paper or args.smoke,
            run_rust_execute=args.run_rust_execute,
            run_sp1_prove_for_originals=args.run_sp1_prove_for_originals,
            run_sp1_verify_tampered=args.run_sp1_verify_tampered,
            reuse_existing_provenance=args.reuse_existing_provenance or args.paper or args.smoke,
            timeout_seconds=args.timeout_seconds,
            out_dir=out_dir,
            work_dir=work_dir,
        )
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print("phase8_3_tamper_benchmark = " + result["status"]["status"])
    print(json.dumps(result["status"], indent=2, sort_keys=True))
    return 0 if result["status"]["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())

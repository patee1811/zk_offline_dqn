"""Profile SP1 host memory across relations, on Kaggle or any GPU box.

Table 2 has an empty Peak RSS column and three rows that failed with
failed_oom or failed_environment. Neither can be acted on without knowing
which proving stage held the memory. This driver runs profile_sp1_memory.py
over a set of relations and writes one summary, so a single Kaggle session
produces the whole column.

Case order matters. Cases run cheapest-first so a session that is killed by
its time limit still leaves the small results behind, and the recursion cases
that are expected to OOM run last.

Nothing runs by default. Set RUN_SP1_PROVE=1 to prove, or pass --execute-only
to measure execute-mode memory without proving.

Example, inside a Kaggle notebook after setup_sp1_on_kaggle.sh:

    RUN_SP1_PROVE=1 python scripts/experiments/run_memory_profile_campaign.py \\
        --out-dir artifacts/reports/memory_profile
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parents[2]
PROFILER = ROOT / "scripts/experiments/profile_sp1_memory.py"
DEFAULT_OUT_DIR = Path("artifacts/reports/memory_profile")


@dataclass(frozen=True)
class ProfileCase:
    """One host invocation to profile."""

    label: str
    relation: str
    host_package: str
    proof_mode: str = "core"
    extra_args: List[str] = field(default_factory=list)
    expect: str = "proof_verified"
    notes: str = ""
    # A Python driver, relative to the repo root, that orchestrates the host
    # instead of the profiler calling cargo directly. Recursion needs one
    # because the case JSON has to be generated before the host will accept it.
    driver: List[str] = field(default_factory=list)

    @property
    def workspace(self) -> Path:
        # Driver cases run from the repo root so their relative paths resolve.
        if self.driver:
            return ROOT
        return ROOT / "zk_backend" / self.relation / "sp1"


# Ordered cheapest-first by the prove times already in Table 2. The recursion
# cases go last: they are the ones expected to exhaust memory, and a session
# that dies there has already banked everything above.
CASES: tuple[ProfileCase, ...] = (
    ProfileCase("short_trace", "short_trace", "short-trace-host",
                notes="82.3s in Table 2, the cheapest proof-backed row"),
    ProfileCase("training_update_batch1", "training_update", "training-update-host",
                notes="104.8s"),
    ProfileCase("merkle_membership", "merkle_membership", "merkle-membership-host",
                notes="121.7s"),
    ProfileCase("one_step_sgd_tiny", "one_step_sgd_tiny", "one-step-sgd-tiny-host",
                notes="122.7s"),
    ProfileCase("forward_td_mlp", "forward_td_mlp", "forward-td-mlp-host",
                notes="142.7s"),
    ProfileCase("td_mvp", "td_mvp", "td-mvp-host",
                notes="167.7s"),
    # --case is required on these two. Their hosts default to k4 and t32
    # respectively, so run 2 profiled the wrong vectors under the right labels.
    ProfileCase("training_fragment_k8", "training_fragment", "training-fragment-host",
                extra_args=["--case", "../../test_vectors/training_fragment_k8_case_0.json",
                            "--max-steps", "8"],
                notes="440.6s, the most expensive proof-backed row at 4.8M cycles"),
    ProfileCase("training_aggregation_t128", "training_aggregation", "training-aggregation-host",
                extra_args=["--case", "../../test_vectors/training_aggregation_t128_case_0.json"],
                notes="253.2s, proof-manifest chain mode"),
    # The rows Table 2 records as failures. Profiling these is the point of the
    # campaign: a peak with a stage name turns failed_oom into a fixable number.
    #
    # The aggregation host takes --mode, not --proof-mode, and it refuses a
    # mode the case JSON does not declare. All three committed vectors say
    # proof_manifest_chain, so a recursive_sp1 case has to be generated first
    # by run_phase7_sp1_training_aggregation_validation.py --aggregation-mode
    # recursive_sp1. These two cases run that generator under the profiler.
    # T=32 aggregates four k=8 children; T=16 aggregates two. The aggregate
    # step holds every child proof at once for the in-circuit verification,
    # so halving the children is the one lever that shrinks the peak without
    # touching chunk_size, FP_SCALE, or the network — all of which anchor
    # committed vectors. T=16 is still real recursion, and it is the row
    # Table 2 already names (binary_tree_native_t16).
    ProfileCase("recursive_native_t16", "training_aggregation", "training-aggregation-host",
                driver=[
                    "scripts/experiments/run_phase7_sp1_training_aggregation_validation.py",
                    "--targets", "16",
                    "--aggregation-mode", "recursive_sp1",
                    "--child-proof-mode", "native_sp1",
                    "--run-child-proves", "--run-prove", "--continue-on-failure",
                ],
                expect="unknown",
                notes="two k=8 children instead of four; half the aggregate load of t32"),
    ProfileCase("recursive_native_t8", "training_aggregation", "training-aggregation-host",
                driver=[
                    "scripts/experiments/run_phase7_sp1_training_aggregation_validation.py",
                    "--targets", "8",
                    "--aggregation-mode", "recursive_sp1",
                    "--child-proof-mode", "native_sp1",
                    "--run-child-proves", "--run-prove", "--continue-on-failure",
                ],
                expect="unknown",
                notes="one child; degenerate aggregation, but proves the circuit runs"),
    ProfileCase("recursive_native_t32", "training_aggregation", "training-aggregation-host",
                driver=[
                    "scripts/experiments/run_phase7_sp1_training_aggregation_validation.py",
                    "--targets", "32",
                    "--aggregation-mode", "recursive_sp1",
                    "--child-proof-mode", "native_sp1",
                    "--run-child-proves", "--run-prove", "--continue-on-failure",
                ],
                expect="failed_oom",
                notes="Table 2 native_flat_recursive_t32 failed_oom; measured 29255 MB"),
    ProfileCase("recursive_binary_tree_t32", "training_aggregation", "training-aggregation-host",
                driver=[
                    "scripts/experiments/run_phase7_sp1_training_aggregation_validation.py",
                    "--targets", "32",
                    "--aggregation-mode", "recursive_sp1",
                    "--aggregation-topology", "binary_tree",
                    "--child-proof-mode", "native_sp1",
                    "--run-child-proves", "--run-prove", "--continue-on-failure",
                ],
                expect="failed_oom",
                notes="Table 2 binary_tree_native_t16 failed_oom; arity 2 is the "
                      "configuration SUMMER's arity-10 choice argues against"),
)


def relative_to_root(path: Path) -> str:
    """Report paths inside the repo as relative; anything else stays absolute."""
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def build_command(case: ProfileCase, *, execute_only: bool) -> List[str]:
    if case.driver:
        driver = list(case.driver)
        if execute_only:
            driver = [arg for arg in driver if arg != "--run-prove"]
            if "--run-execute" not in driver:
                driver.append("--run-execute")
        return [sys.executable, *driver]

    mode = "--execute" if execute_only else "--prove"
    command = ["cargo", "run", "--release", "-p", case.host_package, "--", mode]
    if not execute_only and case.proof_mode != "core":
        command += ["--proof-mode", case.proof_mode]
    return command + case.extra_args


def profile_one(
    case: ProfileCase,
    out_dir: Path,
    *,
    execute_only: bool,
    interval: float,
    timeout: Optional[int],
) -> Dict[str, Any]:
    profile_path = out_dir / f"{case.label}.json"
    command = build_command(case, execute_only=execute_only)
    argv = [
        sys.executable,
        str(PROFILER),
        "--label",
        case.label,
        "--interval",
        str(interval),
        "--out",
        str(profile_path),
        "--cwd",
        str(case.workspace),
        "--",
        *command,
    ]

    print(f"\n=== {case.label} ({case.relation}, {case.proof_mode}) ===")
    print("command =", " ".join(command))
    print("cwd =", case.workspace.as_posix())

    if not case.workspace.is_dir():
        return {
            "label": case.label,
            "status": "skipped",
            "reason": f"workspace missing: {case.workspace.as_posix()}",
        }

    started = time.perf_counter()
    try:
        result = subprocess.run(argv, text=True, timeout=timeout)
        returncode = result.returncode
        status = "completed" if returncode == 0 else "failed"
    except subprocess.TimeoutExpired:
        returncode = None
        status = "timeout"

    record: Dict[str, Any] = {
        "label": case.label,
        "relation": case.relation,
        "host_package": case.host_package,
        "proof_mode": case.proof_mode,
        "mode": "execute" if execute_only else "prove",
        "expected": case.expect,
        "notes": case.notes,
        "returncode": returncode,
        "status": status,
        "wall_seconds": round(time.perf_counter() - started, 3),
        "profile_path": relative_to_root(profile_path),
    }

    # A failed run still carries the number we came for.
    if profile_path.is_file():
        profile = json.loads(profile_path.read_text(encoding="utf-8"))
        memory = profile.get("memory")
        if memory:
            record["peak_rss_mb"] = memory.get("peak_rss_mb")
            record["peak_stage"] = memory.get("peak_stage")
            record["stages"] = memory.get("stages")
        if profile.get("sampler_error"):
            record["sampler_error"] = profile["sampler_error"]
        record["stage_boundaries_seconds"] = profile.get("stage_boundaries_seconds")

    print(f"status = {status}")
    if "peak_rss_mb" in record:
        print(f"peak_rss_mb = {record['peak_rss_mb']}")
        print(f"peak_stage = {record['peak_stage']}")
    return record


def select_cases(only: Optional[str]) -> List[ProfileCase]:
    if not only:
        return list(CASES)
    wanted = {name.strip() for name in only.split(",") if name.strip()}
    selected = [case for case in CASES if case.label in wanted]
    unknown = wanted - {case.label for case in selected}
    if unknown:
        raise SystemExit(f"unknown case labels: {sorted(unknown)}")
    return selected


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    parser.add_argument(
        "--only",
        help="Comma-separated case labels. Defaults to every case.",
    )
    parser.add_argument(
        "--execute-only",
        action="store_true",
        help="Measure execute-mode memory and never prove.",
    )
    parser.add_argument("--interval", type=float, default=0.5)
    parser.add_argument(
        "--timeout",
        type=int,
        default=3600,
        help="Per-case timeout in seconds (default 3600).",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="Print the cases in run order and exit.",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    cases = select_cases(args.only)

    if args.list:
        for case in cases:
            print(f"{case.label:32s} {case.relation:24s} {case.proof_mode:16s} {case.notes}")
        return 0

    if not args.execute_only and os.environ.get("RUN_SP1_PROVE") != "1":
        print("RUN_SP1_PROVE is not 1; nothing was proved.")
        print("Set RUN_SP1_PROVE=1 to prove, or pass --execute-only to profile execute mode.")
        return 0

    out_dir = Path(args.out_dir)
    if not out_dir.is_absolute():
        out_dir = ROOT / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    records = []
    for case in cases:
        records.append(
            profile_one(
                case,
                out_dir,
                execute_only=args.execute_only,
                interval=args.interval,
                timeout=args.timeout,
            )
        )
        # Write after every case: a session killed by its time limit keeps
        # whatever finished.
        summary = {
            "mode": "execute" if args.execute_only else "prove",
            "sample_interval_seconds": args.interval,
            "cases": records,
        }
        (out_dir / "summary.json").write_text(
            json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )

    print("\n=== SUMMARY ===")
    for record in records:
        peak = record.get("peak_rss_mb")
        stage = record.get("peak_stage") or "-"
        peak_text = f"{peak:>10.1f} MB" if isinstance(peak, (int, float)) else f"{'n/a':>13s}"
        print(f"{record['label']:32s} {record['status']:10s} {peak_text}  peak_stage={stage}")
    print(f"\nsummary = {(out_dir / 'summary.json').as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

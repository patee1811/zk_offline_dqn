import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


OUT_DIR = Path("artifacts/full_regression")
SUMMARY_JSON = Path("artifacts/regression_summary.json")
SUMMARY_MD = Path("artifacts/regression_summary.md")


def ensure_out_dir() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    SUMMARY_JSON.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_MD.parent.mkdir(parents=True, exist_ok=True)


def run_command(
    name: str,
    command: List[str],
    env_updates: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    env = os.environ.copy()
    env["PYTHONPATH"] = "."
    env["MPLBACKEND"] = "Agg"
    env["OMP_NUM_THREADS"] = "1"

    if env_updates:
        env.update(env_updates)

    started = time.perf_counter()

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        env=env,
    )

    elapsed_sec = time.perf_counter() - started

    stdout_path = OUT_DIR / f"{name}.stdout.txt"
    stderr_path = OUT_DIR / f"{name}.stderr.txt"

    stdout_path.write_text(result.stdout, encoding="utf-8")
    stderr_path.write_text(result.stderr, encoding="utf-8")

    accepted_markers = [
        "verification_passed = True",
        "all_forward_ok = True",
        "all_tests_passed = True",
        "all_passed = True",
    ]

    marker_ok = any(marker in result.stdout for marker in accepted_markers)

    # compileall does not print a custom success marker.
    if name == "compileall":
        marker_ok = result.returncode == 0

    passed = result.returncode == 0 and marker_ok

    return {
        "name": name,
        "command": " ".join(command),
        "returncode": result.returncode,
        "passed": passed,
        "elapsed_sec": round(elapsed_sec, 4),
        "stdout_path": stdout_path.as_posix(),
        "stderr_path": stderr_path.as_posix(),
        "stdout_tail": "\n".join(result.stdout.splitlines()[-20:]),
        "stderr_tail": "\n".join(result.stderr.splitlines()[-20:]),
    }


def write_json_summary(results: List[Dict[str, Any]]) -> None:
    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "num_checks": len(results),
        "num_passed": sum(1 for item in results if item["passed"]),
        "num_failed": sum(1 for item in results if not item["passed"]),
        "all_passed": all(item["passed"] for item in results),
        "results": results,
    }

    SUMMARY_JSON.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def write_markdown_summary(results: List[Dict[str, Any]]) -> None:
    all_passed = all(item["passed"] for item in results)
    num_passed = sum(1 for item in results if item["passed"])
    num_failed = sum(1 for item in results if not item["passed"])

    lines: List[str] = []
    lines.append("# Full Regression Summary")
    lines.append("")
    lines.append(f"Generated at UTC: `{datetime.now(timezone.utc).isoformat()}`")
    lines.append("")
    lines.append("## Overall Result")
    lines.append("")
    lines.append(f"- Total checks: `{len(results)}`")
    lines.append(f"- Passed: `{num_passed}`")
    lines.append(f"- Failed: `{num_failed}`")
    lines.append(f"- All passed: `{all_passed}`")
    lines.append("")
    lines.append("## Check Table")
    lines.append("")
    lines.append("| Check | Passed | Return code | Runtime seconds | Stdout | Stderr |")
    lines.append("|---|---:|---:|---:|---|---|")

    for item in results:
        lines.append(
            "| "
            f"`{item['name']}` | "
            f"`{item['passed']}` | "
            f"`{item['returncode']}` | "
            f"`{item['elapsed_sec']}` | "
            f"`{item['stdout_path']}` | "
            f"`{item['stderr_path']}` |"
        )

    lines.append("")
    lines.append("## Expected Success Markers")
    lines.append("")
    lines.append("Successful runs should include these markers across the logs:")
    lines.append("")
    lines.append("```text")
    lines.append("verification_passed = True")
    lines.append("all_forward_ok = True")
    lines.append("all_tests_passed = True")
    lines.append("```")
    lines.append("")

    SUMMARY_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    ensure_out_dir()

    py = sys.executable

    checks = [
        {
            "name": "compileall",
            "command": [py, "-m", "compileall", "zk_offline_dqn", "scripts"],
        },
        {
            "name": "verify_minibatch_td_artifact",
            "command": [py, "scripts/artifacts_export/verify_minibatch_td_artifact.py"],
        },
        {
            "name": "verify_forward_td_consistency",
            "command": [
                py,
                "scripts/artifacts_export/verify_forward_td_consistency.py",
                "--artifact",
                "artifacts/minibatch_td_from_dataset.json",
                "--checkpoint",
                "models/offline_dqn_with_target_seed42_best.pt",
            ],
        },
        {
            "name": "verify_one_step_update_artifact",
            "command": [py, "scripts/artifacts_export/verify_one_step_update_artifact.py"],
        },
        {
            "name": "verify_short_trace_contiguous",
            "command": [py, "scripts/artifacts_export/verify_short_trace_update_artifact.py"],
            "env": {
                "SHORT_TRACE_ARTIFACT_PATH": "artifacts/short_trace_update_artifact.json",
                "SHORT_TRACE_MERKLE_PATH": "artifacts/cartpole_dqn_eps010_merkle.json",
                "SHORT_TRACE_INITIAL_CHECKPOINT_PATH": "models/offline_dqn_with_target_seed42_best.pt",
                "SHORT_TRACE_FINAL_CHECKPOINT_PATH": "artifacts/short_trace_work/step_1_post_synced_4_5_6_7.pt",
                "SHORT_TRACE_WORK_DIR": "artifacts/short_trace_work",
            },
        },
        {
            "name": "verify_short_trace_seeded",
            "command": [py, "scripts/artifacts_export/verify_short_trace_update_artifact.py"],
            "env": {
                "SHORT_TRACE_ARTIFACT_PATH": "artifacts/short_trace_seeded_artifact.json",
                "SHORT_TRACE_MERKLE_PATH": "artifacts/cartpole_dqn_eps010_merkle.json",
                "SHORT_TRACE_INITIAL_CHECKPOINT_PATH": "models/offline_dqn_with_target_seed42_best.pt",
                "SHORT_TRACE_FINAL_CHECKPOINT_PATH": "artifacts/short_trace_seeded_work/step_1_post_synced_9_13_15_18.pt",
                "SHORT_TRACE_WORK_DIR": "artifacts/short_trace_seeded_work",
            },
        },
        {
            "name": "run_one_step_negative_tests",
            "command": [py, "scripts/experiments/run_one_step_negative_tests.py"],
        },
        {
            "name": "run_short_trace_negative_tests",
            "command": [py, "scripts/experiments/run_short_trace_negative_tests.py"],
        },
        {
            "name": "run_minibatch_td_negative_tests",
            "command": [py, "scripts/experiments/run_negative_verification_tests.py"],
        },
        {
            "name": "benchmark_distinct_td_sp1_python_only",
            "command": [
                py,
                "scripts/experiments/benchmark_distinct_td_sp1.py",
                "--skip-sp1",
            ],
        },
        {
            "name": "benchmark_forward_td_mlp_sp1_python_only",
            "command": [
                py,
                "scripts/experiments/benchmark_forward_td_mlp_sp1.py",
                "--skip-sp1",
            ],
        },
        {
            "name": "run_td_mvp_test_vector_negative_tests",
            "command": [py, "scripts/experiments/run_td_mvp_test_vector_negative_tests.py"],
        },
    ]

    results: List[Dict[str, Any]] = []

    print("=== FULL REGRESSION RUNNER ===")
    print(f"num_checks = {len(checks)}")
    print()

    for check in checks:
        name = check["name"]
        print(f"running = {name}")

        result = run_command(
            name=name,
            command=check["command"],
            env_updates=check.get("env"),
        )

        results.append(result)

        print(f"{name}_passed = {result['passed']}")
        print(f"{name}_returncode = {result['returncode']}")
        print(f"{name}_elapsed_sec = {result['elapsed_sec']}")
        print()

    write_json_summary(results)
    write_markdown_summary(results)

    all_passed = all(item["passed"] for item in results)

    print("summary_json_path =", SUMMARY_JSON.as_posix())
    print("summary_md_path =", SUMMARY_MD.as_posix())
    print("all_regression_passed =", all_passed)

    if not all_passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()  

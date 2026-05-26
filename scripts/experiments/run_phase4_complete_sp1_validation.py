from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List


ROOT = Path(__file__).resolve().parents[2]


RELATIONS = [
    ("forward_td_mlp", "scripts/experiments/run_phase4_sp1_forward_td_mlp_validation.py"),
    ("one_step_sgd_tiny", "scripts/experiments/run_phase4_sp1_one_step_sgd_validation.py"),
    ("short_trace", "scripts/experiments/run_phase4_sp1_short_trace_validation.py"),
]


def run_relation(relation: str, script: str, out_dir: Path, prove: bool) -> Dict[str, Any]:
    relation_dir = out_dir / "sp1" / relation
    command: List[str] = [sys.executable, script, "--out-dir", str(relation_dir)]
    if prove:
        command.append("--prove")
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    status_path = next(relation_dir.glob("phase4_*_status.json"), None) if relation_dir.exists() else None
    detail = None
    if status_path is not None:
        detail = json.loads(status_path.read_text(encoding="utf-8"))
    return {
        "relation": relation,
        "passed": result.returncode == 0,
        "return_code": result.returncode,
        "detail": detail,
        "stdout_tail": "\n".join(result.stdout.splitlines()[-80:]),
        "stderr_tail": "\n".join(result.stderr.splitlines()[-80:]),
    }


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--prove", action="store_true")
    args = parser.parse_args()
    out_dir = Path(args.out_dir)
    results = [run_relation(relation, script, out_dir, args.prove) for relation, script in RELATIONS]
    summary = {"relations": results, "all_passed": all(item["passed"] for item in results)}
    write_json(out_dir / "phase4_complete_sp1_status.json", summary)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["all_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())


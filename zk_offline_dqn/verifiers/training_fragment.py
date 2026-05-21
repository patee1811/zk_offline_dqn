"""Artifact-facing verifier for Phase 6 training-fragment fixtures."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from zk_offline_dqn.relations.training_fragment import verify_case


DEFAULT_FIXTURE_PATH = "zk_backend/test_vectors/training_fragment_k4_case_0.json"


def verify_file(path: str = DEFAULT_FIXTURE_PATH) -> Dict[str, Any]:
    fixture = json.loads(Path(path).read_text(encoding="utf-8"))
    result = verify_case(fixture)
    return {
        "accepted": result.accepted,
        "reason": result.reason,
        "public_output": result.public_output,
    }


def main() -> int:
    result = verify_file()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["accepted"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

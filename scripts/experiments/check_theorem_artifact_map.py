"""Validate Phase 9 theorem, threat-model, and artifact-map coverage."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List


ROOT = Path(__file__).resolve().parents[2]
THEOREM_MAP = ROOT / "docs/theorem_artifact_map.md"
THEOREMS_TEX = ROOT / "paper/sections/theorems.tex"
THREAT_MODEL_TEX = ROOT / "paper/sections/threat_model.tex"

REQUIRED_THEOREMS = [f"Theorem {idx}" for idx in range(1, 9)]
REQUIRED_THREAT_TERMS = [
    "prover",
    "verifier",
    "public input",
    "private witness",
    "reward",
    "public minari/d4rl",
    "honest collection",
]
NON_THEOREMS = [
    "true recursive aggregation",
    "full dqn training",
    "adam",
    "honest public dataset collection",
]
UNSAFE_PHRASES = [
    "we prove offline dqn training",
    "prove full dqn training",
    "true recursive aggregation soundness",
    "public benchmark honest collection proof",
]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def check_theorem_artifact_map(root: Path | None = None) -> Dict[str, Any]:
    base = root or ROOT
    paths = {
        "theorem_map": base / "docs/theorem_artifact_map.md",
        "theorems_tex": base / "paper/sections/theorems.tex",
        "threat_model_tex": base / "paper/sections/threat_model.tex",
    }
    missing_files = [name for name, path in paths.items() if not path.exists()]
    combined = "\n".join(_read(path) for path in paths.values())
    lower = combined.lower()
    map_text = _read(paths["theorem_map"])
    map_lower = map_text.lower()
    theorem_missing = [label for label in REQUIRED_THEOREMS if label.lower() not in lower]
    threat_missing = [term for term in REQUIRED_THREAT_TERMS if term not in lower]
    non_theorem_missing = [term for term in NON_THEOREMS if term not in map_lower]
    unsafe = [phrase for phrase in UNSAFE_PHRASES if phrase in lower]
    artifact_gaps: List[str] = []
    for label in REQUIRED_THEOREMS:
        line = next((item for item in map_text.splitlines() if label in item), "")
        if not line:
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 9:
            artifact_gaps.append(f"{label}: expected theorem map table row")
            continue
        for index, name in [(2, "relation/component"), (3, "backend/verifier"), (4, "tests"), (6, "Table 2 evidence"), (7, "Table 3 evidence")]:
            if not cells[index]:
                artifact_gaps.append(f"{label}: missing {name}")
        if cells[5].lower() != "n/a":
            artifact_gaps.append(f"{label}: Table 1 N/A reason missing")
    theorem7 = "\n".join(item for item in combined.splitlines() if "Theorem 7" in item or "proof-manifest" in item.lower() or "recursive" in item.lower())
    theorem7_lower = theorem7.lower()
    if "proof-manifest" not in theorem7_lower and "chunk-chain" not in theorem7_lower:
        artifact_gaps.append("Theorem 7 must be proof-manifest/chunk-chain scoped")
    if "not true recursive" not in lower and "not recursively verify" not in lower:
        artifact_gaps.append("Theorem 7 must explicitly state it is not true recursive")

    reasons = []
    if missing_files:
        reasons.append("missing files: " + ", ".join(missing_files))
    if theorem_missing:
        reasons.append("missing theorem labels: " + ", ".join(theorem_missing))
    if threat_missing:
        reasons.append("missing threat model terms: " + ", ".join(threat_missing))
    if non_theorem_missing:
        reasons.append("missing non-theorems: " + ", ".join(non_theorem_missing))
    if unsafe:
        reasons.append("unsafe phrases: " + ", ".join(unsafe))
    if artifact_gaps:
        reasons.append("artifact mapping gaps: " + "; ".join(artifact_gaps[:20]))

    return {
        "status": "passed" if not reasons else "failed",
        "missing_files": missing_files,
        "missing_theorems": theorem_missing,
        "missing_threat_terms": threat_missing,
        "missing_non_theorems": non_theorem_missing,
        "unsafe_phrases": unsafe,
        "artifact_gaps": artifact_gaps,
        "reason": "; ".join(reasons) if reasons else None,
    }


def main() -> int:
    result = check_theorem_artifact_map()
    print("theorem_artifact_map_check = " + result["status"])
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())

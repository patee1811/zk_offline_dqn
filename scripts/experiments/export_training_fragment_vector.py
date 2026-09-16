"""Export a training_fragment vector bound to a committed dataset.

The point of the export is the assertion at the end: the root the relation
derives from the transitions has to equal the root the audited pipeline wrote
into the manifest. When those two differ the proof shows consistent training on
a tree of the prover's choosing rather than on the committed dataset, which is
why the pipeline now commits under the relation's encoding.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from zk_offline_dqn.data_pipeline import (
    FIXED_POINT_LEAF_RULE,
    MERKLE_TREE_NAME,
    RAW_EPISODES_NAME,
    load_manifest,
    read_jsonl,
)
from zk_offline_dqn.relations.training_fragment import generate_case, verify_case
from zk_offline_dqn.zk_specs import encode_fp

# The relation carries the learning rate as a fixed-point integer, so only
# multiples of 1/FP_SCALE exist. 0.05 is what the Table 1 controls selected.
DEFAULT_LEARNING_RATE_FP = 50


def fixed_point_transitions(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """The transitions as the committed Merkle leaves encode them."""
    return [
        {
            "state": [encode_fp(float(value)) for value in row["state"]],
            "next_state": [encode_fp(float(value)) for value in row["next_state"]],
            "action": int(row["action"]),
            "reward": encode_fp(float(row["reward"])),
            "terminated": bool(row["terminated"]),
            "truncated": bool(row["truncated"]),
        }
        for row in rows
    ]


def provenance_from(dataset_dir: Path) -> Dict[str, Any]:
    manifest = load_manifest(dataset_dir)
    merkle_tree = json.loads((dataset_dir / MERKLE_TREE_NAME).read_text(encoding="utf-8"))
    if merkle_tree.get("leaf_hash_rule") != FIXED_POINT_LEAF_RULE:
        raise SystemExit(
            f"{dataset_dir.name} is committed under {merkle_tree.get('leaf_hash_rule')}; "
            "the training relation can only bind to a fixed-point commitment"
        )
    return {
        "dataset_id_hash": hashlib.sha256(
            str(manifest["dataset_id"]).encode("utf-8")
        ).hexdigest(),
        "dataset_type": manifest["dataset_type"],
        "manifest_hash": merkle_tree["manifest_hash"],
        "audit_report_hash": merkle_tree["audit_report_hash"],
        "collection_log_final_hash": merkle_tree["collection_log_final_hash"],
        "raw_trajectory_hash": merkle_tree["raw_trajectory_hash"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-dir", required=True)
    parser.add_argument("--layer-sizes", nargs="+", type=int, required=True)
    parser.add_argument("--num-steps", type=int, default=1)
    parser.add_argument("--learning-rate-fp", type=int, default=DEFAULT_LEARNING_RATE_FP)
    parser.add_argument("--case-id", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    if len(args.layer_sizes) != 3:
        raise SystemExit("the relation supports exactly one hidden layer")

    dataset_dir = Path(args.dataset_dir)
    manifest = load_manifest(dataset_dir)
    rows = read_jsonl(dataset_dir / RAW_EPISODES_NAME)
    transitions = fixed_point_transitions(rows)

    vector = generate_case(
        args.num_steps,
        case_id=args.case_id,
        layer_sizes=args.layer_sizes,
        dataset=transitions,
        provenance=provenance_from(dataset_dir),
        learning_rate=args.learning_rate_fp,
    )

    public = vector["public_inputs"]
    committed_root = manifest["merkle_root"]
    if public["dataset_root"] != committed_root:
        raise SystemExit(
            "dataset_root does not match the committed root:\n"
            f"  relation  {public['dataset_root']}\n"
            f"  committed {committed_root}"
        )
    result = verify_case(vector)
    if not result.accepted:
        raise SystemExit(f"the relation rejected its own vector: {result.reason}")

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(vector, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(f"case_id = {public['case_id']}")
    print(f"dataset_id = {manifest['dataset_id']}")
    print(f"dataset_root = {public['dataset_root']}")
    print(f"matches_committed_merkle_root = True")
    print(f"dataset_size = {public['dataset_size']}")
    print(f"layer_sizes = {list(args.layer_sizes)}")
    print(f"learning_rate_fp = {public['learning_rate']}")
    print(f"num_steps = {public['num_steps']}")
    print(f"out = {out.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

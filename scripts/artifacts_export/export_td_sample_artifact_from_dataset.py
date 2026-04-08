import argparse
import json
import os

from zk_offline_dqn.artifact_export_utils import (
    compute_td_witness,
    dataset_name_from_path,
    file_sha256,
    load_checkpoint_nets,
    load_merkle_artifact,
    load_transition_dataset,
    prepare_checked_transition_membership,
)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Export single-sample TD artifact directly from dataset + Merkle + checkpoint."
    )
    parser.add_argument("--data", type=str, required=True)
    parser.add_argument("--merkle", type=str, required=True)
    parser.add_argument("--checkpoint", type=str, required=True)
    parser.add_argument("--index", type=int, required=True)
    parser.add_argument("--out", type=str, required=True)
    return parser.parse_args()


def main():
    args = parse_args()

    data = load_transition_dataset(args.data)
    merkle = load_merkle_artifact(args.merkle)
    dataset_root = merkle["merkle_root"]

    _, online_net, target_net = load_checkpoint_nets(args.checkpoint)
    checkpoint_sha256 = file_sha256(args.checkpoint)

    membership = prepare_checked_transition_membership(
        data=data,
        merkle=merkle,
        idx=args.index,
    )

    witness_pack = compute_td_witness(
        transition=membership["transition"],
        online_net=online_net,
        target_net=target_net,
    )

    artifact = {
        "public": {
            "dataset_root": dataset_root,
            "loss_type": "smooth_l1",
            "checkpoint_sha256": checkpoint_sha256,
        },
        "transition_membership": {
            "dataset_name": dataset_name_from_path(args.data),
            "target_index": membership["index"],
            "dataset_root": dataset_root,
            "transition": membership["transition"],
            "leaf": membership["leaf"],
            "leaf_hash": membership["leaf_hash"],
            "merkle_path": membership["merkle_path"],
            "path_length": membership["path_length"],
        },
        "td_witness": witness_pack["td_witness"],
        "notes": {
            "checkpoint_path": args.checkpoint,
            "q_online_real_for_debug": witness_pack["debug"]["q_online_real_for_debug"],
            "q_next_online_for_debug": witness_pack["debug"]["q_next_online_for_debug"],
            "q_next_target_for_debug": witness_pack["debug"]["q_next_target_for_debug"],
            "next_action_online_for_debug": witness_pack["debug"]["next_action_online_for_debug"],
            "q_target_max_real_for_debug": witness_pack["debug"]["q_target_max_real_for_debug"],
            "q_target_source": "double_dqn_target_net_at_online_argmax",
            "purpose": "single-sample TD artifact built directly from dataset + merkle + checkpoint",
        },
    }

    out_dir = os.path.dirname(args.out)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(artifact, f, indent=2)

    print("=== TD SAMPLE ARTIFACT EXPORTED FROM DATASET ===")
    print("output_path =", args.out)
    print("data_path =", args.data)
    print("merkle_path =", args.merkle)
    print("dataset_root =", dataset_root)
    print("target_index =", args.index)
    print("checkpoint_path =", args.checkpoint)
    print("checkpoint_sha256 =", checkpoint_sha256)
    print("loss_type =", artifact["public"]["loss_type"])
    print("q_online_fp =", artifact["td_witness"]["q_online_fp"])
    print("q_target_max_fp =", artifact["td_witness"]["q_target_max_fp"])
    print("target_fp =", artifact["td_witness"]["target_fp"])
    print("loss_fp =", artifact["td_witness"]["loss_fp"])
    print("path_length =", artifact["transition_membership"]["path_length"])


if __name__ == "__main__":
    main()
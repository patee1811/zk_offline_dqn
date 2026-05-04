import argparse
import copy
import json
import os
from typing import Any, Dict, List

import torch

from zk_offline_dqn import zk_specs
from zk_offline_dqn.artifact_export_utils import (
    compute_td_witness,
    compute_training_loss,
    file_sha256,
    load_checkpoint_nets,
    load_merkle_artifact,
    load_transition_dataset,
    parse_indices,
    prepare_checked_transition_membership,
)
from zk_offline_dqn.artifact_schema_versions import SCHEMA_ONE_STEP_UPDATE_V1
from zk_offline_dqn.commitments import canonical_checkpoint_state_commitments

encode_fp = zk_specs.encode_fp


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export a pre-ZK artifact for one offline DQN SGD update step."
    )
    parser.add_argument("--data", type=str, required=True)
    parser.add_argument("--merkle", type=str, required=True)
    parser.add_argument("--checkpoint", type=str, required=True)
    parser.add_argument("--indices", type=str, required=True)
    parser.add_argument("--lr", type=float, required=True)
    parser.add_argument("--post-checkpoint-out", type=str, required=True)
    parser.add_argument("--out", type=str, required=True)
    return parser.parse_args()


def grad_and_delta_summary(
    pre_params: Dict[str, torch.Tensor],
    grad_params: Dict[str, torch.Tensor],
    post_params: Dict[str, torch.Tensor],
) -> List[str]:
    lines = []

    for name in pre_params.keys():
        grad_t = grad_params[name]
        delta_t = post_params[name] - pre_params[name]

        lines.append(
            f"{name}: "
            f"shape={tuple(pre_params[name].shape)} "
            f"grad_norm={float(grad_t.norm().item()):.8f} "
            f"delta_norm={float(delta_t.norm().item()):.8f}"
        )

    return lines


def main() -> None:
    args = parse_args()

    indices = parse_indices(args.indices)

    data = load_transition_dataset(args.data)
    merkle = load_merkle_artifact(args.merkle)
    dataset_root = merkle["merkle_root"]

    ckpt, online_net, target_net = load_checkpoint_nets(args.checkpoint)

    pre_checkpoint_sha256 = file_sha256(args.checkpoint)
    pre_state_commitments = canonical_checkpoint_state_commitments(ckpt)

    items = []
    transitions = []
    total_loss_fp = 0

    for idx in indices:
        membership = prepare_checked_transition_membership(
            data=data,
            merkle=merkle,
            idx=idx,
        )

        witness_pack = compute_td_witness(
            transition=membership["transition"],
            online_net=online_net,
            target_net=target_net,
        )

        item = {
            "index": membership["index"],
            "transition": membership["transition"],
            "leaf": membership["leaf"],
            "leaf_hash": membership["leaf_hash"],
            "merkle_path": membership["merkle_path"],
            "td_witness": witness_pack["td_witness"],
        }

        items.append(item)
        transitions.append(membership["transition"])
        total_loss_fp += witness_pack["td_witness"]["loss_fp"]

    batch_size = len(items)
    batch_loss_fp = total_loss_fp // batch_size

    optimizer = torch.optim.SGD(online_net.parameters(), lr=args.lr)

    pre_params = {
        name: p.detach().cpu().clone()
        for name, p in online_net.named_parameters()
    }

    optimizer.zero_grad()

    training_loss = compute_training_loss(
        online_net=online_net,
        target_net=target_net,
        transitions=transitions,
    )

    training_loss.backward()

    grad_params = {
        name: p.grad.detach().cpu().clone()
        for name, p in online_net.named_parameters()
    }

    optimizer.step()

    post_params = {
        name: p.detach().cpu().clone()
        for name, p in online_net.named_parameters()
    }

    gradient_tensors = {
        name: grad_params[name].tolist()
        for name in grad_params
    }

    delta_tensors = {
        name: (post_params[name] - pre_params[name]).tolist()
        for name in post_params
    }

    post_ckpt = copy.deepcopy(ckpt)
    post_ckpt["model_state_dict"] = copy.deepcopy(online_net.state_dict())
    post_ckpt["target_net_state_dict"] = copy.deepcopy(target_net.state_dict())

    if isinstance(post_ckpt.get("step", None), int):
        post_ckpt["step"] = post_ckpt["step"] + 1
    else:
        post_ckpt["step"] = 1

    post_ckpt["source_checkpoint_sha256"] = pre_checkpoint_sha256
    post_ckpt["one_step_update_metadata"] = {
        "optimizer_type": "sgd",
        "learning_rate": args.lr,
        "batch_indices": indices,
        "artifact_path_hint": args.out,
    }

    post_state_commitments = canonical_checkpoint_state_commitments(post_ckpt)

    post_ckpt_dir = os.path.dirname(args.post_checkpoint_out)
    if post_ckpt_dir:
        os.makedirs(post_ckpt_dir, exist_ok=True)

    torch.save(post_ckpt, args.post_checkpoint_out)
    post_checkpoint_sha256 = file_sha256(args.post_checkpoint_out)

    artifact = {
        "schema_version": SCHEMA_ONE_STEP_UPDATE_V1,
        "public": {
            "dataset_root": dataset_root,
            "batch_indices": indices,
            "batch_size": batch_size,
            "loss_type": "smooth_l1",
            "optimizer_type": "sgd",
            "learning_rate_fp": encode_fp(args.lr),
            "pre_checkpoint_sha256": pre_checkpoint_sha256,
            "post_checkpoint_sha256": post_checkpoint_sha256,
            "checkpoint_commitment_type": "sha256_file_and_canonical_state_dicts",
            "pre_online_state_dict_key": pre_state_commitments["online_state_dict_key"],
            "pre_online_state_dict_sha256": pre_state_commitments[
                "online_state_dict_sha256"
            ],
            "pre_target_state_dict_sha256": pre_state_commitments[
                "target_state_dict_sha256"
            ],
            "post_online_state_dict_key": post_state_commitments["online_state_dict_key"],
            "post_online_state_dict_sha256": post_state_commitments[
                "online_state_dict_sha256"
            ],
            "post_target_state_dict_sha256": post_state_commitments[
                "target_state_dict_sha256"
            ],
        },
        "items": items,
        "update_witness": {
            "batch_loss_fp": batch_loss_fp,
            "gradient_tensors": gradient_tensors,
            "delta_tensors": delta_tensors,
        },
        "notes": {},
    }

    out_dir = os.path.dirname(args.out)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(artifact, f, indent=2)

    print("=== ONE-STEP UPDATE ARTIFACT EXPORTED ===")
    print("artifact_path =", args.out)
    print("post_checkpoint_out =", args.post_checkpoint_out)
    print("dataset_root =", dataset_root)
    print("batch_indices =", indices)
    print("batch_size =", batch_size)
    print("optimizer_type = sgd")
    print("learning_rate =", args.lr)
    print("learning_rate_fp =", encode_fp(args.lr))
    print("batch_loss_fp =", batch_loss_fp)
    print("training_loss_real_for_log =", float(training_loss.item()))
    print("pre_checkpoint_sha256 =", pre_checkpoint_sha256)
    print("post_checkpoint_sha256 =", post_checkpoint_sha256)
    print("checkpoint_commitment_type =", artifact["public"]["checkpoint_commitment_type"])
    print("pre_online_state_dict_key =", artifact["public"]["pre_online_state_dict_key"])
    print(
        "pre_online_state_dict_sha256 =",
        artifact["public"]["pre_online_state_dict_sha256"],
    )
    print(
        "pre_target_state_dict_sha256 =",
        artifact["public"]["pre_target_state_dict_sha256"],
    )
    print("post_online_state_dict_key =", artifact["public"]["post_online_state_dict_key"])
    print(
        "post_online_state_dict_sha256 =",
        artifact["public"]["post_online_state_dict_sha256"],
    )
    print(
        "post_target_state_dict_sha256 =",
        artifact["public"]["post_target_state_dict_sha256"],
    )
    print()

    print("=== PARAMETER UPDATE SUMMARY FOR LOG ONLY ===")
    for line in grad_and_delta_summary(
        pre_params=pre_params,
        grad_params=grad_params,
        post_params=post_params,
    ):
        print(line)


if __name__ == "__main__":
    main()
import argparse
import copy
import hashlib
import json
import os
from typing import Dict, List

import torch
import torch.nn.functional as F

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

encode_fp = zk_specs.encode_fp
ONE_FP = encode_fp(1.0)
GAMMA_FP = getattr(zk_specs, "GAMMA_FP", encode_fp(0.99))
GAMMA_REAL = GAMMA_FP / ONE_FP

def parse_args():
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


def tensor_sha256(t: torch.Tensor) -> str:
    arr = t.detach().cpu().contiguous()
    h = hashlib.sha256()
    h.update(str(arr.dtype).encode("utf-8"))
    h.update(str(tuple(arr.shape)).encode("utf-8"))
    h.update(arr.numpy().tobytes())
    return h.hexdigest()


def state_dict_sha256(state_dict: Dict[str, torch.Tensor]) -> str:
    h = hashlib.sha256()
    for key in sorted(state_dict.keys()):
        t = state_dict[key].detach().cpu().contiguous()
        h.update(key.encode("utf-8"))
        h.update(str(t.dtype).encode("utf-8"))
        h.update(str(tuple(t.shape)).encode("utf-8"))
        h.update(t.numpy().tobytes())
    return h.hexdigest()


def summarize_parameter_updates(pre_params, grad_params, post_params):
    summaries = []

    for name in pre_params.keys():
        pre_t = pre_params[name]
        grad_t = grad_params[name]
        post_t = post_params[name]
        delta_t = post_t - pre_t

        summaries.append(
            {
                "name": name,
                "shape": list(pre_t.shape),
                "numel": int(pre_t.numel()),
                "pre_param_sha256": tensor_sha256(pre_t),
                "grad_sha256": tensor_sha256(grad_t),
                "post_param_sha256": tensor_sha256(post_t),
                "delta_sha256": tensor_sha256(delta_t),
                "pre_norm": float(pre_t.norm().item()),
                "grad_norm": float(grad_t.norm().item()),
                "post_norm": float(post_t.norm().item()),
                "delta_norm": float(delta_t.norm().item()),
                "pre_mean": float(pre_t.mean().item()),
                "grad_mean": float(grad_t.mean().item()),
                "post_mean": float(post_t.mean().item()),
                "delta_mean": float(delta_t.mean().item()),
            }
        )

    return summaries


def main():
    args = parse_args()

    indices = parse_indices(args.indices)
    data = load_transition_dataset(args.data)
    merkle = load_merkle_artifact(args.merkle)
    dataset_root = merkle["merkle_root"]

    ckpt, online_net, target_net = load_checkpoint_nets(args.checkpoint)

    pre_checkpoint_sha256 = file_sha256(args.checkpoint)
    pre_online_state_sha256 = state_dict_sha256(online_net.state_dict())
    target_state_sha256 = state_dict_sha256(target_net.state_dict())

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
            "debug": witness_pack["debug"],
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

    parameter_summaries = summarize_parameter_updates(
        pre_params=pre_params,
        grad_params=grad_params,
        post_params=post_params,
    )

    post_online_state_sha256 = state_dict_sha256(online_net.state_dict())

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

    post_ckpt_dir = os.path.dirname(args.post_checkpoint_out)
    if post_ckpt_dir:
        os.makedirs(post_ckpt_dir, exist_ok=True)

    torch.save(post_ckpt, args.post_checkpoint_out)
    post_checkpoint_sha256 = file_sha256(args.post_checkpoint_out)

    artifact = {
        "public": {
            "dataset_root": dataset_root,
            "batch_indices": indices,
            "batch_size": batch_size,
            "loss_type": "smooth_l1",
            "optimizer_type": "sgd",
            "learning_rate_fp": encode_fp(args.lr),
            "learning_rate_real": args.lr,
            "pre_checkpoint_sha256": pre_checkpoint_sha256,
            "post_checkpoint_sha256": post_checkpoint_sha256,
        },
        "items": items,
        "update_witness": {
            "batch_loss_fp": batch_loss_fp,
            "batch_loss_real_for_training": float(training_loss.item()),
            "pre_online_state_sha256": pre_online_state_sha256,
            "post_online_state_sha256": post_online_state_sha256,
            "target_state_sha256": target_state_sha256,
            "parameter_count": int(sum(p.numel() for p in online_net.parameters())),
            "parameter_summaries": parameter_summaries,
            "gradient_tensors": gradient_tensors,
            "delta_tensors": delta_tensors,
        },
        "notes": {
            "checkpoint_path": args.checkpoint,
            "post_checkpoint_path": args.post_checkpoint_out,
            "data_path": args.data,
            "merkle_path_source": args.merkle,
            "q_target_source": "double_dqn_target_net_at_online_argmax",
            "statement_scope": "one offline DQN SGD update step from committed minibatch",
            "limitations": [
                "pre-ZK artifact only",
                "no standalone verifier for gradient correctness yet",
                "target network kept fixed during this one-step statement",
                "no sampler-rule verification beyond explicit batch indices",
            ],
        },
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
    print("batch_loss_real_for_training =", float(training_loss.item()))
    print("pre_checkpoint_sha256 =", pre_checkpoint_sha256)
    print("post_checkpoint_sha256 =", post_checkpoint_sha256)
    print("pre_online_state_sha256 =", pre_online_state_sha256)
    print("post_online_state_sha256 =", post_online_state_sha256)
    print("target_state_sha256 =", target_state_sha256)
    print()
    print("=== PARAMETER UPDATE SUMMARY ===")
    for s in parameter_summaries:
        print(
            f"{s['name']}: "
            f"shape={tuple(s['shape'])} "
            f"grad_norm={s['grad_norm']:.8f} "
            f"delta_norm={s['delta_norm']:.8f}"
        )


if __name__ == "__main__":
    main()
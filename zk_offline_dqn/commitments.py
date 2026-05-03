# zk_offline_dqn/commitments.py

import hashlib
from typing import Dict

import numpy as np
import torch


def _canonical_tensor_bytes(tensor: torch.Tensor) -> bytes:
    """Return deterministic bytes for a tensor.

    The encoding includes dtype, shape, and raw CPU-contiguous tensor bytes.
    This is more stable as a model-state commitment than hashing a whole
    torch checkpoint file directly.
    """
    arr = tensor.detach().cpu().contiguous().numpy()

    header = (
        f"dtype={arr.dtype};"
        f"shape={tuple(arr.shape)};"
    ).encode("utf-8")

    return header + arr.tobytes(order="C")


def canonical_state_dict_sha256(state_dict: Dict[str, torch.Tensor]) -> str:
    """Hash a PyTorch state_dict in a deterministic key-sorted order."""
    h = hashlib.sha256()

    for key in sorted(state_dict.keys()):
        tensor = state_dict[key]

        if not isinstance(tensor, torch.Tensor):
            raise TypeError(
                f"Expected tensor for state_dict[{key!r}], got {type(tensor)!r}"
            )

        key_bytes = key.encode("utf-8")
        value_bytes = _canonical_tensor_bytes(tensor)

        h.update(len(key_bytes).to_bytes(8, "big"))
        h.update(key_bytes)
        h.update(len(value_bytes).to_bytes(8, "big"))
        h.update(value_bytes)

    return h.hexdigest()


def canonical_checkpoint_state_commitments(checkpoint: Dict) -> Dict[str, str]:
    """Return canonical SHA-256 commitments for online and target networks.

    Supports checkpoints that store the online network as either:
    - online_net_state_dict
    - model_state_dict
    """
    if "online_net_state_dict" in checkpoint:
        online_key = "online_net_state_dict"
    elif "model_state_dict" in checkpoint:
        online_key = "model_state_dict"
    else:
        raise KeyError(
            "Checkpoint missing online network state dict. "
            "Expected online_net_state_dict or model_state_dict."
        )

    if "target_net_state_dict" not in checkpoint:
        raise KeyError("Checkpoint missing target_net_state_dict.")

    return {
        "online_state_dict_key": online_key,
        "online_state_dict_sha256": canonical_state_dict_sha256(
            checkpoint[online_key]
        ),
        "target_state_dict_sha256": canonical_state_dict_sha256(
            checkpoint["target_net_state_dict"]
        ),
    }
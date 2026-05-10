import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Union

import torch


PathLike = Union[str, Path]


def file_sha256(path: PathLike) -> str:
    h = hashlib.sha256()

    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)

    return h.hexdigest()


def load_json(path: PathLike) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: PathLike, data: Dict[str, Any], indent: int = 2) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent)
        f.write("\n")


def load_torch_checkpoint(path: PathLike) -> Dict[str, Any]:
    return torch.load(path, map_location="cpu", weights_only=False)

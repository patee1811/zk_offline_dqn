"""Artifact JSON IO wrappers preserving existing repository behavior."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Union

from zk_offline_dqn.io_utils import load_json, write_json


PathLike = Union[str, Path]


def load_json_artifact(path: PathLike) -> Dict[str, Any]:
    return load_json(path)


def write_json_artifact(path: PathLike, data: Dict[str, Any], indent: int = 2) -> None:
    write_json(path, data, indent=indent)

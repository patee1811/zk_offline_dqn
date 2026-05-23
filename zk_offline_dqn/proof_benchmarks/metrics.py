from __future__ import annotations

import hashlib
import json
import os
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

try:  # pragma: no cover - import availability is platform-dependent.
    import resource
except ModuleNotFoundError:  # Windows local development.
    resource = None


STATUS_VALUES = {
    "proof_verified",
    "execute_only",
    "reference_only",
    "not_supported_current_backend",
    "failed_oom",
    "failed_environment",
    "failed_timeout",
    "failed_compile",
    "failed_verify",
    "skipped_incompatible",
}


@dataclass(frozen=True)
class MeasuredCommand:
    command: List[str]
    returncode: int
    elapsed_seconds: float
    peak_rss_mb: float | None
    stdout: str
    stderr: str


def validate_status(value: str) -> str:
    if value not in STATUS_VALUES:
        raise ValueError(f"unsupported Phase 8.2 status: {value}")
    return value


def sha256_file(path: str | Path) -> str | None:
    target = Path(path)
    if not target.exists():
        return None
    digest = hashlib.sha256()
    with target.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def proof_size(path: str | Path) -> int | None:
    target = Path(path)
    return target.stat().st_size if target.exists() else None


def load_json(path: str | Path) -> Dict[str, Any] | None:
    target = Path(path)
    if not target.exists():
        return None
    with target.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    return data if isinstance(data, dict) else None


def metric_value(metrics: Dict[str, Any], *names: str) -> Any:
    for name in names:
        if name in metrics:
            return metrics[name]
    return None


def normalize_metrics(metrics: Dict[str, Any] | None) -> Dict[str, Any]:
    data = metrics or {}
    return {
        "prove_time_seconds": metric_value(data, "prove_time_seconds", "proving_time_sec"),
        "verify_time_seconds": metric_value(data, "verify_time_seconds", "verification_time_sec"),
        "proof_size_bytes": metric_value(data, "proof_size_bytes"),
        "cycle_count": metric_value(data, "cycle_count"),
        "prover_gas": metric_value(data, "prover_gas"),
        "peak_rss_mb": metric_value(data, "peak_rss_mb", "peak_rss_megabytes"),
        "max_rss_mb": metric_value(data, "max_rss_mb", "max_rss_megabytes"),
        "backend_version": metric_value(data, "backend_version"),
        "sp1_version": metric_value(data, "sp1_version"),
        "git_commit": metric_value(data, "git_commit"),
        "public_inputs_sha256": metric_value(data, "public_inputs_sha256"),
        "witness_schema_sha256": metric_value(data, "witness_schema_sha256"),
        "proof_generated": metric_value(data, "proof_generated"),
        "proof_verified": metric_value(data, "proof_verified"),
        "notes": metric_value(data, "notes"),
    }


def run_measured(
    command: List[str],
    *,
    cwd: str | Path | None = None,
    timeout_seconds: int | None = None,
    env: Dict[str, str] | None = None,
) -> MeasuredCommand:
    run_env = os.environ.copy()
    if env:
        run_env.update(env)
    before = _children_rss()
    started = time.perf_counter()
    try:
        result = subprocess.run(
            command,
            cwd=None if cwd is None else Path(cwd),
            env=run_env,
            text=True,
            capture_output=True,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired as exc:
        elapsed = time.perf_counter() - started
        after = _children_rss()
        return MeasuredCommand(
            command=command,
            returncode=124,
            elapsed_seconds=elapsed,
            peak_rss_mb=_rss_delta_mb(before, after),
            stdout=exc.stdout or "",
            stderr=exc.stderr or "timeout",
        )
    elapsed = time.perf_counter() - started
    after = _children_rss()
    return MeasuredCommand(
        command=command,
        returncode=result.returncode,
        elapsed_seconds=elapsed,
        peak_rss_mb=_rss_delta_mb(before, after),
        stdout=result.stdout,
        stderr=result.stderr,
    )


def _rss_delta_mb(before: int, after: int) -> float | None:
    if before < 0 or after < 0:
        return None
    peak = max(before, after)
    if peak <= 0:
        return None
    # Linux reports kilobytes; macOS reports bytes. Kaggle/Linux is the target.
    return round(float(peak) / 1024.0, 3)


def _children_rss() -> int:
    if resource is None:
        return -1
    return int(resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss)

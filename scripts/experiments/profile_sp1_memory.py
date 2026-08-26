"""Sample peak RSS of an SP1 host run and attribute it to a proving stage.

Table 2 leaves Peak RSS empty for most rows because the Rust hosts never
measured it: metrics.json records prove/verify time, proof size, and cycle
count only. That gap is why an OOM failure cannot be attributed to a stage.

This wrapper runs the host command as a child process, samples RSS on an
interval, and splits the samples at the stage markers the host already prints
on stdout ("cycle_count = ...", "proving_time_sec = ..."). It reports a peak
per stage plus an overall peak, so a failed run still yields the stage that
was resident when memory ran out.

The sampler needs psutil. It is not in requirements.txt because nothing else
uses it; install it in the proving environment only.

Example:

    python scripts/experiments/profile_sp1_memory.py \\
        --out artifacts/reports/memory_profile/training_fragment_k8.json \\
        -- cargo run --release -p training-fragment-host -- --prove
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INTERVAL_SECONDS = 0.25
BYTES_PER_MB = 1024 * 1024

# The hosts print these as they finish a stage. Order matters: a sample taken
# before any marker belongs to setup, after the first to proving, and so on.
STAGE_MARKERS = (
    ("execute", "cycle_count ="),
    ("prove", "proving_time_sec ="),
    ("verify", "verification_time_sec ="),
)
STAGE_ORDER = ("setup", "execute", "prove", "verify", "teardown")


class Sampler(threading.Thread):
    """Poll RSS of a process tree until asked to stop."""

    def __init__(self, pid: int, interval: float) -> None:
        super().__init__(daemon=True)
        self.pid = pid
        self.interval = interval
        self.samples: List[Dict[str, float]] = []
        self.error: Optional[str] = None
        self._done = threading.Event()

    def run(self) -> None:
        try:
            import psutil
        except ImportError:
            self.error = "psutil is not installed; run: pip install psutil"
            return

        try:
            root = psutil.Process(self.pid)
        except psutil.NoSuchProcess:
            self.error = f"process {self.pid} exited before sampling started"
            return

        start = time.monotonic()
        while not self._done.is_set():
            total = 0
            try:
                procs = [root] + root.children(recursive=True)
            except psutil.NoSuchProcess:
                break
            for proc in procs:
                try:
                    total += proc.memory_info().rss
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            if total > 0:
                self.samples.append(
                    {
                        "elapsed_seconds": round(time.monotonic() - start, 3),
                        "rss_mb": round(total / BYTES_PER_MB, 3),
                    }
                )
            self._done.wait(self.interval)

    def stop(self) -> None:
        self._done.set()


def stage_at(elapsed: float, boundaries: Dict[str, float]) -> str:
    """Name the stage that was running at `elapsed` seconds."""
    stage = "setup"
    for name, marker_time in boundaries.items():
        if elapsed >= marker_time:
            stage = STAGE_ORDER[STAGE_ORDER.index(name) + 1]
    return stage


def summarize(samples: List[Dict[str, float]], boundaries: Dict[str, float]) -> Dict[str, Any]:
    per_stage: Dict[str, List[float]] = {name: [] for name in STAGE_ORDER}
    for sample in samples:
        per_stage[stage_at(sample["elapsed_seconds"], boundaries)].append(sample["rss_mb"])

    stages = {}
    for name, values in per_stage.items():
        if not values:
            continue
        stages[name] = {
            "peak_rss_mb": max(values),
            "mean_rss_mb": round(sum(values) / len(values), 3),
            "samples": len(values),
        }

    return {
        "peak_rss_mb": max((s["rss_mb"] for s in samples), default=None),
        "peak_stage": max(stages, key=lambda k: stages[k]["peak_rss_mb"], default=None)
        if stages
        else None,
        "stages": stages,
        "sample_count": len(samples),
    }


def run(command: List[str], interval: float, cwd: Optional[Path] = None) -> Dict[str, Any]:
    started = time.monotonic()
    process = subprocess.Popen(
        command,
        cwd=str(cwd or ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    sampler = Sampler(process.pid, interval)
    sampler.start()

    boundaries: Dict[str, float] = {}
    output: List[str] = []
    assert process.stdout is not None
    for line in process.stdout:
        sys.stdout.write(line)
        output.append(line.rstrip("\n"))
        for stage, marker in STAGE_MARKERS:
            if marker in line and stage not in boundaries:
                boundaries[stage] = round(time.monotonic() - started, 3)

    returncode = process.wait()
    sampler.stop()
    sampler.join(timeout=5)

    result: Dict[str, Any] = {
        "command": command,
        "cwd": str(cwd or ROOT),
        "returncode": returncode,
        "status": "completed" if returncode == 0 else "failed",
        "wall_seconds": round(time.monotonic() - started, 3),
        "sample_interval_seconds": interval,
        "stage_boundaries_seconds": boundaries,
        "stdout_tail": output[-40:],
    }
    if sampler.error:
        result["sampler_error"] = sampler.error
        result["memory"] = None
        return result

    result["memory"] = summarize(sampler.samples, boundaries)
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        help="Write the JSON profile here. Prints to stdout when omitted.",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=DEFAULT_INTERVAL_SECONDS,
        help=f"Seconds between RSS samples (default {DEFAULT_INTERVAL_SECONDS}).",
    )
    parser.add_argument(
        "--label",
        default="",
        help="Row label, e.g. training_fragment_k8. Recorded in the output.",
    )
    parser.add_argument(
        "--cwd",
        help="Directory to run the command in. Defaults to the repo root; an "
        "SP1 host needs its own workspace so cargo can find Cargo.toml.",
    )
    parser.add_argument(
        "command",
        nargs=argparse.REMAINDER,
        help="Host command, after a bare --.",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    # argparse.REMAINDER keeps the leading "--". Drop only that one: a
    # `cargo run -p host -- --prove` needs its second separator intact, or
    # cargo claims --prove for itself.
    command = list(args.command)
    if command and command[0] == "--":
        command = command[1:]
    if not command:
        sys.stderr.write("no command given; pass it after --\n")
        return 2

    result = run(command, args.interval, Path(args.cwd) if args.cwd else None)
    result["label"] = args.label

    payload = json.dumps(result, indent=2, sort_keys=True)
    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(payload + "\n", encoding="utf-8")
        print(f"memory_profile = {out_path.as_posix()}")
    else:
        print(payload)

    memory = result.get("memory")
    if memory:
        print(f"peak_rss_mb = {memory['peak_rss_mb']}")
        print(f"peak_stage = {memory['peak_stage']}")
    return 0 if result["returncode"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

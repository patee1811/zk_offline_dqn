from __future__ import annotations

import argparse
import copy
import csv
import json
import os
import pickle
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import gymnasium as gym
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.artifacts_export.export_forward_td_mlp_test_vector import (  # noqa: E402
    build_forward_td_vector,
)
from zk_offline_dqn import zk_specs  # noqa: E402
from zk_offline_dqn.merkle import build_merkle_levels, build_merkle_path, hash_leaf  # noqa: E402


DEFAULT_OUT_DIR = ROOT / "artifacts/benchmarks/second_env_mountaincar"
PYTHON_VERIFIER = ROOT / "scripts/artifacts_export/verify_forward_td_mlp_test_vector.py"
SP1_DIR = ROOT / "zk_backend/td_mvp/sp1"


def write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_pickle(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as f:
        pickle.dump(data, f)


def parse_batch_sizes(raw: str) -> List[int]:
    values = [int(item.strip()) for item in raw.split(",") if item.strip()]
    if not values:
        raise ValueError("at least one batch size is required")
    if any(value <= 0 for value in values):
        raise ValueError(f"batch sizes must be positive, got {values}")
    return values


def run_command(
    command: List[str],
    *,
    cwd: Path,
    stdout_path: Path,
    stderr_path: Path,
) -> Dict[str, Any]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT)
    started = time.perf_counter()
    result = subprocess.run(
        command,
        cwd=cwd,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    elapsed_sec = time.perf_counter() - started
    stdout_path.parent.mkdir(parents=True, exist_ok=True)
    stdout_path.write_text(result.stdout, encoding="utf-8")
    stderr_path.write_text(result.stderr, encoding="utf-8")
    return {
        "command": " ".join(command),
        "returncode": result.returncode,
        "elapsed_sec": round(elapsed_sec, 6),
        "stdout": result.stdout,
        "stderr": result.stderr,
        "stdout_path": stdout_path.relative_to(ROOT).as_posix(),
        "stderr_path": stderr_path.relative_to(ROOT).as_posix(),
    }


def parse_key_values(stdout: str) -> Dict[str, Any]:
    parsed: Dict[str, Any] = {}
    for line in stdout.splitlines():
        if " = " not in line:
            continue
        key, raw = line.split(" = ", 1)
        raw = raw.strip()
        if raw in {"true", "True"}:
            parsed[key.strip()] = True
        elif raw in {"false", "False"}:
            parsed[key.strip()] = False
        else:
            try:
                parsed[key.strip()] = int(raw)
            except ValueError:
                try:
                    parsed[key.strip()] = float(raw)
                except ValueError:
                    parsed[key.strip()] = raw
    return parsed


def transition_leaf(transition: Dict[str, Any]) -> List[int]:
    return zk_specs.serialize_transition_leaf(
        transition,
        obs_dim=2,
        action_dim=3,
    )


def generate_mountaincar_dataset(
    *,
    data_path: Path,
    summary_path: Path,
    target_transitions: int,
    seed: int,
) -> Dict[str, Any]:
    rng = np.random.default_rng(seed)
    env = gym.make("MountainCar-v0")
    env.action_space.seed(seed)

    obs_rows: List[np.ndarray] = []
    action_rows: List[int] = []
    reward_rows: List[float] = []
    next_obs_rows: List[np.ndarray] = []
    done_rows: List[int] = []
    episode_returns: List[float] = []
    episode_lengths: List[int] = []

    ep_idx = 0
    while len(action_rows) < target_transitions:
        obs, _ = env.reset(seed=seed + ep_idx)
        ep_return = 0.0
        ep_len = 0
        done = False
        while not done and len(action_rows) < target_transitions:
            action = int(rng.integers(0, env.action_space.n))
            next_obs, reward, terminated, truncated, _ = env.step(action)
            done = bool(terminated or truncated)

            obs_rows.append(np.asarray(obs, dtype=np.float32))
            action_rows.append(action)
            reward_rows.append(float(reward))
            next_obs_rows.append(np.asarray(next_obs, dtype=np.float32))
            done_rows.append(1 if done else 0)

            obs = next_obs
            ep_return += float(reward)
            ep_len += 1

        episode_returns.append(ep_return)
        episode_lengths.append(ep_len)
        ep_idx += 1

    env.close()

    dataset = {
        "obs": np.asarray(obs_rows, dtype=np.float32),
        "actions": np.asarray(action_rows, dtype=np.int64),
        "rewards": np.asarray(reward_rows, dtype=np.float32),
        "next_obs": np.asarray(next_obs_rows, dtype=np.float32),
        "dones": np.asarray(done_rows, dtype=np.int64),
    }
    write_pickle(data_path, dataset)

    obs_array = dataset["obs"]
    next_obs_array = dataset["next_obs"]
    summary = {
        "env": "MountainCar-v0",
        "dataset_kind": "random_policy_transition_dataset",
        "seed": seed,
        "obs_dim": 2,
        "action_dim": 3,
        "num_transitions": int(len(action_rows)),
        "num_episodes_touched": int(len(episode_lengths)),
        "avg_episode_return": float(np.mean(episode_returns)),
        "avg_episode_length": float(np.mean(episode_lengths)),
        "position_min": float(min(obs_array[:, 0].min(), next_obs_array[:, 0].min())),
        "position_max": float(max(obs_array[:, 0].max(), next_obs_array[:, 0].max())),
        "velocity_min": float(min(obs_array[:, 1].min(), next_obs_array[:, 1].min())),
        "velocity_max": float(max(obs_array[:, 1].max(), next_obs_array[:, 1].max())),
        "reward_min": float(dataset["rewards"].min()),
        "reward_max": float(dataset["rewards"].max()),
        "data_path": data_path.relative_to(ROOT).as_posix(),
    }
    write_json(summary_path, summary)
    return dataset


def transition_at(dataset: Dict[str, Any], idx: int) -> Dict[str, Any]:
    return {
        "obs": [float(value) for value in dataset["obs"][idx].tolist()],
        "action": int(dataset["actions"][idx]),
        "reward": float(dataset["rewards"][idx]),
        "next_obs": [float(value) for value in dataset["next_obs"][idx].tolist()],
        "done": int(dataset["dones"][idx]),
    }


def build_merkle_artifacts(
    *,
    dataset: Dict[str, Any],
    leaf_hashes_path: Path,
    merkle_path: Path,
) -> Dict[str, Any]:
    leaf_hashes = []
    for idx in range(len(dataset["actions"])):
        leaf_hashes.append(hash_leaf(transition_leaf(transition_at(dataset, idx))))

    levels = build_merkle_levels(leaf_hashes)
    leaf_hashes_json = {
        "dataset_name": "mountaincar_random_seed42_transitions",
        "num_transitions": len(leaf_hashes),
        "hash_function": "sha256",
        "leaf_encoding": "comma-separated signed decimal integers encoded as utf-8",
        "transition_schema": "obs[2], action[0..2], reward, next_obs[2], done",
        "leaf_hashes": leaf_hashes,
    }
    merkle_json = {
        "dataset_name": leaf_hashes_json["dataset_name"],
        "num_leaves": len(leaf_hashes),
        "leaf_hash_rule": "sha256",
        "leaf_encoding": leaf_hashes_json["leaf_encoding"],
        "internal_node_hash_rule": "sha256(bytes.fromhex(left) + bytes.fromhex(right))",
        "odd_node_rule": "duplicate_last",
        "num_levels": len(levels),
        "merkle_root": levels[-1][0],
        "levels": levels,
    }
    write_json(leaf_hashes_path, leaf_hashes_json)
    write_json(merkle_path, merkle_json)
    return merkle_json


def build_source_artifact(
    *,
    dataset: Dict[str, Any],
    merkle: Dict[str, Any],
    source_path: Path,
    indices: List[int],
) -> Dict[str, Any]:
    items = []
    for idx in indices:
        transition = transition_at(dataset, idx)
        leaf = transition_leaf(transition)
        leaf_hash = hash_leaf(leaf)
        expected_leaf_hash = merkle["levels"][0][idx]
        if leaf_hash != expected_leaf_hash:
            raise ValueError(f"leaf hash mismatch at index {idx}")
        items.append(
            {
                "index": idx,
                "transition": transition,
                "leaf": leaf,
                "leaf_hash": leaf_hash,
                "merkle_path": build_merkle_path(merkle["levels"], idx),
            }
        )

    source = {
        "schema_version": "minibatch_td_v1",
        "public": {
            "dataset_root": merkle["merkle_root"],
            "fp_scale": zk_specs.SPECS.FP_SCALE,
            "gamma_fp": zk_specs.SPECS.GAMMA_FP,
            "batch_size": len(items),
            "batch_mode": "distinct",
            "leaf_indices": [int(item["index"]) for item in items],
            "loss_type": "smooth_l1",
        },
        "items": items,
        "notes": {
            "env": "MountainCar-v0",
            "purpose": "source minibatch for second-environment forward-TD fixture",
        },
    }
    write_json(source_path, source)
    return source


def run_python_case(case_name: str, fixture_path: Path, out_dir: Path) -> Dict[str, Any]:
    result = run_command(
        [sys.executable, str(PYTHON_VERIFIER), "--input", str(fixture_path)],
        cwd=ROOT,
        stdout_path=out_dir / "logs" / f"python_{case_name}.stdout.txt",
        stderr_path=out_dir / "logs" / f"python_{case_name}.stderr.txt",
    )
    return {
        "accepted": result["returncode"] == 0,
        "returncode": result["returncode"],
        "elapsed_sec": result["elapsed_sec"],
        "stdout_path": result["stdout_path"],
        "stderr_path": result["stderr_path"],
        "metrics": parse_key_values(result["stdout"]),
    }


def run_sp1_case(
    *,
    case_name: str,
    fixture_path: Path,
    out_dir: Path,
    cargo_bin: str,
    expected_accept: bool,
    prove: bool,
) -> Dict[str, Any]:
    command = [
        cargo_bin,
        "run",
        "--release",
        "-p",
        "td-mvp-host",
        "--",
        "--input",
        str(fixture_path.resolve()),
        "--case",
        "valid_control",
        "--execute",
    ]
    if not expected_accept:
        command.append("--skip-host-precheck")
    if prove and expected_accept:
        command.append("--prove")
    result = run_command(
        command,
        cwd=SP1_DIR,
        stdout_path=out_dir / "logs" / f"sp1_{case_name}.stdout.txt",
        stderr_path=out_dir / "logs" / f"sp1_{case_name}.stderr.txt",
    )
    return {
        "accepted": result["returncode"] == 0,
        "returncode": result["returncode"],
        "elapsed_sec": result["elapsed_sec"],
        "stdout_path": result["stdout_path"],
        "stderr_path": result["stderr_path"],
        "metrics": parse_key_values(result["stdout"]),
    }


def evaluate_case(
    *,
    case_name: str,
    expected_accept: bool,
    fixture_path: Path,
    out_dir: Path,
    skip_sp1: bool,
    cargo_bin: str,
    prove: bool,
) -> Dict[str, Any]:
    python_result = run_python_case(case_name, fixture_path, out_dir)
    sp1_result: Optional[Dict[str, Any]] = None
    if not skip_sp1:
        sp1_result = run_sp1_case(
            case_name=case_name,
            fixture_path=fixture_path,
            out_dir=out_dir,
            cargo_bin=cargo_bin,
            expected_accept=expected_accept,
            prove=prove,
        )
    python_expected_ok = python_result["accepted"] == expected_accept
    sp1_expected_ok = None if sp1_result is None else sp1_result["accepted"] == expected_accept
    python_sp1_agree = (
        None if sp1_result is None else python_result["accepted"] == sp1_result["accepted"]
    )
    passed = python_expected_ok if sp1_result is None else (
        python_expected_ok and bool(sp1_expected_ok) and bool(python_sp1_agree)
    )
    return {
        "case_name": case_name,
        "expected_accept": expected_accept,
        "fixture_path": fixture_path.relative_to(ROOT).as_posix(),
        "python": python_result,
        "sp1": sp1_result,
        "python_expected_ok": python_expected_ok,
        "sp1_expected_ok": sp1_expected_ok,
        "python_sp1_agree": python_sp1_agree,
        "passed": passed,
    }


def mutate_selected_target_value(tv: Dict[str, Any]) -> None:
    tv["private"]["items"][0]["forward_witness"]["q_target_max_fp"] += 1


def mutate_argmax(tv: Dict[str, Any]) -> None:
    witness = tv["private"]["items"][0]["forward_witness"]
    action_dim = int(tv["public"]["network_layer_sizes"][-1])
    witness["next_action_online"] = (int(witness["next_action_online"]) + 1) % action_dim


def write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(path: Path, summary: Dict[str, Any]) -> None:
    lines = [
        "# MountainCar Forward-TD SP1 Benchmark Snapshot",
        "",
        "## Commands",
        "",
        "```bash",
        "python3 scripts/experiments/benchmark_mountaincar_forward_td_sp1.py --skip-sp1",
        "python3 scripts/experiments/benchmark_mountaincar_forward_td_sp1.py --prove",
        "```",
        "",
        "## Overall",
        "",
        "- Environment: `MountainCar-v0`",
        "- Relation: `forward_td_mlp_v1`",
        f"- Network spec: `{summary['layer_sizes']}`",
        f"- Merkle root: `{summary['merkle_root']}`",
        f"- Python expected outcomes passed: `{summary['all_python_expected']}`",
        f"- SP1 expected outcomes passed: `{summary['all_sp1_expected']}`",
        f"- Python/SP1 agreement: `{summary['python_sp1_agreement']}`",
        "",
        "## Matrix",
        "",
        "| Case | Batch | Status | Prove time sec | Verify time sec | Proof size bytes | Cycle count |",
        "|---|---:|---|---:|---:|---:|---:|",
    ]
    for row in summary["benchmark_matrix"]:
        lines.append(
            f"| `{row['case']}` | `{row['batch_size']}` | `{row['status']}` | "
            f"`{row['prove_time_sec']}` | `{row['verify_time_sec']}` | "
            f"`{row['proof_size_bytes']}` | `{row['cycle_count']}` |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--target-transitions", type=int, default=64)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--batch-sizes", default="1")
    parser.add_argument("--layer-sizes", default="2,8,8,3")
    parser.add_argument("--cargo-bin", default="cargo")
    parser.add_argument("--skip-sp1", action="store_true")
    parser.add_argument("--prove", action="store_true")
    args = parser.parse_args()

    out_dir = args.out_dir.resolve()
    fixtures_dir = out_dir / "fixtures"
    data_path = ROOT / "data/mountaincar_random_seed42_transitions.pkl"
    data_summary_path = ROOT / "data/mountaincar_random_seed42_transitions.summary.json"
    leaf_hashes_path = ROOT / "artifacts/fixtures/forward_td_mlp/mountaincar/mountaincar_random_seed42_leaf_hashes.json"
    merkle_path = ROOT / "artifacts/fixtures/forward_td_mlp/mountaincar/mountaincar_random_seed42_merkle.json"
    source_path = fixtures_dir / "mountaincar_source_minibatch_td.json"

    batch_sizes = parse_batch_sizes(args.batch_sizes)
    max_batch = max(batch_sizes)
    if args.target_transitions < max_batch:
        raise ValueError("--target-transitions must be at least the max batch size")

    print("=== PHASE D MOUNTAINCAR FORWARD TD SP1 BENCHMARK ===")
    print("out_dir =", out_dir)
    print("target_transitions =", args.target_transitions)
    print("batch_sizes =", batch_sizes)
    print("layer_sizes =", args.layer_sizes)
    print("skip_sp1 =", args.skip_sp1)
    print("prove =", args.prove)
    print()

    dataset = generate_mountaincar_dataset(
        data_path=data_path,
        summary_path=data_summary_path,
        target_transitions=args.target_transitions,
        seed=args.seed,
    )
    merkle = build_merkle_artifacts(
        dataset=dataset,
        leaf_hashes_path=leaf_hashes_path,
        merkle_path=merkle_path,
    )
    source = build_source_artifact(
        dataset=dataset,
        merkle=merkle,
        source_path=source_path,
        indices=list(range(max_batch)),
    )

    results: List[Dict[str, Any]] = []
    for batch_size in batch_sizes:
        case_name = f"mountaincar-forward-TD-{batch_size}"
        fixture_path = fixtures_dir / f"mountaincar_forward_td_mlp_batch_size_{batch_size}.json"
        vector = build_forward_td_vector(
            source_artifact=source,
            source_path=source_path,
            out_path=fixture_path,
            batch_size=batch_size,
            layer_sizes=[int(value) for value in args.layer_sizes.split(",")],
            online_seed=20260624,
            target_seed=20260630,
        )
        write_json(fixture_path, vector)
        result = evaluate_case(
            case_name=case_name,
            expected_accept=True,
            fixture_path=fixture_path,
            out_dir=out_dir,
            skip_sp1=args.skip_sp1,
            cargo_bin=args.cargo_bin,
            prove=args.prove and batch_size == 1,
        )
        results.append(result)
        print(
            f"{case_name}: python_accept={result['python']['accepted']} "
            f"sp1_accept={None if result['sp1'] is None else result['sp1']['accepted']} "
            f"passed={result['passed']}"
        )

    negative_base = load_json(fixtures_dir / "mountaincar_forward_td_mlp_batch_size_1.json")
    for case_name, mutator in [
        ("tamper_selected_target_value", mutate_selected_target_value),
        ("tamper_argmax", mutate_argmax),
    ]:
        tv = copy.deepcopy(negative_base)
        mutator(tv)
        fixture_path = fixtures_dir / f"{case_name}.json"
        write_json(fixture_path, tv)
        result = evaluate_case(
            case_name=case_name,
            expected_accept=False,
            fixture_path=fixture_path,
            out_dir=out_dir,
            skip_sp1=args.skip_sp1,
            cargo_bin=args.cargo_bin,
            prove=False,
        )
        results.append(result)
        print(
            f"{case_name}: python_accept={result['python']['accepted']} "
            f"sp1_accept={None if result['sp1'] is None else result['sp1']['accepted']} "
            f"passed={result['passed']}"
        )

    benchmark_matrix = []
    for result in results:
        metrics = (result.get("sp1") or {}).get("metrics") or {}
        batch_size = 1
        if result["case_name"].startswith("mountaincar-forward-TD-"):
            batch_size = int(result["case_name"].split("-")[-1])
        status = "python_only" if args.skip_sp1 else (
            "accepted" if result["expected_accept"] and result["passed"] else
            "rejected" if (not result["expected_accept"] and result["passed"]) else
            "failed"
        )
        benchmark_matrix.append(
            {
                "case": result["case_name"],
                "environment": "MountainCar-v0",
                "network_spec": args.layer_sizes,
                "batch_size": batch_size,
                "status": status,
                "prove_time_sec": metrics.get("proving_time_sec"),
                "verify_time_sec": metrics.get("verification_time_sec"),
                "proof_size_bytes": metrics.get("proof_size_bytes"),
                "cycle_count": metrics.get("cycle_count"),
            }
        )

    all_python_expected = all(item["python_expected_ok"] for item in results)
    all_sp1_expected = None if args.skip_sp1 else all(item["sp1_expected_ok"] for item in results)
    python_sp1_agreement = None if args.skip_sp1 else all(item["python_sp1_agree"] for item in results)
    all_passed = all(item["passed"] for item in results)
    summary = {
        "environment": "MountainCar-v0",
        "relation": "forward_td_mlp_v1",
        "layer_sizes": args.layer_sizes,
        "data_path": data_path.relative_to(ROOT).as_posix(),
        "data_summary_path": data_summary_path.relative_to(ROOT).as_posix(),
        "leaf_hashes_path": leaf_hashes_path.relative_to(ROOT).as_posix(),
        "merkle_path": merkle_path.relative_to(ROOT).as_posix(),
        "source_fixture_path": source_path.relative_to(ROOT).as_posix(),
        "merkle_root": merkle["merkle_root"],
        "batch_sizes": batch_sizes,
        "skip_sp1": args.skip_sp1,
        "prove": args.prove,
        "case_results": results,
        "benchmark_matrix": benchmark_matrix,
        "all_python_expected": all_python_expected,
        "all_sp1_expected": all_sp1_expected,
        "python_sp1_agreement": python_sp1_agreement,
        "all_passed": all_passed,
    }

    write_json(out_dir / "summary.json", summary)
    write_csv(out_dir / "benchmark_matrix.csv", benchmark_matrix)
    write_markdown(out_dir / "summary.md", summary)

    print()
    print("data_summary_path =", data_summary_path.relative_to(ROOT).as_posix())
    print("merkle_path =", merkle_path.relative_to(ROOT).as_posix())
    print("merkle_root =", merkle["merkle_root"])
    print("summary_json_path =", (out_dir / "summary.json").relative_to(ROOT).as_posix())
    print("benchmark_matrix_csv_path =", (out_dir / "benchmark_matrix.csv").relative_to(ROOT).as_posix())
    print("summary_md_path =", (out_dir / "summary.md").relative_to(ROOT).as_posix())
    print("all_python_expected =", all_python_expected)
    print("all_sp1_expected =", all_sp1_expected)
    print("python_sp1_agreement =", python_sp1_agreement)
    print("all_passed =", all_passed)
    if not all_passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

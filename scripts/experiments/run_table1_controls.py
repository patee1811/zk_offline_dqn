"""Controls that answer the two obvious objections to the Table 1 numbers.

Offline DQN scores 9.3 on cartpole-expert-v2 -- the minimum episode length --
and a reviewer has two ways to dismiss that. Control A rules out undertraining
by sweeping train_steps over a 10x range. Controls B and C rule out a rigged
optimizer comparison by sweeping the learning rate on both sides, since tuning
only the sgd column would flatter the configuration the paper defends.

Heavy: gated behind RUN_HEAVY_BENCHMARKS, like the other runners in this
directory. Roughly 25 minutes per control on CPU at the default grids.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from zk_offline_dqn.rl_benchmarks.agents import (
    provable_learning_rate,
    train_behavior_cloning_discrete,
    train_offline_q,
)
from zk_offline_dqn.rl_benchmarks.datasets import (
    SELF_COLLECTED_DATASETS,
    load_committed_dataset,
)
from zk_offline_dqn.rl_benchmarks.evaluate import evaluate_policy
from zk_offline_dqn.rl_benchmarks.reporting import DISCRETE_BASELINES

DEFAULT_OUT_DIR = ROOT / "artifacts/reports/table1_controls"
# Multiples of 1/FP_SCALE, so every rate here is one the relation can express.
SGD_RATES = [0.001, 0.005, 0.01, 0.05, 0.1, 0.2, 0.5]
# Adam is unprovable at any rate; these bracket its library default of 3e-4.
ADAM_RATES = [3e-4, 1e-3, 3e-3, 1e-2]
STEP_GRID = [5000, 20000, 50000]


def dataset_ids() -> List[str]:
    return [spec.dataset_id for spec in SELF_COLLECTED_DATASETS.values()]


def _train(dataset, baseline: str, *, seed: int, steps: int, optimizer: str,
           learning_rate: float, sgd_learning_rate: float):
    kwargs = dict(
        train_steps=steps,
        seed=seed,
        device="cpu",
        batch_size=256,
        learning_rate=learning_rate,
        optimizer_name=optimizer,
        sgd_learning_rate=sgd_learning_rate,
    )
    if baseline == "bc":
        return train_behavior_cloning_discrete(dataset, **kwargs)
    return train_offline_q(dataset, algorithm=baseline, **kwargs)


def _score(dataset, baseline: str, *, seeds: List[int], steps: int, optimizer: str,
           learning_rate: float, sgd_learning_rate: float, eval_episodes: int) -> List[float]:
    returns = []
    for seed in seeds:
        policy = _train(dataset, baseline, seed=seed, steps=steps, optimizer=optimizer,
                        learning_rate=learning_rate, sgd_learning_rate=sgd_learning_rate)
        summary = evaluate_policy(policy, dataset, seeds=[seed], eval_episodes=eval_episodes)
        returns.append(float(summary.metrics["average_return_mean"]))
    return returns


def _emit(rows: List[Dict[str, Any]], out_path: Path, label: str) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(rows, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    try:
        shown = out_path.relative_to(ROOT).as_posix()
    except ValueError:
        shown = out_path.as_posix()
    print(f"{label} -> {shown} ({len(rows)} rows)")


def control_a(args: argparse.Namespace) -> List[Dict[str, Any]]:
    """Is offline DQN merely undertrained on expert data?"""
    rows: List[Dict[str, Any]] = []
    out_path = Path(args.out_dir) / "control_a_train_steps.json"
    for dataset_id in dataset_ids():
        dataset = load_committed_dataset(ROOT / "artifacts/datasets" / dataset_id)
        for steps in args.step_grid:
            started = time.time()
            returns = _score(dataset, "offline_dqn", seeds=args.seeds, steps=steps,
                             optimizer="adam", learning_rate=args.learning_rate,
                             sgd_learning_rate=args.sgd_learning_rate,
                             eval_episodes=args.eval_episodes)
            rows.append({
                "control": "a",
                "dataset": dataset_id,
                "baseline": "offline_dqn",
                "optimizer": "adam",
                "train_steps": steps,
                "seeds": list(args.seeds),
                "returns": returns,
                "mean_return": sum(returns) / len(returns),
                "seconds": round(time.time() - started, 1),
            })
            print(f"A {dataset_id:24} steps={steps:<7} "
                  f"mean={rows[-1]['mean_return']:8.1f}", flush=True)
            _emit(rows, out_path, "control A")
    return rows


def control_rates(args: argparse.Namespace, optimizer: str) -> List[Dict[str, Any]]:
    """Which learning rate serves this optimizer best across the sweep?"""
    rates = SGD_RATES if optimizer == "sgd" else ADAM_RATES
    if optimizer == "sgd":
        for rate in rates:
            provable_learning_rate(rate)
    suffix = "b_sgd_rates" if optimizer == "sgd" else "c_adam_rates"
    out_path = Path(args.out_dir) / f"control_{suffix}.json"
    rows: List[Dict[str, Any]] = []
    for dataset_id in dataset_ids():
        dataset = load_committed_dataset(ROOT / "artifacts/datasets" / dataset_id)
        for baseline in sorted(DISCRETE_BASELINES):
            for rate in rates:
                started = time.time()
                returns = _score(
                    dataset, baseline, seeds=args.seeds, steps=args.train_steps,
                    optimizer=optimizer,
                    learning_rate=rate if optimizer == "adam" else args.learning_rate,
                    sgd_learning_rate=rate if optimizer == "sgd" else args.sgd_learning_rate,
                    eval_episodes=args.eval_episodes,
                )
                rows.append({
                    "control": "b" if optimizer == "sgd" else "c",
                    "dataset": dataset_id,
                    "baseline": baseline,
                    "optimizer": optimizer,
                    "learning_rate": rate,
                    "train_steps": args.train_steps,
                    "seeds": list(args.seeds),
                    "returns": returns,
                    "mean_return": sum(returns) / len(returns),
                    "seconds": round(time.time() - started, 1),
                })
                print(f"{rows[-1]['control'].upper()} {dataset_id:24} {baseline:12} "
                      f"lr={rate:<7} mean={rows[-1]['mean_return']:8.1f}", flush=True)
                _emit(rows, out_path, f"control {rows[-1]['control'].upper()}")
    return rows


def summarise(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Rank rates by mean normalised score, not by raw mean or by cells won.

    CartPole spans 0..500 and LunarLander -1400..200, so a raw mean lets
    LunarLander pick the rate. Counting cells won ignores margin, which is how
    0.5 leads on wins while collapsing on cartpole-random.
    """
    cells: Dict[Any, Dict[float, float]] = {}
    for row in rows:
        cells.setdefault((row["dataset"], row["baseline"]), {})[row["learning_rate"]] = (
            row["mean_return"]
        )
    rates = sorted({row["learning_rate"] for row in rows})
    normalised: Dict[float, List[float]] = {rate: [] for rate in rates}
    wins: Dict[float, int] = {rate: 0 for rate in rates}
    for by_rate in cells.values():
        values = [by_rate.get(rate) for rate in rates]
        if any(value is None for value in values):
            continue
        low, high = min(values), max(values)
        wins[max(zip(values, rates))[1]] += 1
        for rate, value in zip(rates, values):
            normalised[rate].append(0.0 if high == low else (value - low) / (high - low))
    scores = {
        rate: sum(values) / len(values)
        for rate, values in normalised.items()
        if values
    }
    return {
        "cells": len(cells),
        "cells_won": wins,
        "mean_normalised_score": scores,
        "best_rate": max(scores, key=scores.get) if scores else None,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--controls", nargs="+", default=["a", "b", "c"],
                        choices=["a", "b", "c"])
    parser.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2])
    parser.add_argument("--train-steps", type=int, default=5000)
    parser.add_argument("--step-grid", type=int, nargs="+", default=STEP_GRID)
    parser.add_argument("--eval-episodes", type=int, default=10)
    parser.add_argument("--learning-rate", type=float, default=1e-2)
    parser.add_argument("--sgd-learning-rate", type=float, default=0.05)
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    args = parser.parse_args()

    if os.environ.get("RUN_HEAVY_BENCHMARKS") != "1":
        print("RUN_HEAVY_BENCHMARKS=1 is required; these controls train 200+ policies")
        return 0

    summaries = {}
    if "a" in args.controls:
        control_a(args)
    if "b" in args.controls:
        summaries["sgd"] = summarise(control_rates(args, "sgd"))
    if "c" in args.controls:
        summaries["adam"] = summarise(control_rates(args, "adam"))
    if summaries:
        path = Path(args.out_dir) / "rate_selection.json"
        path.write_text(json.dumps(summaries, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        for optimizer, summary in summaries.items():
            print(f"{optimizer}: best rate {summary['best_rate']} over {summary['cells']} cells")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

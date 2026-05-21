"""Run Phase 8.1 RL performance benchmarks and export paper Table 1."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from zk_offline_dqn.rl_benchmarks.agents import (
    train_behavior_cloning_continuous,
    train_behavior_cloning_discrete,
    train_iql_lite,
    train_offline_q,
)
from zk_offline_dqn.rl_benchmarks.datasets import (
    DatasetUnavailable,
    MINARI_DATASETS,
    SELF_COLLECTED_DATASETS,
    ensure_self_collected_dataset,
    load_named_dataset,
)
from zk_offline_dqn.rl_benchmarks.evaluate import evaluate_policy
from zk_offline_dqn.rl_benchmarks.reporting import skipped_result_rows, write_table_outputs


DISCRETE_BASELINES = {"bc", "offline_dqn", "double_dqn", "cql_lite"}
CONTINUOUS_BASELINES = {"bc_continuous", "iql_lite"}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--smoke", action="store_true")
    mode.add_argument("--paper", action="store_true")
    parser.add_argument("--datasets", nargs="+")
    parser.add_argument("--baselines", nargs="+")
    parser.add_argument("--seeds", nargs="+", type=int)
    parser.add_argument("--train-steps", type=int)
    parser.add_argument("--eval-episodes", type=int)
    parser.add_argument("--dataset-root", default="artifacts/datasets")
    parser.add_argument("--out-dir", default="artifacts/reports/final_ndss")
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--max-transitions", type=int)
    parser.add_argument("--skip-missing-self-collected", action="store_true")
    parser.add_argument("--no-minari-download", action="store_true")
    return parser


def _mode_defaults(args: argparse.Namespace) -> None:
    paper = bool(args.paper)
    if args.datasets is None:
        args.datasets = (
            ["cartpole", "mountaincar", "minari-pointmaze-umaze"]
            if paper
            else ["cartpole", "mountaincar"]
        )
    if args.baselines is None:
        args.baselines = [
            "bc",
            "offline_dqn",
            "double_dqn",
            "cql_lite",
            "bc_continuous",
            "iql_lite",
        ]
    if args.seeds is None:
        args.seeds = [0, 1, 2] if paper else [0]
    if args.train_steps is None:
        args.train_steps = 5000 if paper else 100
    if args.eval_episodes is None:
        args.eval_episodes = 10 if paper else 3
    if args.max_transitions is None:
        args.max_transitions = 10000 if paper else 1000


def _compatible_baselines(action_kind: str, baselines: Iterable[str]) -> List[str]:
    allowed = DISCRETE_BASELINES if action_kind == "discrete" else CONTINUOUS_BASELINES
    return [baseline for baseline in baselines if baseline in allowed]


def _expected_baselines(dataset_name: str, baselines: Iterable[str]) -> List[str]:
    expected = CONTINUOUS_BASELINES if dataset_name in MINARI_DATASETS else DISCRETE_BASELINES
    return [baseline for baseline in baselines if baseline in expected]


def _train_policy(dataset, baseline: str, seed: int, args: argparse.Namespace):
    if baseline == "bc":
        return train_behavior_cloning_discrete(
            dataset, train_steps=args.train_steps, seed=seed, device=args.device
        )
    if baseline in {"offline_dqn", "double_dqn", "cql_lite"}:
        return train_offline_q(
            dataset,
            algorithm=baseline,
            train_steps=args.train_steps,
            seed=seed,
            device=args.device,
        )
    if baseline == "bc_continuous":
        return train_behavior_cloning_continuous(
            dataset, train_steps=args.train_steps, seed=seed, device=args.device
        )
    if baseline == "iql_lite":
        return train_iql_lite(dataset, train_steps=args.train_steps, seed=seed, device=args.device)
    raise ValueError(f"unsupported baseline {baseline}")


def _mean_std(values: List[float | None]) -> tuple[float | None, float | None]:
    numeric = [float(value) for value in values if value is not None]
    if not numeric:
        return None, None
    mean = sum(numeric) / len(numeric)
    variance = sum((value - mean) ** 2 for value in numeric) / len(numeric)
    return mean, variance**0.5


def _aggregate_seed_metrics(
    *,
    dataset,
    baseline: str,
    seed_metrics: List[Dict[str, Any]],
    train_steps: int,
    eval_episodes: int,
) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "dataset": dataset.name,
        "dataset_source_type": dataset.source_type,
        "baseline": baseline,
        "status": "completed",
        "num_seeds": len(seed_metrics),
        "num_eval_episodes": int(eval_episodes),
        "train_steps": int(train_steps),
        "dataset_num_transitions": dataset.size,
        "success_definition": next(
            (metric.get("success_definition") for metric in seed_metrics if metric.get("success_definition")),
            None,
        ),
    }
    for metric in [
        "average_return_mean",
        "normalized_score_mean",
        "success_rate_mean",
    ]:
        mean_value, std_value = _mean_std([seed_metric.get(metric) for seed_metric in seed_metrics])
        result[metric] = mean_value
        result[metric.replace("_mean", "_std")] = std_value
    return result


def _write_phase_outputs(
    results: List[Dict[str, Any]],
    config: Dict[str, Any],
    status: Dict[str, Any],
) -> None:
    phase_dir = ROOT / "artifacts/reports/phase8_1_rl_benchmark"
    phase_dir.mkdir(parents=True, exist_ok=True)
    (phase_dir / "config.json").write_text(
        json.dumps(config, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (phase_dir / "status.json").write_text(
        json.dumps(status, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    with (phase_dir / "results.jsonl").open("w", encoding="utf-8", newline="\n") as handle:
        for result in results:
            handle.write(json.dumps(result, sort_keys=True))
            handle.write("\n")


def run_benchmark(args: argparse.Namespace) -> Dict[str, Any]:
    _mode_defaults(args)
    dataset_root = ROOT / args.dataset_root if not Path(args.dataset_root).is_absolute() else Path(args.dataset_root)
    out_dir = ROOT / args.out_dir if not Path(args.out_dir).is_absolute() else Path(args.out_dir)
    results: List[Dict[str, Any]] = []
    raw_runs: List[Dict[str, Any]] = []

    for dataset_name in args.datasets:
        if dataset_name in SELF_COLLECTED_DATASETS and not args.skip_missing_self_collected:
            ensure_self_collected_dataset(
                dataset_name,
                dataset_root,
                target_transitions=args.max_transitions,
                base_seed=12345 if dataset_name == "cartpole" else 22345,
            )
        try:
            dataset = load_named_dataset(
                dataset_name,
                dataset_root,
                max_transitions=args.max_transitions,
                allow_minari_download=not args.no_minari_download,
            )
        except DatasetUnavailable as exc:
            source = (
                "audited_self_collected"
                if dataset_name in SELF_COLLECTED_DATASETS
                else "public_source_integrity"
            )
            skipped = skipped_result_rows(
                dataset_name,
                _expected_baselines(dataset_name, args.baselines),
                source_type=source,
                reason=str(exc),
            )
            results.extend(skipped)
            raw_runs.extend(skipped)
            continue

        compatible = _compatible_baselines(dataset.action_kind, args.baselines)
        for baseline in compatible:
            seed_metrics: List[Dict[str, Any]] = []
            failure = None
            for seed in args.seeds:
                try:
                    policy = _train_policy(dataset, baseline, seed, args)
                    summary = evaluate_policy(
                        policy,
                        dataset,
                        seeds=[seed],
                        eval_episodes=args.eval_episodes,
                    )
                    seed_metric = dict(summary.metrics)
                    seed_metric["seed"] = seed
                    seed_metrics.append(seed_metric)
                    raw_runs.append(
                        {
                            "dataset": dataset.name,
                            "baseline": baseline,
                            "seed": seed,
                            "metrics": seed_metric,
                            "returns": summary.returns,
                            "successes": summary.successes,
                            "status": "completed",
                        }
                    )
                except Exception as exc:
                    failure = str(exc)
                    raw_runs.append(
                        {
                            "dataset": dataset.name,
                            "baseline": baseline,
                            "seed": seed,
                            "status": "failed",
                            "reason": failure,
                        }
                    )
                    break
            if failure is not None:
                failed = skipped_result_rows(
                    dataset.name,
                    [baseline],
                    source_type=dataset.source_type,
                    reason=failure,
                )[0]
                failed["status"] = "failed"
                failed["train_steps"] = int(args.train_steps)
                failed["dataset_num_transitions"] = dataset.size
                results.append(failed)
            else:
                results.append(
                    _aggregate_seed_metrics(
                        dataset=dataset,
                        baseline=baseline,
                        seed_metrics=seed_metrics,
                        train_steps=args.train_steps,
                        eval_episodes=args.eval_episodes,
                    )
                )

    status = {
        "phase": "8.1",
        "scope": "RL performance only",
        "mode": "paper" if args.paper else "smoke",
        "datasets": args.datasets,
        "baselines": args.baselines,
        "completed_rows": sum(result["status"] == "completed" for result in results),
        "skipped_rows": sum(result["status"] == "skipped" for result in results),
        "failed_rows": sum(result["status"] == "failed" for result in results),
        "raw_run_count": len(raw_runs),
    }
    config = {
        "datasets": args.datasets,
        "baselines": args.baselines,
        "seeds": args.seeds,
        "train_steps": args.train_steps,
        "eval_episodes": args.eval_episodes,
        "dataset_root": dataset_root.as_posix(),
        "out_dir": out_dir.as_posix(),
        "max_transitions": args.max_transitions,
        "device": args.device,
    }
    write_table_outputs(results, out_dir, status=status)
    _write_phase_outputs(raw_runs + results, config, status)
    return status


def main() -> int:
    args = build_parser().parse_args()
    status = run_benchmark(args)
    print("phase8_1_rl_benchmark = completed")
    print(json.dumps(status, indent=2, sort_keys=True))
    return 0 if status["failed_rows"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

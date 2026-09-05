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
    PROVED_SGD_LEARNING_RATE,
    train_behavior_cloning_continuous,
    train_behavior_cloning_discrete,
    train_iql_lite,
    train_offline_q,
)
from zk_offline_dqn.rl_benchmarks.datasets import (
    DatasetUnavailable,
    MINARI_DATASETS,
    SELF_COLLECTED_DATASETS,
    dataset_family_for_name,
    ensure_self_collected_dataset,
    extract_phase2_datasets_from_tarball,
    load_named_dataset,
    public_dataset_id,
    public_family_for_dataset_id,
    regenerate_public_phase2_dataset,
    validate_phase2_dataset,
)
from zk_offline_dqn.rl_benchmarks.evaluate import evaluate_policy
from zk_offline_dqn.rl_benchmarks.reporting import (
    CONTINUOUS_BASELINES,
    DISCRETE_BASELINES,
    skipped_result_rows,
    write_table_outputs,
)


DEFAULT_PUBLIC_SIZES = [10000, 50000, 100000]
PUBLIC_FAMILY_ALIASES = {
    "umaze": "minari-pointmaze-umaze",
    "umaze-dense": "minari-pointmaze-umaze-dense",
    "medium": "minari-pointmaze-medium",
    "open": "minari-pointmaze-open",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--smoke", action="store_true")
    mode.add_argument("--paper", action="store_true")
    parser.add_argument("--datasets", nargs="+")
    parser.add_argument("--baselines", nargs="+")
    parser.add_argument("--optimizers", nargs="+", choices=["adam", "sgd"])
    parser.add_argument("--sgd-learning-rate", type=float, default=PROVED_SGD_LEARNING_RATE)
    parser.add_argument("--learning-rate", type=float)
    parser.add_argument("--seeds", nargs="+", type=int)
    parser.add_argument("--train-steps", type=int)
    parser.add_argument("--eval-episodes", type=int)
    parser.add_argument("--dataset-root", default="artifacts/datasets")
    parser.add_argument("--out-dir", default="artifacts/reports/final_ndss")
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--batch-size", type=int)
    parser.add_argument("--max-transitions", type=int)
    parser.add_argument("--phase2-artifact-root", default="artifacts")
    parser.add_argument("--phase2-tarball", action="append")
    parser.add_argument(
        "--reuse-phase2-datasets",
        action=argparse.BooleanOptionalAction,
        default=None,
    )
    parser.add_argument(
        "--regenerate-missing-phase2-datasets",
        action=argparse.BooleanOptionalAction,
        default=None,
    )
    parser.add_argument("--public-sizes", nargs="+", type=int)
    parser.add_argument("--public-families", nargs="+")
    parser.add_argument("--fail-if-public-missing", action="store_true")
    parser.add_argument("--skip-missing-self-collected", action="store_true")
    return parser


def _mode_defaults(args: argparse.Namespace) -> None:
    paper = bool(args.paper)
    if args.datasets is None:
        # PointMaze is gone from the default sweep: it is continuous-action, so
        # the four DQN-family baselines -- the ones this paper actually proves a
        # relation for -- skipped 24 of its 36 rows, and the 12 that ran used
        # algorithms outside that relation. The public datasets still back the
        # merkle_membership scaling rows in Table 2.
        args.datasets = (
            [
                "cartpole-random",
                "cartpole-medium",
                "cartpole-expert",
                "lunarlander-random",
                "lunarlander-medium",
                "lunarlander-expert",
            ]
            if paper
            else ["cartpole-random", "cartpole-expert"]
        )
    if args.baselines is None:
        args.baselines = ["bc", "offline_dqn", "double_dqn", "cql_lite"]
    if args.learning_rate is None:
        # Both columns get a tuned rate or the comparison is rigged: 3e-4 is a
        # library default, and sweeping only the sgd side would flatter it.
        args.learning_rate = 1e-2 if paper else 3e-4
    if args.optimizers is None:
        # The zk relation verifies plain SGD, so an Adam-only table does not
        # report what the proof system actually checks.
        args.optimizers = ["adam", "sgd"] if paper else ["adam"]
    if args.seeds is None:
        args.seeds = [0, 1, 2] if paper else [0]
    if args.train_steps is None:
        args.train_steps = 5000 if paper else 100
    if args.eval_episodes is None:
        args.eval_episodes = 10 if paper else 3
    if args.batch_size is None:
        args.batch_size = 256 if paper else 64
    if args.max_transitions is None and not paper:
        args.max_transitions = 1000
    if args.public_sizes is None:
        args.public_sizes = list(DEFAULT_PUBLIC_SIZES if paper else [10000])
    if args.public_families is None:
        args.public_families = [name for name in args.datasets if name in MINARI_DATASETS]
    args.public_families = [_normalize_public_family(name) for name in args.public_families]
    if args.reuse_phase2_datasets is None:
        args.reuse_phase2_datasets = paper
    if args.regenerate_missing_phase2_datasets is None:
        args.regenerate_missing_phase2_datasets = paper


def _resolve(path: str | Path) -> Path:
    path = Path(path)
    return path if path.is_absolute() else ROOT / path


def _dedupe(values: Iterable[str]) -> List[str]:
    result: List[str] = []
    for value in values:
        if value not in result:
            result.append(value)
    return result


def _normalize_public_family(value: str) -> str:
    return PUBLIC_FAMILY_ALIASES.get(value, value)


def expand_dataset_requests(args: argparse.Namespace) -> List[str]:
    expanded: List[str] = []
    for dataset_name in args.datasets:
        if dataset_name in MINARI_DATASETS:
            if args.public_families and dataset_name not in args.public_families:
                continue
            expanded.extend(public_dataset_id(dataset_name, size) for size in args.public_sizes)
        else:
            expanded.append(dataset_name)
    for family in args.public_families:
        if family not in MINARI_DATASETS:
            raise ValueError(f"unsupported --public-families value: {family}")
        expanded.extend(public_dataset_id(family, size) for size in args.public_sizes)
    return _dedupe(expanded)


def _dataset_dir_id(dataset_name: str) -> str:
    if dataset_name in SELF_COLLECTED_DATASETS:
        return SELF_COLLECTED_DATASETS[dataset_name][0]
    return dataset_name


def _phase2_tarballs(args: argparse.Namespace, artifact_root: Path) -> List[Path]:
    if args.phase2_tarball:
        return [_resolve(value) for value in args.phase2_tarball]
    return [
        artifact_root / "kaggle_phase2_outputs/phase2_dataset_outputs.tar.gz",
        artifact_root / "kaggle_phase2_scale_outputs/phase2_dataset_scale_outputs_full.tar.gz",
    ]


def _prepare_phase2_datasets(
    args: argparse.Namespace,
    dataset_names: List[str],
    dataset_root: Path,
    artifact_root: Path,
) -> Dict[str, Any]:
    provenance: Dict[str, str] = {}
    reasons: Dict[str, List[str]] = {}
    wanted_ids = [_dataset_dir_id(name) for name in dataset_names]
    unresolved: List[str] = []
    for dataset_id in wanted_ids:
        ok, errors = validate_phase2_dataset(dataset_root / dataset_id)
        if ok:
            provenance[dataset_id] = "reused_existing_artifact"
        else:
            unresolved.append(dataset_id)
            if errors:
                reasons[dataset_id] = errors

    extracted_from: Dict[str, str] = {}
    if unresolved and args.reuse_phase2_datasets:
        for tarball in _phase2_tarballs(args, artifact_root):
            for dataset_id in extract_phase2_datasets_from_tarball(tarball, dataset_root, unresolved):
                ok, errors = validate_phase2_dataset(dataset_root / dataset_id)
                if ok:
                    provenance[dataset_id] = "extracted_from_phase2_tarball"
                    extracted_from[dataset_id] = tarball.as_posix()
                elif errors:
                    reasons[dataset_id] = errors
            unresolved = [dataset_id for dataset_id in unresolved if dataset_id not in provenance]

    regenerated: List[str] = []
    if unresolved and args.regenerate_missing_phase2_datasets:
        for dataset_id in list(unresolved):
            source_name = next(
                (name for name in dataset_names if _dataset_dir_id(name) == dataset_id),
                dataset_id,
            )
            try:
                if source_name in SELF_COLLECTED_DATASETS and not args.skip_missing_self_collected:
                    ensure_self_collected_dataset(source_name, dataset_root)
                elif public_family_for_dataset_id(dataset_id) is not None:
                    regenerate_public_phase2_dataset(dataset_id, dataset_root)
                else:
                    continue
                ok, errors = validate_phase2_dataset(dataset_root / dataset_id)
                if not ok:
                    reasons[dataset_id] = errors
                    continue
                provenance[dataset_id] = "regenerated_with_phase2_pipeline"
                regenerated.append(dataset_id)
            except Exception as exc:
                reasons[dataset_id] = [str(exc)]
        unresolved = [dataset_id for dataset_id in unresolved if dataset_id not in provenance]

    return {
        "provenance": provenance,
        "unresolved": unresolved,
        "reasons": reasons,
        "tarballs": [path.as_posix() for path in _phase2_tarballs(args, artifact_root)],
        "extracted_from": extracted_from,
        "regenerated": regenerated,
    }


def _dataset_transition_limit(args: argparse.Namespace, dataset_name: str) -> int | None:
    """How many transitions to load, or None for the whole committed dataset.

    Paper mode used to cap self-collected datasets at 10000. OfflineDataset.subset
    keeps the *first* N rows, so an expert row cited the merkle_root of a 50k
    dataset while training on its first 23 episodes, and reported 10000 in the
    Transitions column. The datasets are collected at a deliberate size; paper
    mode now uses all of it, and only an explicit --max-transitions truncates.
    """
    if args.max_transitions is not None:
        return int(args.max_transitions)
    return None


def _compatible(action_kind: str, baseline: str) -> bool:
    allowed = DISCRETE_BASELINES if action_kind == "discrete" else CONTINUOUS_BASELINES
    return baseline in allowed


def _expected_baselines(dataset_name: str, baselines: Iterable[str]) -> List[str]:
    expected = (
        CONTINUOUS_BASELINES
        if public_family_for_dataset_id(dataset_name) is not None or dataset_name in MINARI_DATASETS
        else DISCRETE_BASELINES
    )
    return [baseline for baseline in baselines if baseline in expected]


def _optimizers_for(baseline: str, args: argparse.Namespace) -> List[str]:
    """Only the discrete baselines carry the optimizer axis.

    The continuous ones take no optimizer_name, so running them twice would
    report the same Adam numbers under two labels.
    """
    if baseline in DISCRETE_BASELINES:
        return list(args.optimizers)
    return ["adam"]


def _train_policy(dataset, baseline: str, seed: int, args: argparse.Namespace, optimizer: str):
    kwargs = {
        "train_steps": args.train_steps,
        "seed": seed,
        "device": args.device,
        "batch_size": args.batch_size,
        "learning_rate": args.learning_rate,
    }
    if baseline == "bc":
        return train_behavior_cloning_discrete(
            dataset,
            optimizer_name=optimizer,
            sgd_learning_rate=args.sgd_learning_rate,
            **kwargs,
        )
    if baseline in {"offline_dqn", "double_dqn", "cql_lite"}:
        return train_offline_q(
            dataset,
            algorithm=baseline,
            optimizer_name=optimizer,
            sgd_learning_rate=args.sgd_learning_rate,
            **kwargs,
        )
    # The continuous baselines carry no optimizer axis: they are outside the
    # relation this paper proves, and only reachable through --baselines.
    if baseline == "bc_continuous":
        return train_behavior_cloning_continuous(dataset, **kwargs)
    if baseline == "iql_lite":
        return train_iql_lite(dataset, **kwargs)
    raise ValueError(f"unsupported baseline {baseline}")


def _mean_std(values: List[float | None]) -> tuple[float | None, float | None]:
    numeric = [float(value) for value in values if value is not None]
    if not numeric:
        return None, None
    mean = sum(numeric) / len(numeric)
    variance = sum((value - mean) ** 2 for value in numeric) / len(numeric)
    return mean, variance**0.5


def _dataset_result_fields(dataset) -> Dict[str, Any]:
    return {
        "dataset_id": dataset.name,
        "dataset_family": dataset.metadata.get("dataset_family", dataset_family_for_name(dataset.name)),
        "dataset_source_type": dataset.source_type,
        "dataset_num_transitions": dataset.size,
        # Truncation used to be invisible: the row cited a committed root while
        # dataset.size reported the loaded prefix. Carrying both makes any gap
        # between them readable straight off the table.
        "dataset_committed_transitions": (dataset.metadata.get("manifest") or {}).get(
            "total_transitions"
        ),
        "phase2_dataset_provenance": dataset.metadata.get("phase2_dataset_provenance"),
        "manifest_hash": dataset.metadata.get("manifest_hash"),
        "audit_report_hash": dataset.metadata.get("audit_report_hash"),
        "dataset_root": dataset.metadata.get("dataset_root"),
        "merkle_root": dataset.metadata.get("merkle_root"),
    }


def _aggregate_seed_metrics(
    *,
    dataset,
    baseline: str,
    optimizer: str,
    seed_metrics: List[Dict[str, Any]],
    train_steps: int,
    eval_episodes: int,
    seeds: List[int],
) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "dataset": dataset.name,
        "baseline": baseline,
        "optimizer": optimizer,
        "status": "completed",
        "rollout_eval_status": "completed",
        "num_seeds": len(seed_metrics),
        "seed_list": list(seeds),
        "num_eval_episodes": int(eval_episodes),
        "train_steps": int(train_steps),
        "success_definition": next(
            (metric.get("success_definition") for metric in seed_metrics if metric.get("success_definition")),
            None,
        ),
        **_dataset_result_fields(dataset),
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


def _missing_rows(
    dataset_name: str,
    baselines: Iterable[str],
    reason: str,
) -> List[Dict[str, Any]]:
    source_type = (
        "public_source_integrity"
        if public_family_for_dataset_id(dataset_name) is not None or dataset_name in MINARI_DATASETS
        else "audited_self_collected"
    )
    rows = skipped_result_rows(
        dataset_name,
        _expected_baselines(dataset_name, baselines),
        source_type=source_type,
        reason=reason,
        dataset_family=dataset_family_for_name(dataset_name),
    )
    for row in rows:
        row["rollout_eval_status"] = "not_run"
        row["phase2_dataset_provenance"] = None
        row["seed_list"] = []
    return rows


def public_benchmark_gate_failed(
    fail_if_public_missing: bool,
    public_requested_ids: Iterable[str],
    results: Iterable[Dict[str, Any]],
) -> bool:
    completed_ids = {
        result.get("dataset")
        for result in results
        if result.get("status") == "completed"
        and result.get("dataset_source_type") == "public_source_integrity"
    }
    requested_ids = list(public_requested_ids)
    return bool(
        fail_if_public_missing
        and requested_ids
        and not any(dataset_id in completed_ids for dataset_id in requested_ids)
    )


def run_benchmark(args: argparse.Namespace) -> Dict[str, Any]:
    _mode_defaults(args)
    dataset_root = _resolve(args.dataset_root)
    out_dir = _resolve(args.out_dir)
    artifact_root = _resolve(args.phase2_artifact_root)
    dataset_names = expand_dataset_requests(args)
    phase2 = _prepare_phase2_datasets(args, dataset_names, dataset_root, artifact_root)
    results: List[Dict[str, Any]] = []
    raw_runs: List[Dict[str, Any]] = []

    for dataset_name in dataset_names:
        dataset_id = _dataset_dir_id(dataset_name)
        try:
            dataset = load_named_dataset(
                dataset_name,
                dataset_root,
                max_transitions=_dataset_transition_limit(args, dataset_name),
            )
            dataset.metadata["phase2_dataset_provenance"] = phase2["provenance"].get(
                dataset_id,
                dataset.metadata.get("phase2_dataset_provenance"),
            )
        except DatasetUnavailable as exc:
            missing = _missing_rows(dataset_name, args.baselines, str(exc))
            results.extend(missing)
            raw_runs.extend(missing)
            continue

        for baseline in args.baselines:
            if not _compatible(dataset.action_kind, baseline):
                incompatible = skipped_result_rows(
                    dataset.name,
                    [baseline],
                    source_type=dataset.source_type,
                    reason=f"{baseline} is incompatible with {dataset.action_kind} actions",
                    status="incompatible_skipped",
                    dataset_family=dataset.metadata.get("dataset_family"),
                )[0]
                incompatible.update(_dataset_result_fields(dataset))
                incompatible["rollout_eval_status"] = "not_run"
                incompatible["seed_list"] = []
                incompatible["optimizer"] = None
                results.append(incompatible)
                raw_runs.append(incompatible)
                continue

            for optimizer in _optimizers_for(baseline, args):
                seed_metrics: List[Dict[str, Any]] = []
                failure = None
                for seed in args.seeds:
                    try:
                        policy = _train_policy(dataset, baseline, seed, args, optimizer)
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
                                "optimizer": optimizer,
                                "seed": seed,
                                "metrics": seed_metric,
                                "returns": summary.returns,
                                "successes": summary.successes,
                                "status": "completed",
                                "rollout_eval_status": "completed",
                                **_dataset_result_fields(dataset),
                            }
                        )
                    except Exception as exc:
                        failure = str(exc)
                        raw_runs.append(
                            {
                                "dataset": dataset.name,
                                "baseline": baseline,
                                "optimizer": optimizer,
                                "seed": seed,
                                "status": "failed",
                                "reason": failure,
                                "rollout_eval_status": "failed",
                                **_dataset_result_fields(dataset),
                            }
                        )
                        break
                if failure is not None:
                    failed = skipped_result_rows(
                        dataset.name,
                        [baseline],
                        source_type=dataset.source_type,
                        reason=failure,
                        status="failed",
                        dataset_family=dataset.metadata.get("dataset_family"),
                    )[0]
                    failed.update(_dataset_result_fields(dataset))
                    failed["seed_list"] = list(args.seeds)
                    failed["rollout_eval_status"] = "failed"
                    failed["train_steps"] = int(args.train_steps)
                    failed["optimizer"] = optimizer
                    results.append(failed)
                else:
                    results.append(
                        _aggregate_seed_metrics(
                            dataset=dataset,
                            baseline=baseline,
                            optimizer=optimizer,
                            seed_metrics=seed_metrics,
                            train_steps=args.train_steps,
                            eval_episodes=args.eval_episodes,
                            seeds=args.seeds,
                        )
                    )

    public_requested_ids = [
        dataset_name for dataset_name in dataset_names if public_family_for_dataset_id(dataset_name) is not None
    ]
    public_completed_ids = sorted(
        {
            result["dataset"]
            for result in results
            if result.get("status") == "completed"
            and result.get("dataset_source_type") == "public_source_integrity"
        }
    )
    public_gate_failed = public_benchmark_gate_failed(
        args.fail_if_public_missing,
        public_requested_ids,
        results,
    )
    status = {
        "phase": "8.1",
        "scope": "RL performance only",
        "mode": "paper" if args.paper else "smoke",
        "datasets": dataset_names,
        "baselines": args.baselines,
        "optimizers": args.optimizers,
        "sgd_learning_rate": args.sgd_learning_rate,
        "learning_rate": args.learning_rate,
        "completed_rows": sum(result["status"] == "completed" for result in results),
        "skipped_rows": sum(result["status"] == "skipped" for result in results),
        "incompatible_skipped_rows": sum(
            result["status"] == "incompatible_skipped" for result in results
        ),
        "failed_rows": sum(result["status"] == "failed" for result in results),
        "raw_run_count": len(raw_runs),
        "required_public_dataset_ids": public_requested_ids,
        "completed_public_dataset_ids": public_completed_ids,
        "fail_if_public_missing": bool(args.fail_if_public_missing),
        "public_benchmark_gate_failed": public_gate_failed,
        "phase2_dataset_handling": phase2,
        "row_status": [
            {
                "dataset": result.get("dataset"),
                "baseline": result.get("baseline"),
                "status": result.get("status"),
                "reason": result.get("reason"),
            }
            for result in results
        ],
    }
    config = {
        "datasets": dataset_names,
        "requested_datasets": args.datasets,
        "baselines": args.baselines,
        "optimizers": args.optimizers,
        "sgd_learning_rate": args.sgd_learning_rate,
        "learning_rate": args.learning_rate,
        "seeds": args.seeds,
        "train_steps": args.train_steps,
        "eval_episodes": args.eval_episodes,
        "batch_size": args.batch_size,
        "dataset_root": dataset_root.as_posix(),
        "out_dir": out_dir.as_posix(),
        "max_transitions": args.max_transitions,
        "device": args.device,
        "phase2_artifact_root": artifact_root.as_posix(),
        "phase2_tarballs": phase2["tarballs"],
        "reuse_phase2_datasets": bool(args.reuse_phase2_datasets),
        "regenerate_missing_phase2_datasets": bool(args.regenerate_missing_phase2_datasets),
        "public_sizes": args.public_sizes,
        "public_families": args.public_families,
        "observation_flatten_order": ["observation", "achieved_goal", "desired_goal", "remaining keys sorted"],
    }
    write_table_outputs(results, out_dir, status=status)
    _write_phase_outputs(raw_runs + results, config, status)
    return status


def main() -> int:
    args = build_parser().parse_args()
    status = run_benchmark(args)
    print("phase8_1_rl_benchmark = completed")
    print(json.dumps(status, indent=2, sort_keys=True))
    failed = status["failed_rows"] > 0 or status["public_benchmark_gate_failed"]
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Emit the paper's tables, and the ranges its prose quotes, from the committed artifacts.

The report pipeline already writes a LaTeX dump of each table, but those are raw
column-for-column exports: ten columns at full float precision, which will not
fit an IEEE two-column page. So the paper carried its own hand-typed copies, and
they drifted -- by the time anyone checked, the paper reported 440.6 s for a
fragment that now proves in 3.8 s, listed MountainCar as a benchmark
environment, and quoted a Table 1 built from a different experiment entirely.

These emitters produce LaTeX the paper can \\input directly, so a number reaches
the paper only by being measured. tests/unit/test_paper_tables_match_artifacts.py
regenerates them and fails on any difference, which catches both a stale
checkout and a hand edit.
"""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from typing import Any, Dict, Iterable, List

from zk_offline_dqn.backends.sp1.metrics import LEAF_CYCLE_SUMMARY_KEY

ROOT = Path(__file__).resolve().parents[2]
FINAL = ROOT / "artifacts/reports/final_ndss"
GENERATED = ROOT / "paper/generated"
PROVENANCE = ROOT / "artifacts/reports/provenance"

# The two tree families the results section compares, with the target-sync
# interval each was proved at. The interval is checked against the leaves' own
# public inputs, so the label in the sentence cannot come loose from the data.
LEAF_RANGE_TREES = [
    ("SyncFour", "sp1_t1248_lunarlander", 4),
    ("SyncTwoThousand", "sp1_t4992_lunarlander_random", 2000),
]
NUMBER_WORDS = {8: "eight", 16: "sixteen", 32: "thirty-two", 64: "sixty-four"}

# Dataset groups in the order the paper walks them: three quality levels per
# environment, easiest data first.
DATASET_ORDER = [
    "cartpole-random-v2",
    "cartpole-medium-v2",
    "cartpole-expert-v2",
    "lunarlander-random-v1",
    "lunarlander-medium-v1",
    "lunarlander-expert-v1",
]
ALGORITHM_LABELS = [
    ("bc", "BC"),
    ("offline_dqn", "Offline DQN"),
    ("double_dqn", "Double DQN"),
    ("cql_lite", "CQL-lite"),
]
PROVABLE_BASELINE = "double_dqn_provable"

# Readable names for the proof-cost rows, in the order the paper presents them:
# core relations, then the two dataset-bound fragments, then merkle scaling,
# then aggregation, then the whole-run roots.
RELATION_LABELS = [
    ("td_mvp", r"TD MVP"),
    ("merkle_membership", r"Merkle (canonical)"),
    ("forward_td_mlp", r"Fwd-TD MLP"),
    ("one_step_sgd_tiny", r"One-step SGD tiny"),
    ("short_trace", r"Short trace"),
    ("training_update_batch1", r"Training update"),
    ("training_fragment_k1", r"Fragment $k\!=\!1$"),
    ("training_fragment_k4", r"Fragment $k\!=\!4$"),
    ("training_fragment_k8", r"Fragment $k\!=\!8$"),
    ("training_fragment_cartpole_expert_k1", r"Fragment, CartPole data"),
    ("training_fragment_lunarlander_expert_k1", r"Fragment, LunarLander data"),
    ("merkle_membership_dataset_1000", r"Merkle (1k leaves)"),
    ("merkle_membership_dataset_10000", r"Merkle (10k leaves)"),
    ("merkle_membership_dataset_50000", r"Merkle (50k leaves)"),
    ("merkle_membership_dataset_100000", r"Merkle (100k leaves)"),
    ("training_aggregation_manifest_t32", r"Agg.\ chain $T\!=\!32$"),
    ("training_aggregation_manifest_t64", r"Agg.\ chain $T\!=\!64$"),
    ("training_aggregation_manifest_t128", r"Agg.\ chain $T\!=\!128$"),
    ("native_flat_recursive_t16", r"Recursive $T\!=\!16$"),
    ("native_flat_recursive_t32", r"Recursive $T\!=\!32$"),
    ("native_flat_recursive_t64", r"Recursive $T\!=\!64$"),
    ("binary_tree_native_t16", r"Binary tree $T\!=\!16$"),
    ("groth16_recursive_t16", r"Groth16 child $T\!=\!16$"),
    ("binary_tree_native_t1248_cartpole", r"Whole run, CartPole"),
    ("binary_tree_native_t1248_lunarlander", r"Whole run, LunarLander"),
    ("binary_tree_native_t4992_lunarlander_random", r"Whole run, LunarLander-random"),
]


def _read_csv(path: Path) -> List[Dict[str, str]]:
    with path.open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _num(value: str) -> float | None:
    """Table 1 stores 'mean +/- std'; take the mean."""
    if not value:
        return None
    return float(str(value).split()[0])


def tex_number(value: float | None, places: int = 1) -> str:
    """LaTeX renders a leading hyphen as a hyphen, not a minus sign."""
    if value is None:
        return "---"
    text = f"{abs(value):.{places}f}"
    return f"$-${text}" if value < 0 else text


def tex_thousands(value: float | None) -> str:
    if value is None:
        return "---"
    text = f"{int(round(value)):,}"
    return text.replace(",", "{,}")


def table1_rows() -> List[Dict[str, Any]]:
    rows = _read_csv(FINAL / "table1_rl_performance.csv")
    index: Dict[tuple, Dict[str, str]] = {}
    for row in rows:
        index[(row["Dataset"], row["Baseline"], row["Optimizer"])] = row
    out: List[Dict[str, Any]] = []
    for dataset in DATASET_ORDER:
        for baseline, label in ALGORITHM_LABELS:
            adam = index.get((dataset, baseline, "adam"))
            sgd = index.get((dataset, baseline, "sgd"))
            out.append(
                {
                    "dataset": dataset,
                    "algorithm": label,
                    "adam": _num(adam["Avg Return"]) if adam else None,
                    "sgd": _num(sgd["Avg Return"]) if sgd else None,
                }
            )
        provable = index.get((dataset, PROVABLE_BASELINE, "sgd"))
        out.append(
            {
                "dataset": dataset,
                "algorithm": r"\emph{Provable config.}",
                "adam": None,
                "sgd": _num(provable["Avg Return"]) if provable else None,
            }
        )
    return out


def render_table1(rows: Iterable[Dict[str, Any]]) -> str:
    lines = [
        r"% Generated by zk_offline_dqn.experiments.paper_tables -- do not edit.",
        r"\begin{table}[!t]",
        r"\centering",
        r"\small",
        r"\caption{RL performance on the six committed self-collected datasets,",
        r"three seeds each. \emph{Provable config.} is the configuration the SP1",
        r"relation checks: batch size 1, plain SGD, component-wise gradient",
        r"clipping. Adam is reported at its tuned rate and is not expressible in",
        r"the relation at any rate, since $3\times10^{-4}$ encodes to zero at",
        r"$\mathrm{FP\_SCALE}=1000$.}",
        r"\label{tab:rl-performance}",
        r"\renewcommand{\arraystretch}{1.1}",
        r"\begin{tabular}{llrr}",
        r"\toprule",
        r"\textbf{Dataset} & \textbf{Algorithm} &"
        r" \textbf{Adam} & \textbf{SGD} \\",
        r"\midrule",
    ]
    current = None
    for row in rows:
        if row["dataset"] != current:
            if current is not None:
                lines.append(r"\midrule")
            current = row["dataset"]
        lines.append(
            f"{row['dataset']} & {row['algorithm']} & "
            f"{tex_number(row['adam'])} & {tex_number(row['sgd'])} " + r"\\"
        )
    lines.extend([r"\bottomrule", r"\end{tabular}", r"\end{table}", ""])
    return "\n".join(lines)


def table2_rows() -> List[Dict[str, Any]]:
    rows = {r["Case ID"]: r for r in _read_csv(FINAL / "table2_zk_proof_cost.csv")}
    out: List[Dict[str, Any]] = []
    for case_id, label in RELATION_LABELS:
        row = rows.get(case_id)
        if row is None or row["Status"] != "proof_verified":
            continue
        out.append(
            {
                "label": label,
                "prove": float(row["Prove Time (s)"]) if row["Prove Time (s)"] else None,
                "verify": float(row["Verify Time (s)"]) if row["Verify Time (s)"] else None,
                "size_kb": (int(row["Proof Size (bytes)"]) / 1024) if row["Proof Size (bytes)"] else None,
                "kcycles": (int(row["Cycle Count"]) / 1000) if row["Cycle Count"] else None,
                "prover": row["Prover"] or "---",
            }
        )
    return out


def render_table2(rows: Iterable[Dict[str, Any]]) -> str:
    lines = [
        r"% Generated by zk_offline_dqn.experiments.paper_tables -- do not edit.",
        r"\begin{table}[!t]",
        r"\centering",
        r"\footnotesize",
        r"\caption{SP1 proof cost for every proof-verified relation",
        r"configuration. Times in seconds, proof size in KB, cycles in",
        r"thousands. Every row was produced on a g5.2xlarge (NVIDIA A10G) under",
        r"the CUDA prover, and each row's provenance record names the prover that",
        r"produced it.}",
        r"\label{tab:proof-cost}",
        r"\renewcommand{\arraystretch}{1.1}",
        r"\setlength{\tabcolsep}{3pt}",
        r"\begin{tabular}{@{}lrrrr@{}}",
        r"\toprule",
        r"\textbf{Relation} & \textbf{Prove} & \textbf{Verify} &"
        r" \textbf{Size} & \textbf{Cycles} \\",
        r"\midrule",
    ]
    for row in rows:
        lines.append(
            f"{row['label']} & {tex_number(row['prove'], 1)} & "
            f"{tex_number(row['verify'], 3)} & {tex_thousands(row['size_kb'])} & "
            f"{tex_thousands(row['kcycles'])} " + r"\\"
        )
    lines.extend([r"\bottomrule", r"\end{tabular}", r"\end{table}", ""])
    return "\n".join(lines)


def table3_rows() -> List[Dict[str, Any]]:
    """One row per tamper category, in descending order of test count."""
    rows = _read_csv(FINAL / "table3_tamper_rejection.csv")
    grouped: Dict[str, Dict[str, Any]] = {}
    for row in rows:
        key = row.get("Tamper Category") or row.get("Category") or "unknown"
        bucket = grouped.setdefault(
            key, {"category": key, "components": set(), "tests": 0, "rejected": 0,
                  "not_applicable": 0}
        )
        bucket["components"].add(row.get("Component") or row.get("Relation") or key)
        bucket["tests"] += 1
        if row["Status"] == "rejected_as_expected":
            bucket["rejected"] += 1
        elif row["Status"] == "not_applicable":
            bucket["not_applicable"] += 1
    out = []
    for bucket in grouped.values():
        bucket["components"] = len(bucket["components"])
        out.append(bucket)
    out.sort(key=lambda b: (-b["tests"], b["category"]))
    return out


def render_table3(rows: Iterable[Dict[str, Any]]) -> str:
    rows = list(rows)
    total_tests = sum(r["tests"] for r in rows)
    total_rejected = sum(r["rejected"] for r in rows)
    total_na = sum(r["not_applicable"] for r in rows)
    lines = [
        r"% Generated by zk_offline_dqn.experiments.paper_tables -- do not edit.",
        r"\begin{table}[!t]",
        r"\centering",
        r"\footnotesize",
        r"\caption{Tamper rejection by category. Every adversarial modification",
        r"is rejected; rows marked not applicable are configurations where the",
        r"modification has no meaning, not failures.}",
        r"\label{tab:tamper-summary}",
        r"\renewcommand{\arraystretch}{1.1}",
        r"\begin{tabular}{@{}lrrr@{}}",
        r"\toprule",
        r"\textbf{Tamper category} & \textbf{Comp.} & \textbf{Tests} &"
        r" \textbf{Rejected} \\",
        r"\midrule",
    ]
    for row in rows:
        label = row["category"].replace("_", r"\_")
        applicable = row["tests"] - row["not_applicable"]
        cell = f"{row['rejected']}/{applicable}"
        if row["not_applicable"]:
            cell += f" ({row['not_applicable']} n/a)"
        lines.append(
            f"{label} & {row['components']} & {row['tests']} & {cell} " + r"\\"
        )
    applicable_total = total_tests - total_na
    lines.extend([
        r"\midrule",
        r"\textbf{Total} & --- & \textbf{" + str(total_tests) + r"} & \textbf{"
        + f"{total_rejected}/{applicable_total}" + r"} \\",
        r"\bottomrule",
        r"\end{tabular}",
        r"\end{table}",
        "",
    ])
    return "\n".join(lines)


def leaf_cycle_summaries() -> Dict[str, Dict[str, Any]]:
    """Each compared tree's leaf_cycle_summary, as its generator recorded it."""
    out: Dict[str, Dict[str, Any]] = {}
    for name, tree, interval in LEAF_RANGE_TREES:
        paths = sorted(
            (PROVENANCE / tree).glob("_binary_native_work/t*/binary_child_proof_status.json")
        )
        if len(paths) != 1:
            raise ValueError(f"{tree}: expected one tree status file, found {len(paths)}")
        summary = json.loads(paths[0].read_text(encoding="utf-8")).get(LEAF_CYCLE_SUMMARY_KEY)
        if summary is None:
            raise ValueError(
                f"{tree} has no {LEAF_CYCLE_SUMMARY_KEY}; regenerate the tree, or write it "
                "from the committed leaves with backends.sp1.metrics.leaf_cycle_summary"
            )
        if summary["target_sync_interval"] != interval:
            raise ValueError(
                f"{tree} was proved at interval {summary['target_sync_interval']}, "
                f"but the paper labels it {interval}"
            )
        out[name] = summary
    return out


def render_leaf_cycle_macros(summaries: Dict[str, Dict[str, Any]]) -> str:
    """Macros for the leaf-cycle comparison in the results section.

    The spread is stated as a strict upper bound one decimal place above the
    measured value, which is how the sentence reads ("differ by under ...").
    """
    steps = {summary["num_steps"] for summary in summaries.values()}
    if len(steps) != 1:
        raise ValueError(f"compared trees differ in leaf size: {sorted(steps)}")
    low = min(summary["cycle_count_min"] for summary in summaries.values())
    high = max(summary["cycle_count_max"] for summary in summaries.values())
    bound = math.floor(1000 * (high - low) / low) / 10 + 0.1

    lines = [
        "% Generated by zk_offline_dqn.experiments.paper_tables from each tree's",
        f"% {LEAF_CYCLE_SUMMARY_KEY} in artifacts/reports/provenance/. Do not edit by hand.",
    ]
    for name, summary in summaries.items():
        span = "${:.1f}$--${:.1f}$".format(
            summary["cycle_count_min"] / 1e6, summary["cycle_count_max"] / 1e6
        )
        count = summary["leaf_count"]
        lines.append(r"\newcommand{\leafRange" + name + "}{" + span + r"\,M}")
        lines.append(
            r"\newcommand{\leafCount" + name + "}{" + NUMBER_WORDS.get(count, f"${count}$") + "}"
        )
    lines.append(r"\newcommand{\leafSpreadBound}{$" + f"{bound:.1f}" + r"\%$}")
    lines.append(r"\newcommand{\leafSteps}{" + str(steps.pop()) + "}")
    lines.append("")
    return "\n".join(lines)


def render_all() -> Dict[str, str]:
    return {
        "table1_rl_performance.tex": render_table1(table1_rows()),
        "table2_proof_cost.tex": render_table2(table2_rows()),
        "table3_tamper_rejection.tex": render_table3(table3_rows()),
        "leaf_cycle_ranges.tex": render_leaf_cycle_macros(leaf_cycle_summaries()),
    }


def write_all(out_dir: Path | None = None) -> List[Path]:
    target = Path(out_dir) if out_dir is not None else GENERATED
    target.mkdir(parents=True, exist_ok=True)
    written = []
    for name, text in render_all().items():
        path = target / name
        path.write_text(text, encoding="utf-8")
        written.append(path)
    return written


if __name__ == "__main__":
    for path in write_all():
        print(path.relative_to(ROOT).as_posix())

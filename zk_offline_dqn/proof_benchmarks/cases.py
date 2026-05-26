from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ProofCase:
    case_id: str
    category: str
    relation: str
    variant: str
    scale_axis: str
    provenance_dir: str | None = None
    batch_size: int | None = None
    network: str | None = None
    trace_length: int | None = None
    dataset_size: int | None = None
    merkle_depth: int | None = None
    aggregation_t: int | None = None
    proof_backed: bool = True
    status: str = "proof_verified"
    notes: str = ""


CORE_CASES = [
    ProofCase("td_mvp", "core", "td_mvp", "canonical", "relation", None, batch_size=1, network="tiny"),
    ProofCase("merkle_membership", "core", "merkle_membership", "canonical", "merkle_depth", "merkle_membership"),
    ProofCase("forward_td_mlp", "core", "forward_td_mlp", "canonical_tiny", "network", "forward_td_mlp", batch_size=1, network="tiny"),
    ProofCase("one_step_sgd_tiny", "core", "one_step_sgd_tiny", "canonical_tiny", "network", "one_step_sgd_tiny", batch_size=1, network="tiny"),
    ProofCase("short_trace", "core", "short_trace", "canonical", "trace_length", "short_trace", trace_length=1, network="tiny"),
    ProofCase("training_update_batch1", "core", "training_update", "batch1_tiny", "batch_size", "training_update", batch_size=1, network="tiny", trace_length=1),
    ProofCase("training_fragment_k1", "core", "training_fragment_k1", "k1", "trace_length", "training_fragment_k1", batch_size=1, network="tiny", trace_length=1),
    ProofCase("training_fragment_k4", "core", "training_fragment_k4", "k4", "trace_length", "training_fragment_k4", batch_size=1, network="tiny", trace_length=4),
    ProofCase("training_fragment_k8", "core", "training_fragment_k8", "k8", "trace_length", "training_fragment_k8", batch_size=1, network="tiny", trace_length=8),
    ProofCase("training_aggregation_manifest_t32", "aggregation", "training_aggregation_manifest_t32", "proof_manifest_chain", "aggregation_t", "training_aggregation_t32", network="tiny", aggregation_t=32, notes="proof-manifest-chain; does not recursively verify child proofs inside SP1"),
    ProofCase("training_aggregation_manifest_t64", "aggregation", "training_aggregation_manifest_t64", "proof_manifest_chain", "aggregation_t", "training_aggregation_t64", network="tiny", aggregation_t=64, notes="proof-manifest-chain; does not recursively verify child proofs inside SP1"),
    ProofCase("training_aggregation_manifest_t128", "aggregation", "training_aggregation_manifest_t128", "proof_manifest_chain", "aggregation_t", "training_aggregation_t128", network="tiny", aggregation_t=128, notes="proof-manifest-chain; does not recursively verify child proofs inside SP1"),
]


def provenance_path(root: Path, case: ProofCase) -> Path | None:
    return None if case.provenance_dir is None else root / "artifacts/reports/provenance/sp1" / case.provenance_dir

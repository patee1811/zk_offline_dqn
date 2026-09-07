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
    ProofCase("td_mvp", "core", "td_mvp", "canonical", "relation", "td_mvp", batch_size=1, network="tiny"),
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
    # The two rows whose dataset_root is a root Table 1 also carries, so a
    # training proof and an RL result name the same committed object. They were
    # appended to the table by hand when first measured, which meant a
    # regenerated Table 2 silently dropped them; listing them here makes all
    # thirty rows come out of one run.
    ProofCase("training_fragment_cartpole_expert_k1", "core", "training_fragment", "cartpole_expert", "committed_dataset", "training_fragment_cartpole_expert_k1", batch_size=1, network="[4, 64, 2]", notes="dataset_root equals the committed cartpole-expert-v2 merkle_root"),
    ProofCase("training_fragment_lunarlander_expert_k1", "core", "training_fragment", "lunarlander_expert", "committed_dataset", "training_fragment_lunarlander_expert_k1", batch_size=1, network="[8, 64, 4]", notes="dataset_root equals the committed lunarlander-expert-v1 merkle_root"),
]


# Recursive aggregation, where the aggregate guest cryptographically verifies
# each child proof rather than binding a manifest hash. These rows read real
# provenance; the status field is the fallback used when it is absent, which is
# what these rows were before a GPU prover made them reachable.
RECURSIVE_CASES = [
    ProofCase(
        "native_flat_recursive_t16", "recursive_aggregation", "native_flat_recursive_t16",
        "true_recursive_native", "recursive_aggregation", "training_aggregation_recursive_t16",
        network="tiny", aggregation_t=16, status="failed_oom",
        notes="child proofs verified inside the aggregate SP1 guest; requires a CUDA prover",
    ),
    ProofCase(
        "native_flat_recursive_t32", "recursive_aggregation", "native_flat_recursive_t32",
        "true_recursive_native", "recursive_aggregation", "training_aggregation_recursive_t32",
        network="tiny", aggregation_t=32, status="failed_oom",
        notes="child proofs verified inside the aggregate SP1 guest; requires a CUDA prover",
    ),
    ProofCase(
        "native_flat_recursive_t64", "recursive_aggregation", "native_flat_recursive_t64",
        "true_recursive_native", "recursive_aggregation", "training_aggregation_recursive_t64",
        network="tiny", aggregation_t=64, status="failed_oom",
        notes="child proofs verified inside the aggregate SP1 guest; requires a CUDA prover",
    ),
    ProofCase(
        "binary_tree_native_t16", "recursive_aggregation", "binary_tree_native_t16",
        "binary_native_recursive", "recursive_aggregation", "training_aggregation_binary_native_t16",
        network="tiny", aggregation_t=16, status="failed_oom",
        notes="binary-tree topology; child proofs verified inside the aggregate SP1 guest",
    ),
    ProofCase(
        "groth16_recursive_t16", "recursive_aggregation", "groth16_recursive_t16",
        "groth16_child_proofs", "recursive_aggregation", "training_aggregation_groth16_t16",
        network="tiny", aggregation_t=16, status="failed_environment",
        notes="Groth16 child proofs verified in-guest; 20x the cycles of native child verification; PLONK child proofs are untested",
    ),
    # A whole run under one proof, rather than a fragment of one: step_start 0
    # to step_end 1248 over a binary tree of 8 leaves of 156 steps, each leaf
    # bound to the dataset the matching Table 1 rows train on. 1248 was where
    # the earlier attempt stopped, not where the prover did -- Q diverged into
    # i64 overflow at leaf 8 -- and the gradient clip in the relation is what
    # moved that wall.
    ProofCase(
        "binary_tree_native_t1248_cartpole", "recursive_aggregation",
        "binary_tree_native_t1248_cartpole", "whole_run_cartpole", "recursive_aggregation",
        "training_aggregation_binary_native_t1248_cartpole",
        network="[4, 64, 2]", aggregation_t=1248, status="failed_environment",
        notes="one root proof over the entire 1248-step run; dataset_root equals the committed cartpole-expert-v2 merkle_root",
    ),
    ProofCase(
        "binary_tree_native_t1248_lunarlander", "recursive_aggregation",
        "binary_tree_native_t1248_lunarlander", "whole_run_lunarlander", "recursive_aggregation",
        "training_aggregation_binary_native_t1248_lunarlander",
        network="[8, 64, 4]", aggregation_t=1248, status="failed_environment",
        notes="one root proof over the entire 1248-step run; dataset_root equals the committed lunarlander-expert-v1 merkle_root",
    ),
]


def provenance_path(root: Path, case: ProofCase) -> Path | None:
    return None if case.provenance_dir is None else root / "artifacts/reports/provenance/sp1" / case.provenance_dir

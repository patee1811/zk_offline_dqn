from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterable, List, Mapping, Sequence


STATUSES = {
    "rejected_as_expected",
    "accepted_unexpectedly",
    "wrong_rejection_layer",
    "not_applicable",
    "not_supported_current_backend",
    "skipped_incompatible",
    "failed_environment",
    "failed_timeout",
    "failed_setup",
}

LAYERS = {
    "dataset_audit",
    "dataset_commitment_verify",
    "python_semantic_oracle",
    "rust_execute",
    "sp1_prove",
    "sp1_verify",
    "public_input_binding",
    "report_source_check",
    "not_applicable",
}

MANDATORY_CATEGORIES = [
    "reward",
    "next_state",
    "done",
    "action",
    "merkle_path",
    "minibatch_index",
    "q_value",
    "td_target",
    "gradient",
    "checkpoint_hash",
    "target_network_sync",
    "proof_public_input",
]

TABLE3_COLUMNS = [
    "Tamper ID",
    "Tamper Category",
    "Relation / Component",
    "Artifact / Fixture",
    "Mutation",
    "Expected Rejection Layer",
    "Observed Rejection Layer",
    "Expected Result",
    "Observed Result",
    "Status",
    "Error Class",
    "Error Message Snippet",
    "Backend",
    "SP1 Proof Backed",
    "Proof Generated For Original",
    "Tampered Proof Generated",
    "Tampered Verify Passed",
    "Public Input Binding Checked",
    "Dataset Root Checked",
    "Manifest Hash Checked",
    "Audit Report Hash Checked",
    "Checkpoint Hash Checked",
    "Target Sync Checked",
    "Runtime Seconds",
    "Git Commit",
    "Notes",
]


@dataclass(frozen=True)
class TamperCase:
    tamper_id: str
    category: str
    component: str
    artifact: str
    mutation: str
    expected_layer: str
    backend: str
    proof_backed: bool
    source: str
    tamper_name: str = ""
    fixture_path: str = ""
    provenance_dir: str = ""
    public_input_binding: bool = False
    dataset_root_checked: bool = False
    manifest_hash_checked: bool = False
    audit_report_hash_checked: bool = False
    checkpoint_hash_checked: bool = False
    target_sync_checked: bool = False
    notes: str = ""
    proof_public_input_relation: str = ""


@dataclass(frozen=True)
class TamperResult:
    row: Dict[str, Any]
    additional_layers: Sequence[str] = ()


def row_from_case(
    case: TamperCase,
    *,
    observed_layer: str,
    status: str,
    observed_result: str,
    error_class: str = "",
    error_message: str = "",
    runtime_seconds: float | None = None,
    git_commit: str = "",
    notes: str = "",
    proof_generated_for_original: bool | None = None,
    tampered_proof_generated: bool | None = None,
    tampered_verify_passed: bool | None = None,
) -> Dict[str, Any]:
    combined_notes = "; ".join(
        item for item in [case.notes, notes] if item
    )
    row = {
        "Tamper ID": case.tamper_id,
        "Tamper Category": case.category,
        "Relation / Component": case.component,
        "Artifact / Fixture": case.artifact,
        "Mutation": case.mutation,
        "Expected Rejection Layer": case.expected_layer,
        "Observed Rejection Layer": observed_layer,
        "Expected Result": "reject",
        "Observed Result": observed_result,
        "Status": status,
        "Error Class": error_class,
        "Error Message Snippet": _snippet(error_message),
        "Backend": case.backend,
        "SP1 Proof Backed": bool(case.proof_backed),
        "Proof Generated For Original": proof_generated_for_original,
        "Tampered Proof Generated": tampered_proof_generated,
        "Tampered Verify Passed": tampered_verify_passed,
        "Public Input Binding Checked": bool(case.public_input_binding),
        "Dataset Root Checked": bool(case.dataset_root_checked),
        "Manifest Hash Checked": bool(case.manifest_hash_checked),
        "Audit Report Hash Checked": bool(case.audit_report_hash_checked),
        "Checkpoint Hash Checked": bool(case.checkpoint_hash_checked),
        "Target Sync Checked": bool(case.target_sync_checked),
        "Runtime Seconds": runtime_seconds,
        "Git Commit": git_commit,
        "Notes": combined_notes,
    }
    return row


def _snippet(value: str, limit: int = 180) -> str:
    text = " ".join(str(value or "").split())
    return text[:limit]


def validate_rows(rows: Iterable[Mapping[str, Any]]) -> None:
    for index, row in enumerate(rows):
        missing = [column for column in TABLE3_COLUMNS if column not in row]
        if missing:
            raise ValueError(f"row {index} missing Table 3 columns: {missing}")
        status = row.get("Status")
        if status not in STATUSES:
            raise ValueError(f"row {index} has invalid status: {status}")
        layer = row.get("Observed Rejection Layer")
        if layer not in LAYERS:
            raise ValueError(f"row {index} has invalid observed layer: {layer}")
        expected_layer = row.get("Expected Rejection Layer")
        if expected_layer not in LAYERS:
            raise ValueError(f"row {index} has invalid expected layer: {expected_layer}")
        if status == "not_applicable" and not str(row.get("Notes") or "").strip():
            raise ValueError(f"row {index} is not_applicable without a reason")


def check_mandatory_categories(rows: Iterable[Mapping[str, Any]]) -> Dict[str, Any]:
    materialized = list(rows)
    accepted = [
        str(row.get("Tamper ID"))
        for row in materialized
        if row.get("Status") == "accepted_unexpectedly"
    ]
    coverage = {}
    for category in MANDATORY_CATEGORIES:
        matched = [
            row
            for row in materialized
            if str(row.get("Tamper Category")) == category
            or category in str(row.get("Tamper ID", "")).lower()
        ]
        coverage[category] = {
            "total": len(matched),
            "rejected_as_expected": sum(
                1 for row in matched if row.get("Status") == "rejected_as_expected"
            ),
        }
    missing = [
        category
        for category, item in coverage.items()
        if item["rejected_as_expected"] < 1
    ]
    return {
        "status": "passed" if not accepted and not missing else "failed",
        "mandatory_category_coverage": coverage,
        "accepted_unexpectedly": accepted,
        "missing_mandatory_rejections": missing,
    }


def build_case_matrix(*, includes: Mapping[str, bool], smoke: bool = False) -> List[TamperCase]:
    cases: List[TamperCase] = []
    if includes.get("dataset"):
        cases.extend(dataset_cases())
    if includes.get("merkle"):
        cases.extend(merkle_cases(smoke=smoke))
    if includes.get("forward_td"):
        cases.extend(forward_td_cases())
    if includes.get("sgd"):
        cases.extend(sgd_cases())
    if includes.get("training_update"):
        cases.extend(training_update_cases())
    if includes.get("training_fragment"):
        cases.extend(training_fragment_cases(smoke=smoke))
    if includes.get("aggregation"):
        cases.extend(aggregation_cases(smoke=smoke))
        cases.extend(recursive_aggregation_cases(smoke=smoke))
    if includes.get("proof_public_input"):
        cases.extend(proof_public_input_cases(smoke=smoke))
    return cases


def _case(
    tamper_id: str,
    category: str,
    component: str,
    mutation: str,
    expected_layer: str,
    source: str,
    tamper_name: str = "",
    **kwargs: Any,
) -> TamperCase:
    return TamperCase(
        tamper_id=tamper_id,
        category=category,
        component=component,
        artifact=kwargs.pop("artifact", component),
        mutation=mutation,
        expected_layer=expected_layer,
        backend=kwargs.pop("backend", "Python semantic oracle"),
        proof_backed=bool(kwargs.pop("proof_backed", False)),
        source=source,
        tamper_name=tamper_name,
        **kwargs,
    )


def dataset_cases() -> List[TamperCase]:
    return [
        _case("tamper_reward_before_commit", "reward", "dataset_provenance", "increase reward before commitment", "dataset_audit", "dataset"),
        _case("tamper_next_state_before_commit", "next_state", "dataset_provenance", "modify next_state before commitment", "dataset_audit", "dataset"),
        _case("tamper_done_before_commit", "done", "dataset_provenance", "flip terminated flag before commitment", "dataset_audit", "dataset"),
        _case("tamper_action_before_commit", "action", "dataset_provenance", "change action before commitment", "dataset_audit", "dataset"),
        _case("tamper_manifest_hash", "manifest_hash", "dataset_commitment", "modify dataset_manifest.json after commitment", "dataset_commitment_verify", "dataset", manifest_hash_checked=True),
        _case("tamper_audit_report_hash", "audit_report_hash", "dataset_commitment", "modify replay_audit_report.json after commitment", "dataset_commitment_verify", "dataset", audit_report_hash_checked=True),
        _case("tamper_raw_trajectory_hash", "raw_trajectory_hash", "dataset_commitment", "modify raw_episodes.jsonl after commitment", "dataset_commitment_verify", "dataset"),
        _case("tamper_collection_log_final_hash", "collection_log_final_hash", "dataset_commitment", "modify collection_log.jsonl after commitment", "dataset_commitment_verify", "dataset"),
        _case("tamper_merkle_leaf", "merkle_path", "dataset_commitment", "modify merkle_tree.json leaf_hashes", "dataset_commitment_verify", "dataset", dataset_root_checked=True),
        _case("tamper_dataset_root", "dataset_root", "dataset_commitment", "modify merkle_tree.json dataset_root", "dataset_commitment_verify", "dataset", dataset_root_checked=True),
        _case("tamper_raw_after_commit", "raw_trajectory_hash", "dataset_commitment", "modify committed raw transition", "dataset_commitment_verify", "dataset"),
        _case("tamper_public_collection_log_final_hash_absent", "collection_log_final_hash", "public_dataset_commitment", "public benchmark has no honest collection log field to tamper", "not_applicable", "dataset", notes="public benchmark imports are source-integrity-only and do not carry collection_log_final_hash"),
    ]


def merkle_cases(*, smoke: bool = False) -> List[TamperCase]:
    base_names = [
        ("tamper_merkle_path_sibling", "merkle_path", "tamper_path_sibling", "change Merkle path sibling hash", False),
        ("tamper_merkle_path_direction", "merkle_path", "tamper_leaf_index", "make path direction/index inconsistent", False),
        ("tamper_merkle_leaf_hash", "merkle_leaf", "tamper_leaf_hash", "change public leaf hash", False),
        ("tamper_merkle_root", "dataset_root", "tamper_dataset_root", "change public dataset root", False),
        ("tamper_merkle_leaf_index", "minibatch_index", "tamper_leaf_index", "change leaf index", False),
        ("tamper_merkle_depth", "merkle_path", "tamper_path_sibling", "alter path so depth/root recomputation fails", False),
        ("tamper_merkle_manifest_hash_public_input", "proof_public_input", "tamper_manifest_hash_public_input", "change manifest hash public input", True),
        ("tamper_merkle_audit_report_hash_public_input", "proof_public_input", "tamper_audit_report_hash_public_input", "change audit report hash public input", True),
        ("tamper_merkle_dataset_size_public_input", "proof_public_input", "tamper_leaf_index", "change size/index-bound public statement", True),
        ("tamper_merkle_proof_public_input", "proof_public_input", "tamper_dataset_root", "verify original proof against mutated public input", True),
    ]
    variants = [("canonical", "zk_backend/test_vectors/merkle_membership_case_0.json", "merkle_membership")]
    if not smoke:
        variants.extend(
            [
                ("dataset_1k", "zk_backend/test_vectors/merkle_membership_dataset_1k_case_0.json", "merkle_membership_dataset_1k"),
                ("dataset_10k", "zk_backend/test_vectors/merkle_membership_dataset_10k_case_0.json", "merkle_membership_dataset_10k"),
                ("dataset_100k", "zk_backend/test_vectors/merkle_membership_dataset_100k_case_0.json", "merkle_membership_dataset_100k"),
            ]
        )
    cases: List[TamperCase] = []
    for variant, fixture, provenance in variants:
        for tamper_id, category, tamper_name, mutation, public_binding in base_names:
            cases.append(
                _case(
                    f"{tamper_id}_{variant}",
                    category,
                    "merkle_membership",
                    mutation,
                    "public_input_binding" if public_binding else "python_semantic_oracle",
                    "merkle",
                    tamper_name,
                    artifact=fixture,
                    fixture_path=fixture,
                    provenance_dir=provenance,
                    backend="SP1 Merkle membership",
                    proof_backed=True,
                    public_input_binding=public_binding,
                    dataset_root_checked=True,
                    manifest_hash_checked="manifest" in tamper_id,
                    audit_report_hash_checked="audit" in tamper_id,
                )
            )
    return cases


def forward_td_cases() -> List[TamperCase]:
    mapping = [
        ("tamper_q_online", "q_value", "tamper_q_online_public", "change claimed selected online Q"),
        ("tamper_q_target", "q_value", "tamper_q_target_public", "change claimed target-network Q"),
        ("tamper_td_target", "td_target", "tamper_td_target_public", "change claimed TD target"),
        ("tamper_loss", "loss", "tamper_loss_public", "change claimed loss"),
        ("tamper_reward", "reward", "tamper_reward", "change transition reward"),
        ("tamper_done", "done", "tamper_done", "flip done flag"),
        ("tamper_gamma", "td_target", "tamper_td_error_public", "change TD arithmetic public claim"),
        ("tamper_action_index", "action", "tamper_action", "change action index"),
        ("tamper_selected_q_value", "q_value", "tamper_q_online_public", "change selected Q value"),
        ("tamper_public_input_td_target", "proof_public_input", "tamper_td_target_public", "change TD target public input"),
        ("tamper_public_input_loss", "proof_public_input", "tamper_loss_public", "change loss public input"),
    ]
    return [
        _case(
            f"forward_td_mlp_{tamper_id}",
            category,
            "forward_td_mlp",
            mutation,
            "public_input_binding" if category == "proof_public_input" else "python_semantic_oracle",
            "forward_td",
            tamper_name,
            artifact="zk_backend/test_vectors/forward_td_mlp_case_0.json",
            fixture_path="zk_backend/test_vectors/forward_td_mlp_case_0.json",
            provenance_dir="forward_td_mlp",
            backend="SP1 Forward-TD MLP",
            proof_backed=True,
            public_input_binding=category == "proof_public_input",
        )
        for tamper_id, category, tamper_name, mutation in mapping
    ]


def sgd_cases() -> List[TamperCase]:
    mapping = [
        ("tamper_gradient", "gradient", "tamper_gradient", "change gradient tensor"),
        ("tamper_learning_rate", "gradient", "tamper_learning_rate_public", "change learning-rate public input"),
        ("tamper_weight_before", "checkpoint_hash", "tamper_old_weight", "change pre-update weight"),
        ("tamper_weight_after", "checkpoint_hash", "tamper_new_weight", "change post-update weight"),
        ("tamper_bias_before", "checkpoint_hash", "tamper_old_checkpoint_hash_public", "change pre-checkpoint commitment"),
        ("tamper_bias_after", "checkpoint_hash", "tamper_new_checkpoint_hash_public", "change post-checkpoint commitment"),
        ("tamper_public_input_checkpoint_or_update_hash", "proof_public_input", "tamper_update_hash_public", "change update hash public input"),
    ]
    return [
        _case(
            f"one_step_sgd_tiny_{tamper_id}",
            category,
            "one_step_sgd_tiny",
            mutation,
            "public_input_binding" if category == "proof_public_input" else "python_semantic_oracle",
            "sgd",
            tamper_name,
            artifact="zk_backend/test_vectors/one_step_sgd_tiny_case_0.json",
            fixture_path="zk_backend/test_vectors/one_step_sgd_tiny_case_0.json",
            provenance_dir="one_step_sgd_tiny",
            backend="SP1 one-step SGD tiny",
            proof_backed=True,
            public_input_binding=category == "proof_public_input",
            checkpoint_hash_checked="checkpoint" in tamper_id,
        )
        for tamper_id, category, tamper_name, mutation in mapping
    ]


def training_update_cases() -> List[TamperCase]:
    mapping = [
        ("tamper_training_update_reward", "reward", "tamper_reward", "change transition reward"),
        ("tamper_training_update_next_state", "next_state", "tamper_next_state", "change transition next_state"),
        ("tamper_training_update_done", "done", "tamper_terminated", "flip done flag"),
        ("tamper_training_update_action", "action", "tamper_action", "change transition action"),
        ("tamper_training_update_merkle_path", "merkle_path", "tamper_merkle_path", "change Merkle path"),
        ("tamper_training_update_minibatch_index", "minibatch_index", "tamper_leaf_index", "change minibatch/leaf index"),
        ("tamper_training_update_q_online", "q_value", "tamper_q_online_action", "change claimed online Q"),
        ("tamper_training_update_q_target", "q_value", "tamper_q_target_next", "change claimed target Q"),
        ("tamper_training_update_td_target", "td_target", "tamper_td_target", "change claimed TD target"),
        ("tamper_training_update_loss", "td_target", "tamper_loss", "change claimed loss"),
        ("tamper_training_update_gradient", "gradient", "tamper_gradient", "change gradient tensor"),
        ("tamper_training_update_weight_update", "gradient", "tamper_update_hash", "change update hash"),
        ("tamper_training_update_checkpoint_hash_t", "checkpoint_hash", "tamper_checkpoint_hash_t", "change input checkpoint hash"),
        ("tamper_training_update_checkpoint_hash_t_plus_1", "checkpoint_hash", "tamper_checkpoint_hash_t_plus_1", "change output checkpoint hash"),
        ("tamper_training_update_dataset_root", "dataset_root", "tamper_dataset_root", "change dataset root"),
        ("tamper_training_update_config_hash", "manifest_hash", "tamper_manifest_hash", "change manifest/config hash"),
        ("tamper_training_update_public_input_checkpoint", "proof_public_input", "tamper_checkpoint_hash_t_plus_1", "verify original proof against mutated checkpoint public input"),
    ]
    return [
        _case(
            tamper_id,
            category,
            "training_update",
            mutation,
            "public_input_binding" if category == "proof_public_input" else "python_semantic_oracle",
            "training_update",
            tamper_name,
            artifact="zk_backend/test_vectors/training_update_case_0.json",
            fixture_path="zk_backend/test_vectors/training_update_case_0.json",
            provenance_dir="training_update",
            backend="SP1 training update",
            proof_backed=True,
            public_input_binding=category == "proof_public_input",
            dataset_root_checked=category == "dataset_root" or "merkle" in tamper_id,
            manifest_hash_checked=category == "manifest_hash",
            checkpoint_hash_checked=category in {"checkpoint_hash", "proof_public_input"},
        )
        for tamper_id, category, tamper_name, mutation in mapping
    ]


def training_fragment_cases(*, smoke: bool = False) -> List[TamperCase]:
    ks = [8] if smoke else [1, 4, 8]
    mapping = [
        ("tamper_fragment_step_reward", "reward", "tamper_reward_at_step", "change step reward"),
        ("tamper_fragment_step_next_state", "next_state", "tamper_next_state_at_step", "change step next_state"),
        ("tamper_fragment_step_done", "done", "tamper_terminated_at_step", "flip step done flag"),
        ("tamper_fragment_step_action", "action", "tamper_action_at_step", "change step action"),
        ("tamper_fragment_merkle_path", "merkle_path", "tamper_merkle_path", "change step Merkle path"),
        ("tamper_fragment_minibatch_index", "minibatch_index", "tamper_minibatch_index", "change deterministic minibatch index"),
        ("tamper_fragment_gradient", "gradient", "tamper_gradient", "change gradient tensor"),
        ("tamper_fragment_intermediate_checkpoint_hash", "checkpoint_hash", "tamper_checkpoint_hash_after_step", "change intermediate checkpoint hash"),
        ("tamper_fragment_final_checkpoint_hash", "checkpoint_hash", "tamper_final_checkpoint_hash", "change final checkpoint hash"),
        ("tamper_fragment_target_network_sync", "target_network_sync", "tamper_target_sync_event", "change target-network sync event"),
        ("tamper_fragment_step_order", "minibatch_index", "tamper_step_order", "swap/change step order"),
        ("tamper_fragment_global_step", "minibatch_index", "tamper_sampler_seed", "change sampler/global step basis"),
        ("tamper_fragment_config_hash", "manifest_hash", "tamper_manifest_hash", "change config/provenance hash"),
        ("tamper_fragment_public_input_final_checkpoint", "proof_public_input", "tamper_final_checkpoint_hash", "change public final checkpoint"),
    ]
    cases: List[TamperCase] = []
    for k in ks:
        for tamper_id, category, tamper_name, mutation in mapping:
            cases.append(
                _case(
                    f"{tamper_id}_k{k}",
                    category,
                    f"training_fragment_k{k}",
                    mutation,
                    "public_input_binding" if category == "proof_public_input" else "python_semantic_oracle",
                    "training_fragment",
                    tamper_name,
                    artifact=f"zk_backend/test_vectors/training_fragment_k{k}_case_0.json",
                    fixture_path=f"zk_backend/test_vectors/training_fragment_k{k}_case_0.json",
                    provenance_dir=f"training_fragment_k{k}",
                    backend="SP1 training fragment",
                    proof_backed=True,
                    public_input_binding=category == "proof_public_input",
                    checkpoint_hash_checked=category in {"checkpoint_hash", "proof_public_input"},
                    target_sync_checked=category == "target_network_sync",
                    dataset_root_checked=category == "merkle_path",
                    manifest_hash_checked=category == "manifest_hash",
                )
            )
    return cases


def aggregation_cases(*, smoke: bool = False) -> List[TamperCase]:
    targets = [32] if smoke else [32, 64, 128]
    mapping = [
        ("tamper_aggregation_child_proof_hash", "proof_public_input", "tamper_proof_hash", "change child proof manifest hash"),
        ("tamper_aggregation_child_public_inputs_hash", "proof_public_input", "tamper_public_inputs_hash", "change child public inputs hash"),
        ("tamper_aggregation_chunk_order", "minibatch_index", "tamper_chunk_order", "change chunk order"),
        ("tamper_aggregation_checkpoint_link", "checkpoint_hash", "tamper_intermediate_checkpoint_link", "break online checkpoint link"),
        ("tamper_aggregation_target_checkpoint_link", "target_network_sync", "tamper_target_checkpoint_link", "break target checkpoint link"),
        ("tamper_aggregation_dataset_root", "dataset_root", "tamper_dataset_root", "change aggregate dataset root"),
        ("tamper_aggregation_config_hash", "manifest_hash", "tamper_config_hash", "change config hash"),
        ("tamper_aggregation_step_start", "minibatch_index", "tamper_step_start", "change aggregate step_start"),
        ("tamper_aggregation_step_end", "minibatch_index", "tamper_step_end", "change aggregate step_end"),
        ("tamper_aggregation_aggregate_root", "proof_public_input", "tamper_aggregate_root", "change aggregate root"),
        ("tamper_aggregation_public_input_final_checkpoint", "proof_public_input", "tamper_output_checkpoint_hash", "change public final checkpoint"),
    ]
    cases: List[TamperCase] = []
    for target in targets:
        for tamper_id, category, tamper_name, mutation in mapping:
            cases.append(
                _case(
                    f"{tamper_id}_t{target}",
                    category,
                    f"training_aggregation_manifest_t{target}",
                    mutation,
                    "public_input_binding" if category == "proof_public_input" else "python_semantic_oracle",
                    "aggregation",
                    tamper_name,
                    artifact=f"zk_backend/test_vectors/training_aggregation_t{target}_case_0.json",
                    fixture_path=f"zk_backend/test_vectors/training_aggregation_t{target}_case_0.json",
                    provenance_dir=f"training_aggregation_t{target}",
                    backend="SP1 proof-manifest aggregation",
                    proof_backed=True,
                    public_input_binding=category == "proof_public_input",
                    dataset_root_checked=category == "dataset_root",
                    manifest_hash_checked=category == "manifest_hash",
                    checkpoint_hash_checked=category in {"checkpoint_hash", "proof_public_input"},
                    target_sync_checked=category == "target_network_sync",
                    notes="proof-manifest-chain mode; child proofs are bound by hash, not verified in-guest (see the recursive rows for in-guest verification)",
                )
            )
    return cases


def recursive_aggregation_cases(*, smoke: bool = False) -> List[TamperCase]:
    """Tamper cases that only mean something when children are verified in-guest.

    Manifest mode binds a child by its hash, so attacking the proof bytes or the
    verifying key changes nothing it checks. Recursive mode runs the verifier, so
    these are the attacks that separate the two. The last one is the sharpest:
    every child proof is individually valid and the chain between them is broken.
    """
    configs = (
        [("training_aggregation_recursive_t16", 16, "flat")]
        if smoke
        else [
            ("training_aggregation_recursive_t16", 16, "flat"),
            ("training_aggregation_recursive_t32", 32, "flat"),
            ("training_aggregation_recursive_t64", 64, "flat"),
            ("training_aggregation_binary_native_t16", 16, "binary_tree"),
            ("training_aggregation_groth16_t16", 16, "groth16_child"),
        ]
    )
    mapping = [
        ("child_proof_bytes", "proof_public_input", "tamper_child_proof_bytes", "corrupt child proof bytes"),
        ("child_public_values", "proof_public_input", "tamper_child_public_values", "corrupt child public values"),
        ("child_vkey_hash", "proof_public_input", "tamper_child_vkey_hash", "substitute an unexpected child verifying key"),
        ("child_proof_order", "minibatch_index", "tamper_child_proof_order", "reorder child proofs"),
        ("valid_child_wrong_position", "minibatch_index", "tamper_valid_child_proof_wrong_position", "move a valid child proof to the wrong position"),
        ("valid_children_broken_chain", "checkpoint_hash", "tamper_individually_valid_child_proofs_broken_chain", "keep every child proof valid but break the checkpoint chain"),
        ("child_step_start", "minibatch_index", "tamper_child_step_start", "change child step_start"),
        ("child_step_end", "minibatch_index", "tamper_child_step_end", "change child step_end"),
        ("child_input_checkpoint", "checkpoint_hash", "tamper_child_input_checkpoint_hash", "change child input checkpoint hash"),
        ("child_output_checkpoint", "checkpoint_hash", "tamper_child_output_checkpoint_hash", "change child output checkpoint hash"),
        ("child_target_checkpoint", "target_network_sync", "tamper_child_target_checkpoint_hash", "change child target checkpoint hash"),
        ("child_dataset_root", "dataset_root", "tamper_child_dataset_root", "change child dataset root"),
        ("child_config_hash", "manifest_hash", "tamper_child_config_hash", "change child config hash"),
    ]
    cases: List[TamperCase] = []
    for provenance, target, topology in configs:
        for suffix, category, tamper_name, mutation in mapping:
            cases.append(
                _case(
                    f"tamper_recursive_{suffix}_{provenance}",
                    category,
                    provenance,
                    mutation,
                    "public_input_binding" if category == "proof_public_input" else "python_semantic_oracle",
                    "aggregation",
                    tamper_name,
                    artifact=f"artifacts/reports/provenance/sp1/{provenance}/tamper_report.json",
                    fixture_path=f"artifacts/reports/provenance/sp1/{provenance}/public_inputs.json",
                    provenance_dir=provenance,
                    backend="SP1 recursive aggregation",
                    proof_backed=True,
                    public_input_binding=category == "proof_public_input",
                    dataset_root_checked=category == "dataset_root",
                    manifest_hash_checked=category == "manifest_hash",
                    checkpoint_hash_checked=category in {"checkpoint_hash", "proof_public_input"},
                    target_sync_checked=category == "target_network_sync",
                    notes=f"child proofs verified inside the aggregate guest; T={target}, {topology} topology; requires a CUDA prover",
                )
            )
    return cases


def proof_public_input_cases(*, smoke: bool = False) -> List[TamperCase]:
    relations = [
        ("td_mvp", "td_mvp", "artifacts/reports/provenance/sp1/kaggle_sp1_validation_summary.json", ""),
        ("merkle", "merkle_membership", "artifacts/reports/provenance/sp1/merkle_membership/public_inputs.json", "merkle_membership"),
        ("forward_td_mlp", "forward_td_mlp", "artifacts/reports/provenance/sp1/forward_td_mlp/public_inputs.json", "forward_td_mlp"),
        ("one_step_sgd", "one_step_sgd_tiny", "artifacts/reports/provenance/sp1/one_step_sgd_tiny/public_inputs.json", "one_step_sgd_tiny"),
        ("training_update", "training_update", "artifacts/reports/provenance/sp1/training_update/public_inputs.json", "training_update"),
        ("training_fragment_k8", "training_fragment_k8", "artifacts/reports/provenance/sp1/training_fragment_k8/public_inputs.json", "training_fragment_k8"),
        ("training_aggregation_t32", "training_aggregation_manifest_t32", "artifacts/reports/provenance/sp1/training_aggregation_t32/public_inputs.json", "training_aggregation_t32"),
    ]
    cases = [
        _case(
            f"tamper_proof_public_input_{suffix}",
            "proof_public_input",
            component,
            "mutate public input hash used to bind the original proof/receipt",
            "public_input_binding",
            "proof_public_input",
            artifact=artifact,
            provenance_dir=provenance,
            backend="SP1 public input binding",
            proof_backed=True,
            public_input_binding=True,
            proof_public_input_relation=component,
        )
        for suffix, component, artifact, provenance in relations
    ]
    if not smoke:
        cases.extend(
            [
                _case(
                    "tamper_proof_bytes_if_available",
                    "proof_public_input",
                    "proof_artifact_policy",
                    "tamper retained proof bytes if policy kept them",
                    "sp1_verify",
                    "proof_bytes",
                    artifact="artifacts/reports/provenance/sp1/**/proof.bin",
                    backend="SP1 verify",
                    proof_backed=True,
                    notes="proof binaries are intentionally not committed",
                ),
                _case(
                    "tamper_receipt_if_available",
                    "proof_public_input",
                    "proof_artifact_policy",
                    "tamper retained receipt if policy kept it",
                    "sp1_verify",
                    "proof_bytes",
                    artifact="artifacts/reports/provenance/sp1/**/*.receipt",
                    backend="SP1 verify",
                    proof_backed=True,
                    notes="receipts are intentionally not committed",
                ),
            ]
        )
    return cases

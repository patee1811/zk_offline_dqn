from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Mapping

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from zk_offline_dqn.backends.sp1.training_aggregation import (  # noqa: E402
    BACKEND_DIR,
    cargo_command,
    case_path_for_target,
    load_case,
    tampered_case,
    verify_case_reference,
    write_generated_binary_native_case,
    write_generated_case,
    write_generated_recursive_case,
)
from zk_offline_dqn.backends.sp1.training_fragment import (  # noqa: E402
    BACKEND_DIR as FRAGMENT_BACKEND_DIR,
    cargo_command as fragment_cargo_command,
)
from zk_offline_dqn.relations.training_aggregation import (  # noqa: E402
    CHILD_PROOF_MODE,
    BINARY_AGGREGATION_TOPOLOGY,
    GROTH16_CHILD_PROOF_MODE,
    PLONK_CHILD_PROOF_MODE,
    RECURSIVE_AGGREGATION_MODE,
    RECURSIVE_CHILD_PROOF_MODES,
    build_binary_native_case,
    generate_recursive_child_cases,
    placeholder_aggregation_child_material,
    placeholder_child_material,
    recompute_roots,
)


TAMPER_CASES = [
    "tamper_step_start",
    "tamper_step_end",
    "tamper_chunk_order",
    "tamper_missing_chunk",
    "tamper_duplicate_chunk",
    "tamper_input_checkpoint_hash",
    "tamper_output_checkpoint_hash",
    "tamper_intermediate_checkpoint_link",
    "tamper_target_checkpoint_link",
    "tamper_dataset_root",
    "tamper_manifest_hash",
    "tamper_audit_report_hash",
    "tamper_collection_log_hash",
    "tamper_raw_trajectory_hash",
    "tamper_config_hash",
    "tamper_relation_id",
    "tamper_chunk_size",
    "tamper_chunk_count",
    "tamper_public_inputs_hash",
    "tamper_proof_hash",
    "tamper_verify_report_hash",
    "tamper_tamper_report_hash",
    "tamper_aggregate_root",
    "tamper_chunk_public_inputs_root",
    "tamper_chunk_proof_root",
]

RECURSIVE_TAMPER_CASES = [
    "tamper_child_proof_bytes",
    "tamper_child_public_values",
    "tamper_child_vkey_hash",
    "tamper_child_proof_hash",
    "tamper_child_proof_order",
    "tamper_child_step_start",
    "tamper_child_step_end",
    "tamper_child_input_checkpoint_hash",
    "tamper_child_output_checkpoint_hash",
    "tamper_child_target_checkpoint_hash",
    "tamper_child_dataset_root",
    "tamper_child_config_hash",
    "tamper_valid_child_proof_wrong_position",
    "tamper_individually_valid_child_proofs_broken_chain",
]

GROTH16_RECURSIVE_TAMPER_CASES = [
    "tamper_groth16_child_proof_bytes",
    "tamper_groth16_child_public_values",
    "tamper_groth16_child_vkey_hash",
    "tamper_groth16_child_public_values_hash",
    "tamper_groth16_valid_child_proof_wrong_position",
    "tamper_groth16_individually_valid_child_proofs_broken_chain",
]

PLONK_RECURSIVE_TAMPER_CASES = [
    "tamper_plonk_child_proof_bytes",
    "tamper_plonk_child_public_values",
    "tamper_plonk_child_vkey_hash",
    "tamper_plonk_child_public_values_hash",
    "tamper_plonk_valid_child_proof_wrong_position",
    "tamper_plonk_individually_valid_child_proofs_broken_chain",
]

BINARY_NATIVE_TAMPER_CASES = [
    "tamper_binary_native_left_child_proof_bytes",
    "tamper_binary_native_right_child_proof_bytes",
    "tamper_binary_native_left_public_values",
    "tamper_binary_native_right_public_values",
    "tamper_binary_native_left_vkey_hash",
    "tamper_binary_native_right_vkey_hash",
    "tamper_binary_native_swap_left_right",
    "tamper_binary_native_broken_checkpoint_link",
    "tamper_binary_native_broken_target_checkpoint_link",
    "tamper_binary_native_duplicate_child",
    "tamper_binary_native_missing_child",
    "tamper_binary_native_wrong_dataset_root",
    "tamper_binary_native_wrong_config_hash",
    "tamper_binary_native_wrong_node_range",
    "tamper_binary_native_wrong_child_relation_id",
]

BINARY_NATIVE_T32_TAMPER_CASES = [
    "tamper_binary_native_t32_root_uses_leaf_instead_of_level1",
    "tamper_binary_native_t32_level1_manifests_swapped",
]

CORE_RUST_TAMPER_CASES = [
    "tamper_chunk_order",
    "tamper_intermediate_checkpoint_link",
    "tamper_target_checkpoint_link",
    "tamper_dataset_root",
    "tamper_relation_id",
    "tamper_public_inputs_hash",
    "tamper_proof_hash",
    "tamper_aggregate_root",
]

RECURSIVE_CORE_RUST_TAMPER_CASES = [
    "tamper_child_proof_bytes",
    "tamper_child_public_values",
    "tamper_child_vkey_hash",
    "tamper_child_proof_order",
    "tamper_valid_child_proof_wrong_position",
    "tamper_individually_valid_child_proofs_broken_chain",
]

BINARY_NATIVE_CORE_RUST_TAMPER_CASES = [
    "tamper_binary_native_left_child_proof_bytes",
    "tamper_binary_native_right_child_proof_bytes",
    "tamper_binary_native_left_public_values",
    "tamper_binary_native_right_public_values",
    "tamper_binary_native_left_vkey_hash",
    "tamper_binary_native_right_vkey_hash",
    "tamper_binary_native_swap_left_right",
    "tamper_binary_native_broken_checkpoint_link",
    "tamper_binary_native_broken_target_checkpoint_link",
]


def write_json(path: Path, data: Any, *, compact: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if compact:
        payload = json.dumps(data, sort_keys=True, separators=(",", ":"))
    else:
        payload = json.dumps(data, indent=2, sort_keys=True)
    path.write_text(payload + "\n", encoding="utf-8")


def run_command(
    command: List[str], *, cwd: Path = BACKEND_DIR, env: Dict[str, str] | None = None
) -> Dict[str, Any]:
    run_env = os.environ.copy()
    if env:
        run_env.update(env)
    result = subprocess.run(command, cwd=cwd, env=run_env, capture_output=True, text=True)
    return {
        "command": " ".join(command),
        "passed": result.returncode == 0,
        "return_code": result.returncode,
        "stdout_tail": "\n".join(result.stdout.splitlines()[-40:]),
        "stderr_tail": "\n".join(result.stderr.splitlines()[-40:]),
    }


def public_child_proof_mode(case: Mapping[str, Any]) -> str | None:
    return case["public_inputs"].get("child_proof_mode")


def public_topology(case: Mapping[str, Any]) -> str | None:
    return case["public_inputs"].get("aggregation_topology")


def output_dir_name(public: Mapping[str, Any]) -> str:
    if public["aggregation_mode"] != RECURSIVE_AGGREGATION_MODE:
        return f"training_aggregation_t{public['step_end']}"
    if public.get("aggregation_topology") == BINARY_AGGREGATION_TOPOLOGY:
        return f"training_aggregation_binary_native_t{public['step_end']}"
    if public.get("child_proof_mode") == GROTH16_CHILD_PROOF_MODE:
        return f"training_aggregation_groth16_t{public['step_end']}"
    if public.get("child_proof_mode") == PLONK_CHILD_PROOF_MODE:
        return f"training_aggregation_plonk_t{public['step_end']}"
    return f"training_aggregation_recursive_t{public['step_end']}"


def run_tamper_checks(case_path: Path, out_dir: Path, run_execute: bool) -> Dict[str, Any]:
    case = load_case(case_path)
    recursive = case["public_inputs"]["aggregation_mode"] == RECURSIVE_AGGREGATION_MODE
    names = TAMPER_CASES + (RECURSIVE_TAMPER_CASES if recursive else [])
    if public_child_proof_mode(case) == GROTH16_CHILD_PROOF_MODE:
        names += GROTH16_RECURSIVE_TAMPER_CASES
    if public_child_proof_mode(case) == PLONK_CHILD_PROOF_MODE:
        names += PLONK_RECURSIVE_TAMPER_CASES
    if public_topology(case) == BINARY_AGGREGATION_TOPOLOGY:
        names += BINARY_NATIVE_TAMPER_CASES
        if int(case["public_inputs"]["step_end"]) == 32:
            names += BINARY_NATIVE_T32_TAMPER_CASES
    rust_names = CORE_RUST_TAMPER_CASES + (RECURSIVE_CORE_RUST_TAMPER_CASES if recursive else [])
    if public_topology(case) == BINARY_AGGREGATION_TOPOLOGY:
        rust_names += BINARY_NATIVE_CORE_RUST_TAMPER_CASES
    checks = []
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        for name in names:
            mutated = tampered_case(case, name)
            reference = verify_case_reference(mutated)
            execute = None
            if run_execute and name in rust_names:
                path = tmp_path / f"{name}.json"
                write_json(path, mutated, compact=True)
                execute = run_command(
                    cargo_command(
                        case_path=path,
                        mode="execute",
                        aggregation_mode=case["public_inputs"]["aggregation_mode"],
                        child_proof_mode=public_child_proof_mode(case),
                        topology=public_topology(case),
                    )
                )
            passed = not reference.accepted
            if execute is not None:
                passed = passed and not execute["passed"]
            checks.append(
                {
                    "case": name,
                    "passed": passed,
                    "reference_accepted": reference.accepted,
                    "reference_reason": reference.reason,
                    "execute_passed": None if execute is None else execute["passed"],
                    "execute_return_code": None if execute is None else execute["return_code"],
                }
            )
    report = {
        "relation": "training_aggregation",
        "aggregation_mode": case["public_inputs"]["aggregation_mode"],
        "chunk_size": case["public_inputs"]["chunk_size"],
        "chunk_count": case["public_inputs"]["chunk_count"],
        "step_end": case["public_inputs"]["step_end"],
        "all_passed": all(item["passed"] for item in checks),
        "checks": checks,
    }
    write_json(out_dir / "tamper_report.json", report)
    return report


def validate_case(
    case_path: Path,
    out_root: Path,
    aggregation_mode: str,
    run_execute: bool,
    run_prove: bool,
) -> Dict[str, Any]:
    case = load_case(case_path)
    public = case["public_inputs"]
    recursive = public["aggregation_mode"] == RECURSIVE_AGGREGATION_MODE
    target = int(public["step_end"])
    out_dir = out_root / output_dir_name(public)
    out_dir.mkdir(parents=True, exist_ok=True)
    reference = verify_case_reference(case)
    roots = (
        recompute_roots(case["private_witness"]["chunks"], recursive=recursive)
        if reference.accepted
        else {}
    )
    execute = None
    if run_execute or run_prove:
        execute = run_command(
            cargo_command(
                case_path=case_path,
                mode="execute",
                aggregation_mode=aggregation_mode,
                child_proof_mode=public.get("child_proof_mode"),
                topology=public.get("aggregation_topology"),
            )
        )
    proof = None
    should_prove = run_prove or os.environ.get("RUN_SP1_PROVE") == "1"
    if should_prove:
        proof = run_command(
            cargo_command(
                case_path=case_path,
                mode="prove",
                aggregation_mode=aggregation_mode,
                child_proof_mode=public.get("child_proof_mode"),
                topology=public.get("aggregation_topology"),
                out_dir=out_dir,
            ),
            env={"RUN_SP1_PROVE": "1"},
        )
        proof_path = out_dir / "proof.bin"
        if proof_path.exists():
            proof_path.unlink()
    tamper = run_tamper_checks(case_path, out_dir, run_execute=bool(execute and execute["passed"]))
    required_files = [
        "public_inputs.json",
        "witness_schema.json",
        "metrics.json",
        "verify_report.json",
        "tamper_report.json",
        "proof_artifact_policy.json",
        "aggregation_manifest.json",
        "chunk_manifest.json",
    ]
    if recursive:
        required_files.append("recursive_child_proof_manifest.json")
    if public.get("aggregation_topology") == BINARY_AGGREGATION_TOPOLOGY:
        required_files.append("binary_tree_manifest.json")
    proof_backed = bool(proof and proof["passed"] and tamper["all_passed"])
    status = {
        "relation": "training_aggregation",
        "aggregation_mode": public["aggregation_mode"],
        "aggregation_topology": public.get("aggregation_topology"),
        "child_proof_mode": public.get("child_proof_mode"),
        "chunk_size": public["chunk_size"],
        "chunk_count": public["chunk_count"],
        "leaf_chunk_count": public.get("leaf_chunk_count"),
        "tree_depth": public.get("node_depth"),
        "step_start": public["step_start"],
        "step_end": public["step_end"],
        "reference_passed": reference.accepted,
        "execute_passed": bool(execute and execute["passed"]),
        "proof_generated": bool(proof and proof["passed"] and (out_dir / "metrics.json").exists()),
        "proof_verified": bool(proof and proof["passed"]),
        "public_inputs_saved": (out_dir / "public_inputs.json").exists(),
        "witness_schema_saved": (out_dir / "witness_schema.json").exists(),
        "metrics_saved": (out_dir / "metrics.json").exists(),
        "verify_report_saved": (out_dir / "verify_report.json").exists(),
        "tamper_report_saved": (out_dir / "tamper_report.json").exists(),
        "proof_artifact_policy_saved": (out_dir / "proof_artifact_policy.json").exists(),
        "aggregation_manifest_saved": (out_dir / "aggregation_manifest.json").exists(),
        "chunk_manifest_saved": (out_dir / "chunk_manifest.json").exists(),
        "recursive_child_proof_manifest_saved": (
            out_dir / "recursive_child_proof_manifest.json"
        ).exists(),
        "tamper_test_passed": bool(tamper["all_passed"]),
        "child_proof_verification_inside_guest": recursive,
        "roots_match_reference": bool(
            roots and all(public[key] == value for key, value in roots.items())
        ),
        "claim_status": (
            "sp1_true_recursive_binary_tree_proof_backed"
            if public.get("aggregation_topology") == BINARY_AGGREGATION_TOPOLOGY
            else "sp1_true_recursive_aggregation_proof_backed"
            if recursive
            else "sp1_proof_backed_manifest_chain_not_true_recursion"
        )
        if proof_backed and all((out_dir / name).exists() for name in required_files)
        else "not_proof_backed",
        "execute": execute,
        "proof": proof,
    }
    write_json(out_dir / f"{out_dir.name}_status.json", status)
    return status


def prepare_recursive_case(
    target: int,
    out_root: Path,
    *,
    child_proof_mode: str,
    run_child_proves: bool,
) -> tuple[Path, List[Dict[str, Any]]]:
    if child_proof_mode not in RECURSIVE_CHILD_PROOF_MODES:
        raise SystemExit(f"unsupported --child-proof-mode {child_proof_mode}")
    child_cases = generate_recursive_child_cases(target)
    work_dir = out_root / "_recursive_child_work" / f"t{target}"
    case_dir = work_dir / "cases"
    materials: List[Dict[str, Any]] = []
    child_statuses = []
    for chunk_id, child_case in enumerate(child_cases):
        case_path = case_dir / f"training_fragment_recursive_chunk_{chunk_id}.json"
        write_json(case_path, child_case, compact=True)
        if run_child_proves:
            child_out = work_dir / f"child_{chunk_id}"
            prove = run_command(
                fragment_cargo_command(
                    case_path=case_path,
                    mode="prove",
                    out_dir=child_out,
                    max_steps=8,
                    proof_mode=child_proof_mode,
                ),
                cwd=FRAGMENT_BACKEND_DIR,
                env={"RUN_SP1_PROVE": "1"},
            )
            material_path = child_out / "recursive_child_proof_material.json"
            if not prove["passed"] or not material_path.exists():
                raise RuntimeError(
                    f"child proof {chunk_id} failed: {prove['stderr_tail'] or prove['stdout_tail']}"
                )
            material = json.loads(material_path.read_text(encoding="utf-8"))
            material["metrics_hash"] = sha256_file(child_out / "metrics.json")
            material["verify_report_hash"] = sha256_file(child_out / "verify_report.json")
            proof_path = child_out / "proof.bin"
            if proof_path.exists():
                proof_path.unlink()
        else:
            material = placeholder_child_material(
                child_case,
                chunk_id,
                proof_mode=child_proof_mode,
            )
            prove = None
        materials.append(material)
        child_statuses.append(
            {
                "chunk_id": chunk_id,
                "step_start": child_case["public_inputs"]["global_step_start"],
                "step_end": child_case["public_inputs"]["global_step_start"]
                + child_case["public_inputs"]["num_steps"],
                "child_proof_material_saved": "proof_bytes" in material,
                "prove": prove,
            }
        )
    case_path = out_root / "_recursive_cases" / f"training_aggregation_recursive_t{target}_case_0.json"
    write_generated_recursive_case(
        target,
        case_path,
        child_materials=materials,
        child_proof_mode=child_proof_mode,
    )
    write_json(work_dir / "child_proof_status.json", {"children": child_statuses})
    return case_path, child_statuses


def _prepare_leaf_materials(
    child_cases: List[Mapping[str, Any]],
    work_dir: Path,
    *,
    run_child_proves: bool,
) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    case_dir = work_dir / "leaf_cases"
    materials: List[Dict[str, Any]] = []
    statuses = []
    for chunk_id, child_case in enumerate(child_cases):
        case_path = case_dir / f"training_fragment_binary_leaf_{chunk_id}.json"
        write_json(case_path, child_case, compact=True)
        if run_child_proves:
            child_out = work_dir / f"leaf_{chunk_id}"
            prove = run_command(
                fragment_cargo_command(
                    case_path=case_path,
                    mode="prove",
                    out_dir=child_out,
                    max_steps=8,
                    proof_mode=CHILD_PROOF_MODE,
                ),
                cwd=FRAGMENT_BACKEND_DIR,
                env={"RUN_SP1_PROVE": "1"},
            )
            material_path = child_out / "recursive_child_proof_material.json"
            if not prove["passed"] or not material_path.exists():
                raise RuntimeError(
                    f"binary leaf proof {chunk_id} failed: {prove['stderr_tail'] or prove['stdout_tail']}"
                )
            material = json.loads(material_path.read_text(encoding="utf-8"))
            material["metrics_hash"] = sha256_file(child_out / "metrics.json")
            material["verify_report_hash"] = sha256_file(child_out / "verify_report.json")
            proof_path = child_out / "proof.bin"
            if proof_path.exists():
                proof_path.unlink()
        else:
            material = placeholder_child_material(child_case, chunk_id)
            prove = None
        materials.append(material)
        statuses.append(
            {
                "chunk_id": chunk_id,
                "step_start": child_case["public_inputs"]["global_step_start"],
                "step_end": child_case["public_inputs"]["global_step_start"]
                + child_case["public_inputs"]["num_steps"],
                "prove": prove,
            }
        )
    return materials, statuses


def _prove_binary_node_material(
    case: Mapping[str, Any],
    case_path: Path,
    out_dir: Path,
    *,
    run_child_proves: bool,
    child_id: int,
) -> tuple[Dict[str, Any], Dict[str, Any]]:
    write_json(case_path, case, compact=True)
    if not run_child_proves:
        return placeholder_aggregation_child_material(case, child_id), {"prove": None}
    prove = run_command(
        cargo_command(
            case_path=case_path,
            mode="prove",
            aggregation_mode=RECURSIVE_AGGREGATION_MODE,
            child_proof_mode=CHILD_PROOF_MODE,
            topology=BINARY_AGGREGATION_TOPOLOGY,
            out_dir=out_dir,
        ),
        env={"RUN_SP1_PROVE": "1"},
    )
    material_path = out_dir / "recursive_child_proof_material.json"
    if not prove["passed"] or not material_path.exists():
        raise RuntimeError(
            f"binary internal proof {child_id} failed: {prove['stderr_tail'] or prove['stdout_tail']}"
        )
    material = json.loads(material_path.read_text(encoding="utf-8"))
    material["metrics_hash"] = sha256_file(out_dir / "metrics.json")
    material["verify_report_hash"] = sha256_file(out_dir / "verify_report.json")
    proof_path = out_dir / "proof.bin"
    if proof_path.exists():
        proof_path.unlink()
    return material, {"prove": prove, "out_dir": str(out_dir)}


def _build_binary_level(
    cases,
    materials,
    *,
    depth: int,
    leaf_chunk_count: int,
    work_dir: Path,
    run_child_proves: bool,
    statuses: List[Dict[str, Any]],
    internal_dirs: Dict[str, Path],
):
    """Fold one level of the tree: pair siblings, prove each pair, return the parents.

    Recursion needs the parent to verify proofs of nodes that are themselves
    parents, so every level except the last is proved here and its material is
    handed upward. The root is not proved -- the caller writes its case and the
    host proves it, the same way the depth-1 tree always worked.
    """
    parent_cases = []
    parent_materials = []
    level_dir = work_dir / f"level{depth}"
    is_root_level = len(cases) == 2
    for pair_id in range(0, len(cases), 2):
        # The last fold produces the root, and downstream provenance keys off
        # node_id == "root".
        node_id = "root" if is_root_level else f"level{depth}_node{pair_id // 2}"
        case = build_binary_native_case(
            cases[pair_id : pair_id + 2],
            materials[pair_id : pair_id + 2],
            node_id=node_id,
            node_depth=depth,
            leaf_chunk_count=leaf_chunk_count,
        )
        parent_cases.append(case)
        if is_root_level:
            # The caller writes the root case and the host proves it.
            parent_materials.append(None)
            continue
        out_dir = level_dir / node_id
        material, status = _prove_binary_node_material(
            case,
            level_dir / f"{node_id}_case.json",
            out_dir,
            run_child_proves=run_child_proves,
            child_id=pair_id // 2,
        )
        parent_materials.append(material)
        statuses.append({"node_id": node_id, **status})
        internal_dirs[node_id] = out_dir
    return parent_cases, parent_materials


def prepare_binary_native_case(
    target: int,
    out_root: Path,
    *,
    run_child_proves: bool,
) -> tuple[Path, List[Dict[str, Any]], Dict[str, Path]]:
    child_cases = generate_recursive_child_cases(target)
    leaves = len(child_cases)
    if leaves < 2 or leaves & (leaves - 1):
        raise SystemExit(
            f"binary native aggregation needs a power-of-two leaf count, got {leaves}"
        )
    work_dir = out_root / "_binary_native_work" / f"t{target}"
    leaf_materials, statuses = _prepare_leaf_materials(
        child_cases, work_dir, run_child_proves=run_child_proves
    )
    internal_dirs: Dict[str, Path] = {}

    cases = list(child_cases)
    materials = list(leaf_materials)
    depth = 0
    span = 2
    while len(cases) > 1:
        depth += 1
        cases, materials = _build_binary_level(
            cases,
            materials,
            depth=depth,
            leaf_chunk_count=span,
            work_dir=work_dir,
            run_child_proves=run_child_proves,
            statuses=statuses,
            internal_dirs=internal_dirs,
        )
        span *= 2
    case = cases[0]

    case_path = (
        out_root
        / "_binary_native_cases"
        / f"training_aggregation_binary_native_t{target}_case_0.json"
    )
    write_json(case_path, case, compact=True)
    write_json(work_dir / "binary_child_proof_status.json", {"children": statuses})
    return case_path, statuses, internal_dirs


def copy_level1_manifests(root_out_dir: Path, internal_dirs: Mapping[str, Path]) -> None:
    for node_id, source in internal_dirs.items():
        manifest = source / "aggregation_manifest.json"
        if manifest.exists():
            (root_out_dir / f"{node_id}_manifest.json").write_bytes(manifest.read_bytes())


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--targets", nargs="+", type=int, default=[32, 64, 128])
    parser.add_argument("--chunk-size", type=int, default=8)
    parser.add_argument("--aggregation-mode", default="proof_manifest_chain")
    parser.add_argument("--aggregation-topology")
    parser.add_argument("--child-proof-mode", default=CHILD_PROOF_MODE)
    parser.add_argument("--out-root", default="artifacts/reports/provenance/sp1")
    parser.add_argument("--run-reference", action="store_true")
    parser.add_argument("--run-child-proves", action="store_true")
    parser.add_argument("--run-execute", action="store_true")
    parser.add_argument("--run-prove", action="store_true")
    parser.add_argument("--continue-on-failure", action="store_true")
    args = parser.parse_args()
    if args.chunk_size != 8:
        raise SystemExit("Phase 7 requires --chunk-size 8")
    if args.aggregation_mode not in {"proof_manifest_chain", RECURSIVE_AGGREGATION_MODE}:
        raise SystemExit("unsupported --aggregation-mode")
    if args.aggregation_topology not in {None, BINARY_AGGREGATION_TOPOLOGY}:
        raise SystemExit("unsupported --aggregation-topology")
    if (
        args.aggregation_mode == RECURSIVE_AGGREGATION_MODE
        and (args.run_execute or args.run_prove)
        and not args.run_child_proves
    ):
        raise SystemExit("recursive execute/prove requires --run-child-proves")
    out_root = Path(args.out_root)
    if not out_root.is_absolute():
        out_root = ROOT / out_root
    statuses = []
    for target in args.targets:
        child_statuses = []
        internal_dirs: Dict[str, Path] = {}
        if (
            args.aggregation_mode == RECURSIVE_AGGREGATION_MODE
            and args.aggregation_topology == BINARY_AGGREGATION_TOPOLOGY
        ):
            case_path, child_statuses, internal_dirs = prepare_binary_native_case(
                target,
                out_root,
                run_child_proves=args.run_child_proves,
            )
        elif args.aggregation_mode == RECURSIVE_AGGREGATION_MODE:
            case_path, child_statuses = prepare_recursive_case(
                target,
                out_root,
                child_proof_mode=args.child_proof_mode,
                run_child_proves=args.run_child_proves,
            )
        else:
            case_path = write_generated_case(target)
        status = validate_case(
            case_path,
            out_root,
            aggregation_mode=args.aggregation_mode,
            run_execute=args.run_execute,
            run_prove=args.run_prove,
        )
        status["child_proves"] = child_statuses
        if status["proof_verified"] and internal_dirs:
            copy_level1_manifests(
                out_root / output_dir_name(load_case(case_path)["public_inputs"]), internal_dirs
            )
        statuses.append(status)
        if (
            args.aggregation_mode == RECURSIVE_AGGREGATION_MODE
            and (args.run_execute or args.run_prove)
            and not status["proof_verified"]
            and args.run_prove
            and not args.continue_on_failure
        ):
            break
    summary = {"relation": "training_aggregation", "cases": statuses}
    status_name = (
        "phase7_true_recursive_aggregation_status.json"
        if args.aggregation_mode == RECURSIVE_AGGREGATION_MODE
        else "phase7_training_aggregation_status.json"
    )
    write_json(out_root / status_name, summary)
    print(json.dumps(summary, indent=2, sort_keys=True))
    should_prove = args.run_prove or os.environ.get("RUN_SP1_PROVE") == "1"
    ok = all(item["reference_passed"] and item["tamper_test_passed"] for item in statuses)
    if args.run_execute:
        ok = ok and all(item["execute_passed"] for item in statuses)
    if should_prove:
        ok = ok and all(item["proof_verified"] for item in statuses)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

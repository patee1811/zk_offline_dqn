"""Verification subcommands for the zk_offline_dqn CLI."""

from __future__ import annotations

import argparse
import os
from typing import Any, Callable

from zk_offline_dqn.verifiers.forward_td_mlp import (
    DEFAULT_INPUT as DEFAULT_FORWARD_TD_MLP_INPUT,
    verify_forward_td_mlp_test_vector_path_report,
)
from zk_offline_dqn.verifiers.membership import (
    DEFAULT_TRANSITION_MEMBERSHIP_ARTIFACT_PATH,
    format_transition_membership_report,
    load_transition_membership_artifact,
    verify_transition_membership_artifact,
)
from zk_offline_dqn.verifiers.minibatch_td import (
    DEFAULT_ARTIFACT_PATH as DEFAULT_MINIBATCH_TD_ARTIFACT_PATH,
    DEFAULT_CHECKPOINT_PATH as DEFAULT_MINIBATCH_TD_CHECKPOINT_PATH,
    verify_minibatch_td_artifact_path_report,
)
from zk_offline_dqn.verifiers.one_step_sgd_tiny import (
    DEFAULT_INPUT as DEFAULT_ONE_STEP_SGD_TINY_INPUT,
    verify_one_step_sgd_tiny_test_vector_path_report,
)
from zk_offline_dqn.verifiers.one_step_update import (
    DEFAULT_ARTIFACT_PATH as DEFAULT_ONE_STEP_UPDATE_ARTIFACT_PATH,
    DEFAULT_MERKLE_PATH as DEFAULT_ONE_STEP_UPDATE_MERKLE_PATH,
    verify_one_step_update_artifact_path_report,
)
from zk_offline_dqn.verifiers.short_trace import (
    DEFAULT_ARTIFACT_PATH as DEFAULT_SHORT_TRACE_ARTIFACT_PATH,
    verify_short_trace_artifact_path_report,
)
from zk_offline_dqn.verifiers.td_mvp import (
    DEFAULT_INPUT as DEFAULT_TD_MVP_INPUT,
    verify_td_mvp_test_vector_path_report,
)


CommandFunc = Callable[[argparse.Namespace], int]


def _print_accepted(accepted: bool) -> int:
    print(f"accepted = {accepted}")
    return 0 if accepted else 1


def _run_command(args: argparse.Namespace, func: CommandFunc) -> int:
    try:
        return func(args)
    except Exception as exc:
        print("accepted = False")
        print(f"error = {type(exc).__name__}: {exc}")
        return 1


def _verify_membership(args: argparse.Namespace) -> int:
    artifact = load_transition_membership_artifact(args.artifact)
    result = verify_transition_membership_artifact(artifact)
    print(format_transition_membership_report(artifact, result, args.artifact))
    return _print_accepted(result.accepted)


def _verify_td_mvp(args: argparse.Namespace) -> int:
    result, report = verify_td_mvp_test_vector_path_report(args.input)
    print(report)
    return _print_accepted(bool(result["verification_passed"]))


def _verify_forward_td_mlp(args: argparse.Namespace) -> int:
    _, report = verify_forward_td_mlp_test_vector_path_report(args.input)
    print(report)
    return _print_accepted(True)


def _verify_one_step_sgd_tiny(args: argparse.Namespace) -> int:
    _, report = verify_one_step_sgd_tiny_test_vector_path_report(args.input)
    print(report)
    return _print_accepted(True)


def _verify_minibatch_td(args: argparse.Namespace) -> int:
    result, report = verify_minibatch_td_artifact_path_report(
        artifact_path=args.artifact,
        checkpoint_path=args.checkpoint,
    )
    print(report)
    return _print_accepted(bool(result["verification_passed"]))


def _verify_one_step_update(args: argparse.Namespace) -> int:
    kwargs: dict[str, Any] = {
        "artifact_path": args.artifact,
        "merkle_path": args.merkle,
    }
    if args.checkpoint is not None:
        kwargs["checkpoint_path"] = args.checkpoint
    if args.post_checkpoint is not None:
        kwargs["post_checkpoint_path"] = args.post_checkpoint

    result, report = verify_one_step_update_artifact_path_report(**kwargs)
    print(report)
    return _print_accepted(bool(result["verification_passed"]))


def _verify_short_trace(args: argparse.Namespace) -> int:
    result, report = verify_short_trace_artifact_path_report(
        artifact_path=args.artifact,
        merkle_path=args.merkle,
        initial_checkpoint_path=args.initial_checkpoint,
        final_checkpoint_path=args.final_checkpoint,
        work_dir=args.work_dir,
    )
    print(report)
    return _print_accepted(bool(result["verification_passed"]))


def register_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
    parser = subparsers.add_parser(
        "verify",
        help="Run relation-level artifact and test-vector verifiers.",
        description="Run relation-level artifact and test-vector verifiers.",
    )
    verify_subparsers = parser.add_subparsers(dest="verify_command", required=True)

    membership = verify_subparsers.add_parser(
        "membership",
        help="Verify a transition membership artifact.",
    )
    membership.add_argument(
        "--artifact",
        default=DEFAULT_TRANSITION_MEMBERSHIP_ARTIFACT_PATH,
        help="Transition membership artifact path.",
    )
    membership.set_defaults(func=lambda args: _run_command(args, _verify_membership))

    td_mvp = verify_subparsers.add_parser(
        "td-mvp",
        help="Verify a TD MVP test vector.",
    )
    td_mvp.add_argument(
        "--input",
        default=str(DEFAULT_TD_MVP_INPUT),
        help="TD MVP test-vector path.",
    )
    td_mvp.set_defaults(func=lambda args: _run_command(args, _verify_td_mvp))

    forward_td_mlp = verify_subparsers.add_parser(
        "forward-td-mlp",
        help="Verify a forward-TD MLP test vector.",
    )
    forward_td_mlp.add_argument(
        "--input",
        default=DEFAULT_FORWARD_TD_MLP_INPUT,
        help="Forward-TD MLP test-vector path.",
    )
    forward_td_mlp.set_defaults(
        func=lambda args: _run_command(args, _verify_forward_td_mlp)
    )

    one_step_sgd_tiny = verify_subparsers.add_parser(
        "one-step-sgd-tiny",
        help="Verify a one-step SGD tiny test vector.",
    )
    one_step_sgd_tiny.add_argument(
        "--input",
        default=DEFAULT_ONE_STEP_SGD_TINY_INPUT,
        help="One-step SGD tiny test-vector path.",
    )
    one_step_sgd_tiny.set_defaults(
        func=lambda args: _run_command(args, _verify_one_step_sgd_tiny)
    )

    minibatch_td = verify_subparsers.add_parser(
        "minibatch-td",
        help="Verify a minibatch TD artifact.",
    )
    minibatch_td.add_argument(
        "--artifact",
        default=os.environ.get(
            "MINIBATCH_TD_ARTIFACT_PATH",
            DEFAULT_MINIBATCH_TD_ARTIFACT_PATH,
        ),
        help="Minibatch TD artifact path.",
    )
    minibatch_td.add_argument(
        "--checkpoint",
        default=os.environ.get(
            "MINIBATCH_TD_CHECKPOINT_PATH",
            DEFAULT_MINIBATCH_TD_CHECKPOINT_PATH,
        ),
        help="Checkpoint path.",
    )
    minibatch_td.set_defaults(func=lambda args: _run_command(args, _verify_minibatch_td))

    one_step_update = verify_subparsers.add_parser(
        "one-step-update",
        help="Verify a one-step update artifact.",
    )
    one_step_update.add_argument(
        "--artifact",
        default=os.environ.get(
            "ONE_STEP_ARTIFACT_PATH",
            DEFAULT_ONE_STEP_UPDATE_ARTIFACT_PATH,
        ),
        help="One-step update artifact path.",
    )
    one_step_update.add_argument(
        "--merkle",
        default=os.environ.get(
            "ONE_STEP_MERKLE_PATH",
            DEFAULT_ONE_STEP_UPDATE_MERKLE_PATH,
        ),
        help="Merkle artifact path.",
    )
    one_step_update.add_argument(
        "--checkpoint",
        default=os.environ.get("ONE_STEP_CHECKPOINT_PATH"),
        help="Pre-update checkpoint path. Defaults to artifact notes or verifier default.",
    )
    one_step_update.add_argument(
        "--post-checkpoint",
        default=os.environ.get("ONE_STEP_POST_CHECKPOINT_PATH"),
        help="Post-update checkpoint path. Defaults to artifact notes or verifier default.",
    )
    one_step_update.set_defaults(
        func=lambda args: _run_command(args, _verify_one_step_update)
    )

    short_trace = verify_subparsers.add_parser(
        "short-trace",
        help="Verify a short-trace update artifact.",
    )
    short_trace.add_argument(
        "--artifact",
        default=os.environ.get(
            "SHORT_TRACE_ARTIFACT_PATH",
            DEFAULT_SHORT_TRACE_ARTIFACT_PATH,
        ),
        help="Short-trace artifact path.",
    )
    short_trace.add_argument(
        "--merkle",
        default=os.environ.get("SHORT_TRACE_MERKLE_PATH"),
        help="Merkle artifact path. Defaults to artifact notes when present.",
    )
    short_trace.add_argument(
        "--initial-checkpoint",
        default=os.environ.get("SHORT_TRACE_INITIAL_CHECKPOINT_PATH"),
        help="Initial checkpoint path. Defaults to artifact notes when present.",
    )
    short_trace.add_argument(
        "--final-checkpoint",
        default=os.environ.get("SHORT_TRACE_FINAL_CHECKPOINT_PATH"),
        help="Final checkpoint path. Defaults to artifact notes when present.",
    )
    short_trace.add_argument(
        "--work-dir",
        default=os.environ.get("SHORT_TRACE_WORK_DIR"),
        help="Trace work directory. Defaults to final checkpoint directory when available.",
    )
    short_trace.set_defaults(func=lambda args: _run_command(args, _verify_short_trace))

    return parser

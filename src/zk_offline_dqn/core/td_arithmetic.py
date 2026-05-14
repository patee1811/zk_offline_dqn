"""Compatibility wrapper for fixed-point TD arithmetic.

Phase 1A intentionally does not migrate or reimplement TD arithmetic.  This
module re-exports stable helpers from ``zk_offline_dqn.zk_specs`` so future
core imports can be introduced without changing numeric behavior.
"""

from zk_offline_dqn.zk_specs import (
    SPECS,
    ZKSpecs,
    compute_bootstrapped_fp,
    compute_mse_loss_fp,
    compute_smooth_l1_loss_fp,
    compute_td_target_fp,
    decode_fp,
    encode_fp,
)

FP_SCALE = SPECS.FP_SCALE
GAMMA_FP = SPECS.GAMMA_FP
SMOOTH_L1_BETA_FP = SPECS.SMOOTH_L1_BETA_FP

__all__ = [
    "FP_SCALE",
    "GAMMA_FP",
    "SMOOTH_L1_BETA_FP",
    "SPECS",
    "ZKSpecs",
    "compute_bootstrapped_fp",
    "compute_mse_loss_fp",
    "compute_smooth_l1_loss_fp",
    "compute_td_target_fp",
    "decode_fp",
    "encode_fp",
]

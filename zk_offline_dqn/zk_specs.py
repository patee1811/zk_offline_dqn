from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass(frozen=True)
class ZKSpecs:
    # Fixed-point scale: x_real -> round(x_real * FP_SCALE)
    FP_SCALE: int = 1000

    # CartPole constants
    OBS_DIM: int = 4
    ACTION_DIM: int = 2

    # gamma = 0.99 -> 990 in fixed point
    GAMMA_FP: int = 990

    # Default to SmoothL1 to match the current offline DQN trainer.
    LOSS_TYPE: str = "smooth_l1"

    # beta = 1.0 is the default for torch.nn.SmoothL1Loss().
    SMOOTH_L1_BETA_FP: int = 1000


SPECS = ZKSpecs()


def encode_fp(x: float) -> int:
    return int(round(x * SPECS.FP_SCALE))


def decode_fp(x_fp: int) -> float:
    return x_fp / SPECS.FP_SCALE


def serialize_transition_leaf(
    transition: Dict,
    *,
    obs_dim: Optional[int] = None,
    action_dim: Optional[int] = None,
) -> List[int]:
    obs = transition["obs"]
    action = int(transition["action"])
    reward = transition["reward"]
    next_obs = transition["next_obs"]
    done = int(transition["done"])
    expected_obs_dim = SPECS.OBS_DIM if obs_dim is None else int(obs_dim)
    expected_action_dim = SPECS.ACTION_DIM if action_dim is None else int(action_dim)

    if expected_obs_dim <= 0:
        raise ValueError(f"obs_dim must be positive, got {expected_obs_dim}")
    if expected_action_dim <= 0:
        raise ValueError(f"action_dim must be positive, got {expected_action_dim}")
    if len(obs) != expected_obs_dim:
        raise ValueError(f"obs must have length {expected_obs_dim}, got {len(obs)}")
    if len(next_obs) != expected_obs_dim:
        raise ValueError(
            f"next_obs must have length {expected_obs_dim}, got {len(next_obs)}"
        )
    if action < 0 or action >= expected_action_dim:
        raise ValueError(
            f"action must be in [0, {expected_action_dim - 1}], got {action}"
        )
    if done not in (0, 1, False, True):
        raise ValueError(f"done must be 0/1 or bool, got {done}")

    obs_fp = [encode_fp(float(x)) for x in obs]
    reward_fp = encode_fp(float(reward))
    next_obs_fp = [encode_fp(float(x)) for x in next_obs]
    done_int = int(done)

    return obs_fp + [action] + [reward_fp] + next_obs_fp + [done_int]


def compute_bootstrapped_fp(q_target_max_fp: int) -> int:
    return (SPECS.GAMMA_FP * q_target_max_fp) // SPECS.FP_SCALE


def compute_td_target_fp(reward_fp: int, done: int, q_target_max_fp: int) -> int:
    done_int = int(done)
    if done_int not in (0, 1):
        raise ValueError(f"done must be 0 or 1, got {done}")

    bootstrapped_fp = compute_bootstrapped_fp(q_target_max_fp)
    return reward_fp + (1 - done_int) * bootstrapped_fp


# Keep MSE for temporary backward compatibility with older scripts.
def compute_mse_loss_fp(q_online_fp: int, target_fp: int) -> int:
    diff = q_online_fp - target_fp
    return diff * diff


def compute_smooth_l1_loss_fp(q_online_fp: int, target_fp: int) -> int:
    """
    Fixed-point SmoothL1Loss with beta = 1.0.

    If |delta| < beta:
        loss = 0.5 * delta^2 / beta
    Otherwise:
        loss = |delta| - 0.5 * beta

    Inputs and outputs are fixed-point integers.
    """
    delta_fp = q_online_fp - target_fp
    abs_delta_fp = abs(delta_fp)
    beta_fp = SPECS.SMOOTH_L1_BETA_FP

    if abs_delta_fp < beta_fp:
        return (abs_delta_fp * abs_delta_fp) // (2 * beta_fp)

    return abs_delta_fp - (beta_fp // 2)

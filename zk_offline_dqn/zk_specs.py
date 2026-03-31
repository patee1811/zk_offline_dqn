from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class ZKSpecs:
    # Fixed-point scale: x_real -> round(x_real * FP_SCALE)
    FP_SCALE: int = 1000

    # CartPole constants
    OBS_DIM: int = 4
    ACTION_DIM: int = 2

    # gamma = 0.99 -> 990 in fixed point
    GAMMA_FP: int = 990

    # MVP dùng MSE cho dễ verify/circuit
    LOSS_TYPE: str = "mse"


SPECS = ZKSpecs()


def encode_fp(x: float) -> int:
    """Encode a real number into fixed-point integer."""
    return int(round(x * SPECS.FP_SCALE))


def decode_fp(x_fp: int) -> float:
    """Decode fixed-point integer back to float."""
    return x_fp / SPECS.FP_SCALE


def serialize_transition_leaf(transition: Dict) -> List[int]:
    """
    Canonical leaf format for one CartPole transition.

    Output order is FIXED and must never change:
      [obs0, obs1, obs2, obs3,
       action,
       reward,
       next_obs0, next_obs1, next_obs2, next_obs3,
       done]
    All observation/reward values are fixed-point integers.
    """
    obs = transition["obs"]
    action = int(transition["action"])
    reward = transition["reward"]
    next_obs = transition["next_obs"]
    done = int(transition["done"])

    if len(obs) != SPECS.OBS_DIM:
        raise ValueError(f"obs must have length {SPECS.OBS_DIM}, got {len(obs)}")
    if len(next_obs) != SPECS.OBS_DIM:
        raise ValueError(
            f"next_obs must have length {SPECS.OBS_DIM}, got {len(next_obs)}"
        )
    if action < 0 or action >= SPECS.ACTION_DIM:
        raise ValueError(f"action must be in [0, {SPECS.ACTION_DIM - 1}], got {action}")
    if done not in (0, 1, False, True):
        raise ValueError(f"done must be 0/1 or bool, got {done}")

    obs_fp = [encode_fp(float(x)) for x in obs]
    reward_fp = encode_fp(float(reward))
    next_obs_fp = [encode_fp(float(x)) for x in next_obs]
    done_int = int(done)

    leaf = obs_fp + [action] + [reward_fp] + next_obs_fp + [done_int]
    return leaf


def compute_bootstrapped_fp(q_target_max_fp: int) -> int:
    """
    Compute gamma * q_target_max in fixed-point.
    Using truncation/floor by integer division for consistency.
    """
    return (SPECS.GAMMA_FP * q_target_max_fp) // SPECS.FP_SCALE


def compute_td_target_fp(reward_fp: int, done: int, q_target_max_fp: int) -> int:
    """
    y = r + (1 - done) * gamma * q_target_max
    All values are fixed-point integers.
    """
    done_int = int(done)
    if done_int not in (0, 1):
        raise ValueError(f"done must be 0 or 1, got {done}")

    bootstrapped_fp = compute_bootstrapped_fp(q_target_max_fp)
    return reward_fp + (1 - done_int) * bootstrapped_fp


def compute_mse_loss_fp(q_online_fp: int, target_fp: int) -> int:
    """
    MSE per-sample loss in integer arithmetic:
      loss = (q - target)^2
    """
    delta_fp = q_online_fp - target_fp
    return delta_fp * delta_fp


if __name__ == "__main__":
    print("=== ZK SPECS CHECK ===")
    print("FP_SCALE =", SPECS.FP_SCALE)
    print("GAMMA_FP =", SPECS.GAMMA_FP)
    print("LOSS_TYPE =", SPECS.LOSS_TYPE)

    sample_transition = {
        "obs": [0.1, -0.2, 0.03, 0.4],
        "action": 1,
        "reward": 1.0,
        "next_obs": [0.11, -0.18, 0.05, 0.38],
        "done": 0,
    }

    leaf = serialize_transition_leaf(sample_transition)
    print("Serialized leaf =", leaf)

    q_online_fp = encode_fp(1.234)
    q_target_max_fp = encode_fp(1.500)
    reward_fp = encode_fp(1.0)

    target_fp = compute_td_target_fp(reward_fp, 0, q_target_max_fp)
    loss_fp = compute_mse_loss_fp(q_online_fp, target_fp)

    print("q_online_fp =", q_online_fp)
    print("q_target_max_fp =", q_target_max_fp)
    print("target_fp =", target_fp, "->", decode_fp(target_fp))
    print("loss_fp =", loss_fp)
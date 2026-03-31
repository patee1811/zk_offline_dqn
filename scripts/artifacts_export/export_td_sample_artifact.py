import json

from zk_offline_dqn.zk_specs import (
    encode_fp,
    compute_td_target_fp,
    compute_mse_loss_fp,
)


MEMBERSHIP_ARTIFACT_PATH = "artifacts/sample_transition_membership.json"
OUTPUT_PATH = "artifacts/sample_td_artifact.json"

# Tạm thời gán tay 2 witness Q-values để test TD arithmetic
Q_ONLINE_REAL = 1.234
Q_TARGET_MAX_REAL = 1.500


def main():
    with open(MEMBERSHIP_ARTIFACT_PATH, "r", encoding="utf-8") as f:
        membership = json.load(f)

    transition = membership["transition"]

    reward_fp = encode_fp(float(transition["reward"]))
    done_int = int(transition["done"])

    q_online_fp = encode_fp(Q_ONLINE_REAL)
    q_target_max_fp = encode_fp(Q_TARGET_MAX_REAL)

    target_fp = compute_td_target_fp(
        reward_fp=reward_fp,
        done=done_int,
        q_target_max_fp=q_target_max_fp,
    )

    loss_fp = compute_mse_loss_fp(
        q_online_fp=q_online_fp,
        target_fp=target_fp,
    )

    artifact = {
        "public": {
            "dataset_root": membership["dataset_root"],
            "loss_type": "mse",
        },
        "transition_membership": membership,
        "td_witness": {
            "q_online_fp": q_online_fp,
            "q_target_max_fp": q_target_max_fp,
            "target_fp": target_fp,
            "loss_fp": loss_fp,
        },
        "notes": {
            "q_online_real_for_debug": Q_ONLINE_REAL,
            "q_target_max_real_for_debug": Q_TARGET_MAX_REAL,
            "purpose": "single-sample TD arithmetic test before batch-level proof",
        },
    }

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(artifact, f, indent=2)

    print("=== TD SAMPLE ARTIFACT EXPORTED ===")
    print("output_path =", OUTPUT_PATH)
    print("dataset_root =", artifact["public"]["dataset_root"])
    print("loss_type =", artifact["public"]["loss_type"])
    print("reward_fp =", reward_fp)
    print("done =", done_int)
    print("q_online_fp =", q_online_fp)
    print("q_target_max_fp =", q_target_max_fp)
    print("target_fp =", target_fp)
    print("loss_fp =", loss_fp)


if __name__ == "__main__":
    main()
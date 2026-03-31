import pickle
from typing import Dict, Iterator

from zk_offline_dqn.zk_specs import serialize_transition_leaf


DATASET_PATH = "data/cartpole_dqn_eps010_transitions.pkl"


def load_dataset(path):
    with open(path, "rb") as f:
        return pickle.load(f)


def iter_transitions(data) -> Iterator[Dict]:
    required_keys = ["obs", "actions", "rewards", "next_obs", "dones"]

    if not (isinstance(data, dict) and all(k in data for k in required_keys)):
        raise ValueError(
            "Expected columnar dict with keys "
            "['obs', 'actions', 'rewards', 'next_obs', 'dones']."
        )

    n = len(data["obs"])
    if not all(len(data[k]) == n for k in required_keys):
        raise ValueError("Column lengths do not match.")

    for i in range(n):
        yield {
            "obs": data["obs"][i],
            "action": data["actions"][i],
            "reward": data["rewards"][i],
            "next_obs": data["next_obs"][i],
            "done": data["dones"][i],
        }


def main():
    data = load_dataset(DATASET_PATH)

    count = 0
    first_5_leaves = []
    done_count = 0
    action_counts = {}

    for transition in iter_transitions(data):
        leaf = serialize_transition_leaf(transition)

        if count < 5:
            first_5_leaves.append(leaf)

        action = int(transition["action"])
        done = int(transition["done"])

        action_counts[action] = action_counts.get(action, 0) + 1
        done_count += done
        count += 1

    print("=== DATASET SERIALIZATION CHECK ===")
    print("num_transitions =", count)
    print("done_count =", done_count)
    print("done_ratio =", done_count / count)
    print("action_counts =", action_counts)

    print("\n=== FIRST 5 LEAVES ===")
    for i, leaf in enumerate(first_5_leaves):
        print(f"leaf[{i}] =", leaf)


if __name__ == "__main__":
    main()
import pickle
from pprint import pprint

from zk_offline_dqn.zk_specs import serialize_transition_leaf


DATASET_PATH = "data/cartpole_dqn_eps010_transitions.pkl"


def load_dataset(path):
    with open(path, "rb") as f:
        data = pickle.load(f)
    return data


def get_first_transition(data):
    # Trường hợp 1: file là list trực tiếp
    if isinstance(data, list):
        if len(data) == 0:
            raise ValueError("Dataset is an empty list.")
        return data[0]

    # Trường hợp 2: file là dict chứa list transitions
    if isinstance(data, dict) and "transitions" in data:
        transitions = data["transitions"]
        if len(transitions) == 0:
            raise ValueError("data['transitions'] is empty.")
        return transitions[0]

    # Trường hợp 3: flattened columnar format
    required_keys = ["obs", "actions", "rewards", "next_obs", "dones"]
    if isinstance(data, dict) and all(k in data for k in required_keys):
        n = len(data["obs"])
        if n == 0:
            raise ValueError("Columnar dataset is empty.")

        return {
            "obs": data["obs"][0],
            "action": data["actions"][0],
            "reward": data["rewards"][0],
            "next_obs": data["next_obs"][0],
            "done": data["dones"][0],
        }

    raise ValueError(
        f"Unsupported dataset format: type={type(data)}. "
        "Expected list, dict with key 'transitions', "
        "or columnar dict with keys "
        "['obs', 'actions', 'rewards', 'next_obs', 'dones']."
    )


def main():
    data = load_dataset(DATASET_PATH)

    print("=== DATASET TOP-LEVEL INFO ===")
    print("type(data) =", type(data))

    if isinstance(data, list):
        print("len(data) =", len(data))
    elif isinstance(data, dict):
        print("dict keys =", list(data.keys()))
        for k, v in data.items():
            try:
                print(f"len({k}) = {len(v)}")
            except TypeError:
                print(f"len({k}) = <not available>")

    transition = get_first_transition(data)

    print("\n=== FIRST TRANSITION RAW ===")
    pprint(transition)

    if not isinstance(transition, dict):
        raise ValueError(
            f"Expected one transition to be a dict, got {type(transition)}"
        )

    print("\ntransition keys =", list(transition.keys()))

    leaf = serialize_transition_leaf(transition)

    print("\n=== SERIALIZED LEAF ===")
    print(leaf)
    print("leaf length =", len(leaf))


if __name__ == "__main__":
    main()
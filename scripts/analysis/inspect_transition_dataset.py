import pickle

DATA_PATH = "data/cartpole_dqn_eps010_transitions.pkl"

with open(DATA_PATH, "rb") as f:
    dataset = pickle.load(f)

print("Keys:", dataset.keys())
print("obs shape:", dataset["obs"].shape)
print("actions shape:", dataset["actions"].shape)
print("rewards shape:", dataset["rewards"].shape)
print("next_obs shape:", dataset["next_obs"].shape)
print("dones shape:", dataset["dones"].shape)

print("First 5 actions:", dataset["actions"][:5])
print("First 5 rewards:", dataset["rewards"][:5])
print("First 5 dones:", dataset["dones"][:5])
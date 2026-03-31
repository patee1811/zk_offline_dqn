import pickle

DATA_PATH = "data/cartpole_dqn_eps010_episodes.pkl"

with open(DATA_PATH, "rb") as f:
    episodes = pickle.load(f)

print(f"Number of episodes: {len(episodes)}")

first = episodes[0]
print("Keys:", first.keys())
print("obs shape:", first["obs"].shape)
print("actions shape:", first["actions"].shape)
print("rewards shape:", first["rewards"].shape)
print("next_obs shape:", first["next_obs"].shape)
print("dones shape:", first["dones"].shape)

print("First 3 actions:", first["actions"][:3])
print("First 3 rewards:", first["rewards"][:3])
print("First 3 dones:", first["dones"][:3])
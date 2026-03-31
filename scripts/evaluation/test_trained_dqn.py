import gymnasium as gym
from stable_baselines3 import DQN


def main():
    env = gym.make("CartPole-v1")
    model = DQN.load("models/dqn_cartpole_behavior", env=env)

    episode_returns = []

    for ep in range(5):
        obs, info = env.reset(seed=100 + ep)
        done = False
        total_reward = 0.0

        while not done:
            action, _ = model.predict(obs, deterministic=True)
            obs, reward, terminated, truncated, info = env.step(action)
            done = terminated or truncated
            total_reward += reward

        episode_returns.append(total_reward)
        print(f"Episode {ep + 1}: return={total_reward}")

    env.close()
    print("Average return over 5 test episodes:", sum(episode_returns) / len(episode_returns))


if __name__ == "__main__":
    main()
import gymnasium as gym

def main():
    env = gym.make("CartPole-v1")
    obs, info = env.reset(seed=42)

    total_reward = 0.0
    step_count = 0

    for _ in range(200):
        action = env.action_space.sample()
        next_obs, reward, terminated, truncated, info = env.step(action)
        total_reward += reward
        step_count += 1
        obs = next_obs

        if terminated or truncated:
            break

    env.close()
    print(f"Smoke test OK | steps={step_count} | total_reward={total_reward}")

if __name__ == "__main__":
    main()
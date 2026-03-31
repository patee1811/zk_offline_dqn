from pathlib import Path

import gymnasium as gym
from stable_baselines3 import DQN
from stable_baselines3.common.evaluation import evaluate_policy


def main():
    models_dir = Path("models")
    models_dir.mkdir(parents=True, exist_ok=True)

    env = gym.make("CartPole-v1")

    model = DQN(
        policy="MlpPolicy",
        env=env,
        learning_rate=1e-3,
        buffer_size=10000,
        learning_starts=1000,
        batch_size=64,
        gamma=0.99,
        train_freq=4,
        target_update_interval=500,
        exploration_fraction=0.2,
        exploration_final_eps=0.05,
        verbose=1,
        seed=42,
    )

    model.learn(total_timesteps=20000, progress_bar=False)

    model_path = models_dir / "dqn_cartpole_behavior"
    model.save(str(model_path))

    mean_reward, std_reward = evaluate_policy(
        model,
        env,
        n_eval_episodes=20,
        deterministic=True,
    )

    env.close()

    print(f"Model saved to: {model_path}.zip")
    print(f"Evaluation mean_reward={mean_reward:.2f}, std_reward={std_reward:.2f}")


if __name__ == "__main__":
    main()
from pathlib import Path
import argparse

import pandas as pd
import matplotlib.pyplot as plt


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--log", type=str, required=True)
    args = parser.parse_args()

    log_path = Path(args.log)
    df = pd.read_csv(log_path)

    print("Log path:", log_path)
    print("Columns:", list(df.columns))
    print(df.head(10))
    print()
    print(df.tail(10))
    print()
    print(df.describe(include="all"))

    best_idx = df["eval_mean_return"].idxmax()
    best_row = df.loc[best_idx]
    print("\nBest row:")
    print(best_row)

    out_dir = log_path.parent
    stem = log_path.stem

    for col in ["mean_total_loss", "mean_td_loss", "mean_cql_penalty", "eval_mean_return", "eval_std_return"]:
        if "step" in df.columns and col in df.columns:
            plt.figure(figsize=(8, 5))
            plt.plot(df["step"], df[col])
            plt.xlabel("step")
            plt.ylabel(col)
            plt.title(f"CQL {col} vs step")
            plt.grid(True)
            plt.tight_layout()
            plt.savefig(out_dir / f"{stem}_{col}.png", dpi=150)
            plt.close()

    print("\nSaved plots next to the log file.")


if __name__ == "__main__":
    main()
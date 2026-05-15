#!/usr/bin/env bash
set -u

echo "=== SP1 KAGGLE SETUP CHECK ==="
echo "cwd = $(pwd)"
echo "RUN_SP1_EXECUTE = ${RUN_SP1_EXECUTE:-0}"
echo "RUN_SP1_PROVE = ${RUN_SP1_PROVE:-0}"

check_internet() {
  python - <<'PY'
import socket
try:
    socket.create_connection(("example.com", 80), timeout=5).close()
    print("internet_available = True")
except OSError as exc:
    print(f"internet_available = False ({exc})")
PY
}

check_internet

if ! command -v cargo >/dev/null 2>&1 || ! command -v rustc >/dev/null 2>&1; then
  echo "Rust toolchain missing; installing rustup."
  curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
fi

if [ -f "$HOME/.cargo/env" ]; then
  # shellcheck disable=SC1091
  source "$HOME/.cargo/env"
fi

echo "rustc_version = $(rustc --version 2>/dev/null || true)"
echo "cargo_version = $(cargo --version 2>/dev/null || true)"

if ! cargo prove --version >/dev/null 2>&1 || ! command -v sp1up >/dev/null 2>&1; then
  echo "SP1 tooling missing; running the Succinct SP1 installer."
  curl -L https://sp1up.succinct.xyz | bash
fi

if [ -f "$HOME/.sp1/env" ]; then
  # shellcheck disable=SC1091
  source "$HOME/.sp1/env"
fi
if [ -f "$HOME/.cargo/env" ]; then
  # shellcheck disable=SC1091
  source "$HOME/.cargo/env"
fi

echo "cargo_prove_version = $(cargo prove --version 2>/dev/null || true)"
echo "sp1up_version = $(sp1up --version 2>/dev/null || true)"

if [ -d "zk_backend/td_mvp/sp1" ]; then
  cd zk_backend/td_mvp/sp1 || exit 0
  if [ "${RUN_SP1_EXECUTE:-0}" = "1" ]; then
    cargo test
    cargo run --release -p td-mvp-host -- --execute
  else
    echo "SP1 execute skipped; set RUN_SP1_EXECUTE=1 to run cargo test and execute."
  fi
  if [ "${RUN_SP1_PROVE:-0}" = "1" ]; then
    cargo run --release -p td-mvp-host -- --prove
  else
    echo "SP1 proof skipped; set RUN_SP1_PROVE=1 to prove."
  fi
else
  echo "SP1 workspace not found at zk_backend/td_mvp/sp1."
fi

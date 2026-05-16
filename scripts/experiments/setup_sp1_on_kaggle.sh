#!/usr/bin/env bash
set -u

echo "=== SP1 KAGGLE SETUP CHECK ==="
echo "cwd = $(pwd)"
echo "RUN_SP1_EXECUTE = ${RUN_SP1_EXECUTE:-0}"
echo "RUN_SP1_PROVE = ${RUN_SP1_PROVE:-0}"
echo "path_before = $PATH"
SETUP_STATUS="started"
RUSTUP_STATUS="not_needed"
SP1UP_STATUS="not_needed"
APT_STATUS="not_needed"
INTERNET_AVAILABLE="unknown"

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
if python - <<'PY'
import socket, sys
try:
    socket.create_connection(("example.com", 80), timeout=5).close()
except OSError:
    sys.exit(1)
PY
then
  INTERNET_AVAILABLE="true"
else
  INTERNET_AVAILABLE="false"
fi

if [ "$INTERNET_AVAILABLE" = "true" ] && command -v apt-get >/dev/null 2>&1; then
  echo "Installing native build prerequisites with apt-get."
  SUDO=""
  if command -v sudo >/dev/null 2>&1; then
    SUDO="sudo"
  fi
  if $SUDO apt-get update && $SUDO apt-get install -y \
    build-essential \
    pkg-config \
    libssl-dev \
    protobuf-compiler \
    libprotobuf-dev \
    curl \
    git \
    clang \
    lld; then
    APT_STATUS="installed"
  else
    APT_STATUS="failed"
  fi
elif [ "$INTERNET_AVAILABLE" != "true" ]; then
  APT_STATUS="skipped_no_internet"
fi

if command -v protoc >/dev/null 2>&1; then
  export PROTOC="$(command -v protoc)"
  if [ -d "/usr/include" ]; then
    export PROTOC_INCLUDE="/usr/include"
  fi
fi

if ! command -v cargo >/dev/null 2>&1 || ! command -v rustc >/dev/null 2>&1; then
  echo "Rust toolchain missing; installing rustup."
  if curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y; then
    RUSTUP_STATUS="installed"
  else
    RUSTUP_STATUS="failed"
  fi
fi

if [ -f "$HOME/.cargo/env" ]; then
  # shellcheck disable=SC1091
  source "$HOME/.cargo/env"
fi
export PATH="$HOME/.cargo/bin:$HOME/.sp1/bin:$PATH"

RUSTC_VERSION="$(rustc --version 2>/dev/null || true)"
CARGO_VERSION="$(cargo --version 2>/dev/null || true)"
PROTOC_VERSION="$(protoc --version 2>/dev/null || true)"
echo "rustc_version = $RUSTC_VERSION"
echo "cargo_version = $CARGO_VERSION"
echo "protoc_version = $PROTOC_VERSION"

if [ "$INTERNET_AVAILABLE" = "true" ] && { ! cargo prove --version >/dev/null 2>&1 || ! command -v sp1up >/dev/null 2>&1; }; then
  echo "SP1 tooling missing; running the Succinct SP1 installer."
  if curl -L https://sp1up.succinct.xyz | bash; then
    SP1UP_STATUS="installer_completed"
  else
    SP1UP_STATUS="installer_failed"
  fi
elif [ "$INTERNET_AVAILABLE" != "true" ]; then
  SP1UP_STATUS="skipped_no_internet"
fi

if [ -f "$HOME/.sp1/env" ]; then
  # shellcheck disable=SC1091
  source "$HOME/.sp1/env"
fi
if [ -f "$HOME/.cargo/env" ]; then
  # shellcheck disable=SC1091
  source "$HOME/.cargo/env"
fi
export PATH="$HOME/.cargo/bin:$HOME/.sp1/bin:$PATH"

if command -v sp1up >/dev/null 2>&1 && ! cargo prove --version >/dev/null 2>&1; then
  echo "cargo prove missing after installer; running sp1up to install SP1 toolchain."
  if sp1up -v 6.1.0 || sp1up; then
    SP1UP_STATUS="${SP1UP_STATUS}_toolchain_installed"
  else
    SP1UP_STATUS="${SP1UP_STATUS}_toolchain_failed"
  fi
fi

CARGO_PROVE_VERSION="$(cargo prove --version 2>/dev/null || true)"
SP1UP_VERSION="$(sp1up --help 2>/dev/null | head -n 1 || true)"
echo "cargo_prove_version = $CARGO_PROVE_VERSION"
echo "sp1up_version = $SP1UP_VERSION"
echo "protoc_path = ${PROTOC:-}"
echo "protoc_include = ${PROTOC_INCLUDE:-}"
echo "path_after = $PATH"

CARGO_TEST_STATUS="not_run"
SP1_EXECUTE_STATUS="not_run"
SP1_PROVE_STATUS="not_run"

if [ -d "zk_backend/td_mvp/sp1" ]; then
  cd zk_backend/td_mvp/sp1 || exit 0
  if [ "${RUN_SP1_EXECUTE:-0}" = "1" ]; then
    if cargo test; then
      CARGO_TEST_STATUS="passed"
    else
      CARGO_TEST_STATUS="failed"
    fi
    if cargo run --release -p td-mvp-host -- --execute; then
      SP1_EXECUTE_STATUS="passed"
    else
      SP1_EXECUTE_STATUS="failed"
    fi
  else
    echo "SP1 execute skipped; set RUN_SP1_EXECUTE=1 to run cargo test and execute."
    SP1_EXECUTE_STATUS="skipped"
  fi
  if [ "${RUN_SP1_PROVE:-0}" = "1" ]; then
    if cargo run --release -p td-mvp-host -- --prove; then
      SP1_PROVE_STATUS="passed"
    else
      SP1_PROVE_STATUS="failed"
    fi
  else
    echo "SP1 proof skipped; set RUN_SP1_PROVE=1 to prove."
    SP1_PROVE_STATUS="skipped"
  fi
  cd - >/dev/null || true
else
  echo "SP1 workspace not found at zk_backend/td_mvp/sp1."
fi

SETUP_STATUS="completed"
mkdir -p artifacts/reports
python - <<PY
import json
from pathlib import Path
summary = {
    "setup_status": "$SETUP_STATUS",
    "internet_available": "$INTERNET_AVAILABLE",
    "apt_status": "$APT_STATUS",
    "rustup_status": "$RUSTUP_STATUS",
    "sp1up_status": "$SP1UP_STATUS",
    "rustc_version": "$RUSTC_VERSION",
    "cargo_version": "$CARGO_VERSION",
    "protoc_version": "$PROTOC_VERSION",
    "protoc_path": "${PROTOC:-}",
    "protoc_include": "${PROTOC_INCLUDE:-}",
    "cargo_prove_version": "$CARGO_PROVE_VERSION",
    "sp1up_version": "$SP1UP_VERSION",
    "cargo_test_status": "$CARGO_TEST_STATUS",
    "sp1_execute_status": "$SP1_EXECUTE_STATUS",
    "sp1_prove_status": "$SP1_PROVE_STATUS",
}
path = Path("artifacts/reports/kaggle_sp1_setup_summary.json")
path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
print("setup_summary_path =", path.as_posix())
PY

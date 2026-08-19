#!/usr/bin/env bash
#
# Idempotent one-shot setup for example_agents (macOS / Linux / WSL).
# Safe to re-run: every step checks before it acts.
#
# Usage:  ./scripts/bootstrap.sh
set -euo pipefail

REQUIRED_PYTHON="3.12"
UV_INSTALL_URL="https://astral.sh/uv/install.sh"

BOLD=$(printf '\033[1m'); GREEN=$(printf '\033[32m'); YELLOW=$(printf '\033[33m')
RED=$(printf '\033[31m'); RESET=$(printf '\033[0m')

step() { echo "${BOLD}==> $*${RESET}"; }
ok()   { echo "  ${GREEN}OK${RESET}    $*"; }
warn() { echo "  ${YELLOW}WARN${RESET}  $*"; }
fail() { echo "  ${RED}FAIL${RESET}  $*"; }

cd "$(dirname "$0")/.."
REPO_ROOT=$(pwd)
step "Repository root: $REPO_ROOT"

# --- 1. curl -------------------------------------------------------------
step "Checking curl"
if command -v curl >/dev/null 2>&1; then
  ok "curl found"
else
  fail "curl is required but not installed."
  echo "        macOS: install the Xcode command line tools with 'xcode-select --install'"
  echo "        Debian/Ubuntu/WSL: 'sudo apt-get update && sudo apt-get install -y curl'"
  exit 1
fi

# --- 2. uv (this also gives us Python) -----------------------------------
step "Checking uv (Python toolchain and dependency manager)"
if ! command -v uv >/dev/null 2>&1; then
  warn "uv not found - installing from $UV_INSTALL_URL"
  curl -LsSf "$UV_INSTALL_URL" | sh
  # The installer drops uv in one of these; add whichever exists to this shell.
  for candidate in "$HOME/.local/bin" "$HOME/.cargo/bin"; do
    [ -x "$candidate/uv" ] && export PATH="$candidate:$PATH"
  done
fi

if command -v uv >/dev/null 2>&1; then
  ok "uv $(uv --version | awk '{print $2}') at $(command -v uv)"
else
  fail "uv installed but not on PATH for this shell."
  echo "        Add this to ~/.zshrc or ~/.bashrc, then open a new terminal:"
  echo "          export PATH=\"\$HOME/.local/bin:\$PATH\""
  exit 1
fi

# --- 3. Python ------------------------------------------------------------
# uv manages its own interpreters, so a system Python is nice-to-have, not required.
step "Checking Python >= $REQUIRED_PYTHON"
if uv python find ">=$REQUIRED_PYTHON" >/dev/null 2>&1; then
  ok "Python $(uv run --no-project python -c 'import sys; print(".".join(map(str, sys.version_info[:3])))' 2>/dev/null || echo "$REQUIRED_PYTHON+") available"
else
  warn "No Python >= $REQUIRED_PYTHON found - letting uv download one"
  uv python install "$REQUIRED_PYTHON"
  ok "Python $REQUIRED_PYTHON installed by uv"
fi

# --- 4. Dependencies ------------------------------------------------------
step "Installing project dependencies into .venv (uv sync)"
uv sync
ok "Dependencies installed"

# --- 5. .env --------------------------------------------------------------
step "Checking .env"
if [ -f .env ]; then
  ok ".env already exists (left untouched)"
else
  cp .env.example .env
  ok "Created .env from .env.example"
  warn "Edit .env and set GOOGLE_CLOUD_PROJECT before running an agent."
fi

# --- 6. pre-commit (only meaningful inside a git checkout) -----------------
step "Checking developer git hooks"
if [ -d .git ] && command -v git >/dev/null 2>&1; then
  uv pip install --quiet pre-commit
  uv run pre-commit install >/dev/null
  ok "pre-commit hooks installed"
else
  warn "Not a git checkout (or git missing) - skipping pre-commit hooks."
  echo "        This is expected if you downloaded the repo as an archive."
  echo "        You can still run the agents; you just cannot commit from here."
fi

# --- 7. gcloud ------------------------------------------------------------
step "Checking Google Cloud CLI"
if command -v gcloud >/dev/null 2>&1; then
  ok "gcloud found at $(command -v gcloud)"
else
  warn "gcloud not installed. The agents call Vertex AI and need it."
  echo "        Install: https://cloud.google.com/sdk/docs/install"
  echo "        macOS with Homebrew: brew install --cask google-cloud-sdk"
fi

echo
step "Bootstrap finished. Next: ./scripts/doctor.sh"

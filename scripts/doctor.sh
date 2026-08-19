#!/usr/bin/env bash
#
# Pre-flight check: tells you exactly what is still missing before an agent can run.
# Exits non-zero if any blocking problem is found.
#
# Usage:  ./scripts/doctor.sh
set -uo pipefail

BOLD=$(printf '\033[1m'); GREEN=$(printf '\033[32m'); YELLOW=$(printf '\033[33m')
RED=$(printf '\033[31m'); RESET=$(printf '\033[0m')

PROBLEMS=0

ok()    { echo "  ${GREEN}OK${RESET}    $*"; }
warn()  { echo "  ${YELLOW}WARN${RESET}  $*"; }
bad()   { echo "  ${RED}FAIL${RESET}  $*"; PROBLEMS=$((PROBLEMS + 1)); }
hint()  { echo "        $*"; }

cd "$(dirname "$0")/.."
echo "${BOLD}example_agents doctor${RESET}"
echo

# --- Toolchain ------------------------------------------------------------
echo "${BOLD}Toolchain${RESET}"
if command -v uv >/dev/null 2>&1; then
  ok "uv $(uv --version | awk '{print $2}')"
else
  bad "uv not installed"
  hint "Run ./scripts/bootstrap.sh"
fi

if [ -d .venv ]; then
  ok "virtualenv .venv exists"
else
  bad ".venv missing - dependencies were never installed"
  hint "Run ./scripts/bootstrap.sh"
fi

if uv run python -c "import google.adk" >/dev/null 2>&1; then
  ok "google-adk importable"
else
  bad "google-adk not installed in .venv"
  hint "Run: uv sync"
fi

# --- Configuration --------------------------------------------------------
echo
echo "${BOLD}Configuration${RESET}"
if [ -f .env ]; then
  ok ".env present"
  # shellcheck disable=SC1091
  set -a; . ./.env >/dev/null 2>&1; set +a

  # Which backend is this .env configured for?
  case "$(printf '%s' "${GOOGLE_GENAI_USE_VERTEXAI:-TRUE}" | tr '[:lower:]' '[:upper:]')" in
    TRUE) BACKEND="vertexai" ;;
    *)    BACKEND="aistudio" ;;
  esac

  if [ "$BACKEND" = "vertexai" ]; then
    ok "backend: Vertex AI (Google Cloud project)"

    if [ -z "${GOOGLE_CLOUD_PROJECT:-}" ] || [ "${GOOGLE_CLOUD_PROJECT}" = "your-gcp-project" ]; then
      bad "GOOGLE_CLOUD_PROJECT is unset or still the placeholder"
      hint "Edit .env and set GOOGLE_CLOUD_PROJECT=<your-project-id>"
      hint "List projects you can see: gcloud projects list"
      hint "No Google Cloud account? Use Option B in .env.example instead."
    else
      ok "GOOGLE_CLOUD_PROJECT=${GOOGLE_CLOUD_PROJECT}"
    fi

    ok "GOOGLE_CLOUD_LOCATION=${GOOGLE_CLOUD_LOCATION:-<unset, agents default to europe-west1>}"
  else
    ok "backend: Google AI Studio API key (no Google Cloud account needed)"

    if [ -z "${GOOGLE_API_KEY:-}" ] || [ "${GOOGLE_API_KEY}" = "your-ai-studio-api-key" ]; then
      bad "GOOGLE_API_KEY is unset or still the placeholder"
      hint "Get a key at https://aistudio.google.com/apikey, then set it in .env"
    else
      ok "GOOGLE_API_KEY is set (${#GOOGLE_API_KEY} characters)"
    fi
  fi

  if [ -z "${MODEL:-}" ]; then
    bad "MODEL is unset"
    hint "Edit .env and set MODEL=gemini-2.5-flash"
  else
    ok "MODEL=${MODEL}"
  fi
else
  bad ".env missing"
  hint "Run: cp .env.example .env  (then set GOOGLE_CLOUD_PROJECT)"
fi

# --- Google Cloud ---------------------------------------------------------
# Only relevant for the Vertex AI backend; an API key needs none of this.
echo
echo "${BOLD}Google Cloud${RESET}"
if [ "${BACKEND:-vertexai}" = "aistudio" ]; then
  ok "not required - this .env uses a Google AI Studio API key"
elif command -v gcloud >/dev/null 2>&1; then
  ok "gcloud installed"

  if gcloud auth list --filter=status:ACTIVE --format="value(account)" 2>/dev/null | grep -q .; then
    ok "logged in as $(gcloud auth list --filter=status:ACTIVE --format='value(account)' 2>/dev/null | head -1)"
  else
    bad "no active gcloud account"
    hint "Run: gcloud auth login"
  fi

  if gcloud auth application-default print-access-token >/dev/null 2>&1; then
    ok "application default credentials present"
  else
    bad "no application default credentials (ADC) - agents cannot call Vertex AI"
    hint "Run: gcloud auth application-default login"
  fi
else
  bad "gcloud not installed"
  hint "Install: https://cloud.google.com/sdk/docs/install"
fi

# --- Live model check -----------------------------------------------------
# Configuration can look perfect and still fail. The usual cause is a model that
# is not served in the configured region. One tiny call settles it.
echo
echo "${BOLD}Live model check${RESET}"
if [ "$PROBLEMS" -ne 0 ]; then
  warn "skipped - fix the problems above first"
elif [ "${SKIP_LIVE:-0}" = "1" ]; then
  warn "skipped (SKIP_LIVE=1)"
elif ! command -v uv >/dev/null 2>&1; then
  warn "skipped - uv not available"
else
  LIVE=$(uv run python - <<'PYEOF' 2>/dev/null
import os

from dotenv import load_dotenv

# Explicit path: find_dotenv() cannot walk the stack when read from stdin.
load_dotenv(dotenv_path=".env")

from google import genai

model = os.getenv("MODEL", "gemini-2.5-flash")
use_vertex = os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "TRUE").strip().upper() == "TRUE"

try:
    if use_vertex:
        client = genai.Client(
            vertexai=True,
            project=os.environ["GOOGLE_CLOUD_PROJECT"],
            location=os.getenv("GOOGLE_CLOUD_LOCATION", "europe-west1"),
        )
    else:
        client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])
    client.models.generate_content(model=model, contents="ping")
    print("OK")
except Exception as exc:
    print("ERR " + str(exc).replace("\n", " ")[:300])
PYEOF
)

  case "$LIVE" in
    OK*)
      ok "$MODEL responded from ${GOOGLE_CLOUD_LOCATION:-the API-key endpoint}"
      ;;
    *404*)
      bad "model '$MODEL' is not available in region '${GOOGLE_CLOUD_LOCATION:-unset}'"
      hint "Pick a region that serves it, e.g. GOOGLE_CLOUD_LOCATION=europe-west1"
      hint "Remember to set CLOUD_ML_REGION to the same value."
      hint "Regions: https://cloud.google.com/vertex-ai/generative-ai/docs/learn/locations"
      ;;
    *"API key not valid"*)
      bad "GOOGLE_API_KEY was rejected"
      hint "Re-copy the key from https://aistudio.google.com/apikey"
      ;;
    *403*|*PERMISSION_DENIED*)
      bad "permission denied calling the model"
      hint "Enable the API: gcloud services enable aiplatform.googleapis.com --project=${GOOGLE_CLOUD_PROJECT:-<id>}"
      ;;
    ERR*)
      bad "model call failed: ${LIVE#ERR }"
      ;;
    *)
      warn "could not complete the live check (offline?)"
      ;;
  esac
fi

# --- Agents ---------------------------------------------------------------
echo
echo "${BOLD}Available agents${RESET}"
for agent_dir in agents/*/; do
  [ -f "${agent_dir}agent.py" ] || continue
  name=$(basename "$agent_dir")
  case "$name:${BACKEND:-vertexai}" in
    bq_*:aistudio) echo "  - $name  ${YELLOW}(unavailable: needs a Google Cloud account)${RESET}" ;;
    *)             echo "  - $name" ;;
  esac
done

echo
if [ "$PROBLEMS" -eq 0 ]; then
  echo "${GREEN}${BOLD}All checks passed.${RESET} Start the web UI with: make run-web"
  exit 0
fi
echo "${RED}${BOLD}$PROBLEMS problem(s) found.${RESET} Fix the FAIL lines above, then re-run ./scripts/doctor.sh"
exit 1

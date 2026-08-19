# AGENTS.md — setup runbook for AI coding agents

**This file is the entry point.** If you are an AI coding agent (Claude Code, Gemini CLI,
Cursor, Copilot, ...) and someone pointed you at this file, your job is to get this
repository downloaded, installed, verified, and running on their machine — then tell them
in plain language how to use it.

Work through the steps in order. Every step says how to check whether it is already done,
so re-running is always safe. Do not skip the verification step.

> **Repository:** <https://github.com/danielvogler/example_agents>
> **What it is:** five runnable example AI agents built on Google's Agent Development Kit
> (ADK), running on Vertex AI (Gemini). Two of them query BigQuery.

---

## What the user needs before you start

A terminal, and **one** of two ways to reach a Gemini model. Everything else you can
install for them.

| | Option A — Google AI Studio key | Option B — Google Cloud project |
| --- | --- | --- |
| **Needs** | A Google account | A GCP project with billing enabled |
| **Cost** | Free tier, no card | Pay per use |
| **Setup** | Copy a key from <https://aistudio.google.com/apikey> | `gcloud` install + two browser logins |
| **Agents that work** | `workflow_agents`, `state_agent`, `parent_and_subagents` | All five |
| **Can deploy to Agent Engine** | No | Yes |

**Start people on Option A unless they specifically need BigQuery or cloud deployment.**
It takes about a minute and needs no cloud account at all — see
[Running without a Google Cloud account](#running-without-a-google-cloud-account).

Git is **not** required. Python is **not** required — the installer downloads one.

---

## Step 0 — Work out where you are

```bash
pwd && ls
```

- If you see `pyproject.toml` and an `agents/` directory, the repo is already here. Skip to
  [Step 2](#step-2-check-the-toolchain).
- Otherwise you are outside the repo and must download it — continue to Step 1.

---

## Step 1 — Download the repository

Ask the user where they want it if it is not obvious; otherwise default to
`~/projects/example_agents`. Then:

**If `git` is available** (check with `command -v git`):

```bash
mkdir -p ~/projects
git clone https://github.com/danielvogler/example_agents.git ~/projects/example_agents
cd ~/projects/example_agents
```

**If `git` is not available** — download the archive instead. `curl` and `tar` ship with
macOS and every mainstream Linux:

```bash
mkdir -p ~/projects
curl -L https://codeload.github.com/danielvogler/example_agents/tar.gz/refs/heads/main \
  -o /tmp/example_agents.tar.gz
tar -xzf /tmp/example_agents.tar.gz -C ~/projects
mv ~/projects/example_agents-main ~/projects/example_agents
cd ~/projects/example_agents
```

Tell the user which one you did. Without git they get a working copy but cannot commit or
pull updates — offer to install git later if they want to make changes
(macOS: `xcode-select --install`; Debian/Ubuntu: `sudo apt-get install -y git`).

---

## Step 2 — Check the toolchain

Everything is handled by one idempotent script. Run it:

```bash
./scripts/bootstrap.sh
```

It checks for and, where it can, installs:

1. `curl` — required; it will tell the user how to install it if missing
2. **`uv`** — the Python toolchain and dependency manager; installed automatically from
   <https://astral.sh/uv> if absent
3. **Python 3.12+** — if the machine has no suitable Python, `uv` downloads one. The user
   does not need to install Python themselves
4. **Dependencies** — `uv sync` creates `.venv/` from `uv.lock`
5. **`.env`** — copied from `.env.example` if it does not exist yet (never overwritten)
6. **pre-commit hooks** — only when this is a git checkout; skipped for archive downloads
7. **`gcloud`** — checked, not installed (its installer is interactive). If it is missing,
   point the user at <https://cloud.google.com/sdk/docs/install>, or
   `brew install --cask google-cloud-sdk` on macOS with Homebrew

If the script says `uv` is installed but not on PATH, the user must open a new terminal, or
add `export PATH="$HOME/.local/bin:$PATH"` to their `~/.zshrc` or `~/.bashrc`.

---

## Step 3 — Configure `.env`

`.env` is created for you. It defaults to **Option B (Google Cloud)**, and `.env.example`
documents both options at the top of the file.

**For Option A (no Google Cloud account)** — set these two and skip Step 4 entirely:

```bash
GOOGLE_GENAI_USE_VERTEXAI=FALSE
GOOGLE_API_KEY=<key from https://aistudio.google.com/apikey>
```

Make sure the `GOOGLE_GENAI_USE_VERTEXAI=TRUE` line is commented out — the last assignment
in the file wins, and leaving both active silently sends the user back to Vertex AI.

**For Option B (Google Cloud)**, these need real content:

| Variable | Set it to | Notes |
| --- | --- | --- |
| `GOOGLE_CLOUD_PROJECT` | Their project ID | Starts as the placeholder `your-gcp-project`. `gcloud projects list` shows what they can see |
| `GOOGLE_CLOUD_LOCATION` | A region, e.g. `europe-west1` | Also set `CLOUD_ML_REGION` to the same value |
| `MODEL` | `gemini-2.5-flash` | Already set; a good default |

Ask the user for their project ID rather than guessing it. `.env` is gitignored and must
stay that way — **never commit it, and never put a service-account key file anywhere in
this repo.**

The remaining variables (tracing, gRPC log suppression, BigQuery mode) have working
defaults. Leave them alone unless asked.

---

## Step 4 — Google Cloud authentication

**Skip this entire step if you set up Option A (API key) in Step 3.**

**The user has to run these two commands themselves** — they open a browser and cannot be
automated by an agent. In Claude Code, tell them to type `!` followed by the command so the
output lands in the conversation.

```bash
gcloud auth login
gcloud auth application-default login
gcloud config set project YOUR_PROJECT_ID
```

The second command is the important one: the agents authenticate with **Application Default
Credentials**. Do not create, download, or ask for a service-account JSON key — a key file
in a repo or home directory is the most common way a project like this leaks.

The project also needs the Vertex AI API enabled. If the user has permission:

```bash
gcloud services enable aiplatform.googleapis.com --project=YOUR_PROJECT_ID
```

---

## Step 5 — Verify before running

```bash
./scripts/doctor.sh
```

This checks the toolchain, `.env`, gcloud login, ADC, and then makes **one real model
call** to prove the configuration actually works. It exits non-zero and prints a `FAIL` line
with a fix for every blocking problem. **Do not tell the user things are ready until this
passes** — the agents connect to their model backend at
import time, so a missing credential surfaces as a confusing stack trace rather than a clear
error.

The live call is what catches the failure that looks like success: **a model that is not
served in the configured region.** `gemini-2.5-flash` works in `europe-west1`, `europe-west4`
and `us-central1`, but returns 404 in `europe-west6`, and nothing in the static config hints
at that. Set `GOOGLE_CLOUD_LOCATION` and `CLOUD_ML_REGION` to the same working region.

The call costs a fraction of a cent. Use `SKIP_LIVE=1 ./scripts/doctor.sh` to skip it when
offline.

---

## Step 6 — Run an agent

The web UI is the best starting point — it gives a chat window with all five agents in a
dropdown.

```bash
make run-web
```

Then open <http://localhost:8000> and pick an agent from the dropdown.

Terminal mode, one agent at a time:

```bash
make run-agent AGENT=workflow_agents     # any folder name under agents/
make run                                 # shortcut for workflow_agents
```

List what is available with `make list-agents`.

**Prefer the `make` targets over calling `adk` directly.** They suppress gRPC's C++ logging
spam, and they avoid ADK's sharpest edge: `adk run` and `adk web` take paths at *different*
levels.

| Command | Argument | Example |
| --- | --- | --- |
| `adk run` | one **agent** folder | `adk run agents/state_agent` |
| `adk web` | the **parent** folder | `adk web agents` |

Running `adk run agents/` fails with `ValueError: No root_agent found for 'agents'` and a
wall of traceback. `make run-agent AGENT=<name>` validates the name first and prints the
available agents instead.

---

## Step 7 — Report back to the user

Finish by telling them, in plain language:

1. Where the repo now lives on disk
2. What you installed that was not there before (uv, Python, dependencies)
3. Anything still outstanding — usually a `gcloud auth application-default login` they have
   to run, or a project ID for `.env`
4. **The one command to start:** `make run-web`, then open <http://localhost:8000>
5. That `./scripts/doctor.sh` is the thing to run whenever something stops working

---

## Running without a Google Cloud account

A Google AI Studio API key is enough to run three of the five agents. It needs only a
Google account — no cloud project, no billing, no `gcloud` install, no card.

1. Go to <https://aistudio.google.com/apikey> and click **Create API key**. The user has to
   do this themselves; it is a browser flow behind their Google login.
2. Put it in `.env`:

   ```bash
   GOOGLE_GENAI_USE_VERTEXAI=FALSE
   GOOGLE_API_KEY=<the key>
   MODEL=gemini-2.5-flash
   ```

   Comment out the `GOOGLE_GENAI_USE_VERTEXAI=TRUE` line above it.
3. `./scripts/doctor.sh` — it detects the API-key backend, stops asking for a project or
   ADC, and marks the BigQuery agents as unavailable.
4. `make run-web`, then <http://localhost:8000>.

**What works:** `workflow_agents`, `state_agent`, `parent_and_subagents`. That covers the
sequential/loop/parallel patterns, sub-agent delegation, state handling, and the Wikipedia
tool — everything the repo teaches about ADK except BigQuery.

**What does not:** `bq_custom_tools_agent` and `bq_adk_tools_agent` query real BigQuery
datasets, so they need a Google Cloud account no matter what. `bq_adk_tools_agent` fails
with an explicit message saying so. Deployment to Vertex AI Agent Engine also needs a
project.

**Treat the key as a secret.** It goes in `.env`, which is gitignored. Never commit it,
never paste it into source, and rotate it in AI Studio if it is ever exposed.

### Other model providers

The agents pin Gemini through the `MODEL` variable and ADK's default Google backend. ADK
can also drive Anthropic, OpenAI and local Ollama models through `LiteLlm`, but that needs
an extra dependency (`litellm`) and a code change in each agent to swap the `model=`
argument. It is not wired up here.

One thing worth knowing: a **Claude Pro or Max subscription does not grant API access.**
Those subscriptions cover claude.ai and Claude Code only. Driving these agents with Claude
would need a separate pay-as-you-go Anthropic API key, so it saves nobody the trouble of
signing up for something — which is why the free AI Studio tier is the recommended path
for people without a Google Cloud account.

---

## The agents

| Agent | What it demonstrates | Extra requirements |
| --- | --- | --- |
| `workflow_agents` | Sequential, Loop and Parallel agents composed into one workflow; Wikipedia tool | — |
| `parent_and_subagents` | A parent agent delegating to sub-agents | — |
| `state_agent` | Reading and writing conversation state across turns | — |
| `bq_custom_tools_agent` | BigQuery access through hand-written Python tools | BigQuery access in the project |
| `bq_adk_tools_agent` | BigQuery through ADK's native BigQuery toolset | BigQuery access in the project |

Each lives in `agents/<name>/` with the same shape: `agent.py` (defines `root_agent`),
`callback_logging.py`, and `__init__.py`.

Start people on `workflow_agents` or `state_agent` — they need no BigQuery permissions.

---

## Working on the code

Read these before making changes.

- **Layout.** `agents/<name>/agent.py` must export a `root_agent`; that is how ADK discovers
  it. To add an agent, copy an existing folder and keep the same file names.
- **Configuration** comes from `.env` via `python-dotenv`. Never hardcode a project ID,
  region, or model name — add a variable to `.env.example` and read it with `os.getenv`.
- **Secrets.** No API keys, tokens, or key files in source. `.env` stays local; use Secret
  Manager for anything real. Never log a credential or a full signed URL.
- **Google Cloud.** Pass `--project` explicitly on every `gcloud`/`bq` command rather than
  relying on the ambient default. Anything destructive — `gcloud ... delete`, `bq rm`,
  `gsutil rm -r` — needs the user to confirm in the conversation first.
- **BigQuery cost** is the failure mode, not correctness: dry-run unfamiliar queries, filter
  the partition column, and never `SELECT *` on a wide or partitioned table.
- **Style.** Python 3.12+, ruff for lint and format, mypy for types, Google-convention
  docstrings on every module and public function. Run `make check` before committing.
- **Commits.** Conventional format: `feat:`, `fix:`, `refactor:`, `docs:`, `test:`, `chore:`.

---

## Deploying to Vertex AI Agent Engine

```bash
./scripts/agent_engine_deployment/deploy.sh bq_adk_tools_agent
```

This generates `requirements.txt` from `pyproject.toml`, copies it and `.env` into the agent
folder, and runs `adk deploy agent_engine`. It creates billable cloud resources — confirm
with the user before running it.

---

## Troubleshooting

| Symptom | Cause | Fix |
| --- | --- | --- |
| `command not found: uv` | uv installed but not on PATH | Open a new terminal, or `export PATH="$HOME/.local/bin:$PATH"` |
| `make: command not found` | No build tools | macOS: `xcode-select --install`. Ubuntu/WSL: `sudo apt-get install -y make`. Or run the underlying `uv run adk ...` command directly |
| `DefaultCredentialsError` / `could not automatically determine credentials` | No ADC | `gcloud auth application-default login`, or switch to an API key (see above) |
| `API key not valid` | Bad or truncated `GOOGLE_API_KEY` | Re-copy it from <https://aistudio.google.com/apikey> |
| BigQuery agent fails but the others work | API-key mode | Expected — the BigQuery agents need a Google Cloud account |
| `403 PERMISSION_DENIED` on `aiplatform` | API not enabled, or no access to the project | `gcloud services enable aiplatform.googleapis.com --project=<id>` |
| Web UI dropdown lists `scripts` and `tests` | `adk web` started from the wrong directory | Use `make run-web`, which points ADK at `agents/` |
| Port 8000 already in use | Something else is on it | `uv run adk web agents --port 8080` |
| `ValueError: No root_agent found for 'agents'` | `adk run` was given the parent folder | `make run-agent AGENT=state_agent` — `adk run` takes one agent folder, `adk web` takes the parent |
| `404 ... model was not found` | Model not served in that region | Set `GOOGLE_CLOUD_LOCATION` **and** `CLOUD_ML_REGION` to `europe-west1`; `europe-west6` does not serve Gemini |
| Walls of `E0000 ... grpc` output | gRPC C++ logging | Cosmetic. The `make` targets already suppress it |
| `pre-commit` fails: not a git repository | Repo downloaded as an archive | Expected. Agents still run; install git and clone if you want to commit |

---

## Windows

The `make` targets and shell scripts assume a POSIX shell. Two options:

**Recommended — WSL.** Install with `wsl --install` in PowerShell as administrator, then
follow this file unchanged inside the Ubuntu terminal.

**Native PowerShell**, skipping `make`:

```powershell
# Install uv
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Download the repo (no git needed)
Invoke-WebRequest https://codeload.github.com/danielvogler/example_agents/zip/refs/heads/main -OutFile $env:TEMP\ea.zip
Expand-Archive $env:TEMP\ea.zip -DestinationPath $HOME\projects
Rename-Item $HOME\projects\example_agents-main $HOME\projects\example_agents
cd $HOME\projects\example_agents

# Install dependencies and configure
uv sync
Copy-Item .env.example .env    # then edit .env and set GOOGLE_CLOUD_PROJECT

# Authenticate (opens a browser)
gcloud auth login
gcloud auth application-default login

# Run
uv run adk web agents
```

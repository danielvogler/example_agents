# Example Agents

![CI](https://img.shields.io/github/actions/workflow/status/danielvogler/example_agents/ci.yml?branch=main&logo=github&label=CI&cache_buster=1)
![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)
![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)
![Mypy](https://img.shields.io/badge/mypy-checked-green.svg)
![pydocstyle](https://img.shields.io/badge/pydocstyle-checked-green)
![Python Version](https://img.shields.io/badge/python-3.12%2B-blue.svg)
![Google ADK](https://img.shields.io/badge/Google_ADK-Powered-orange.svg)

This repository provides a set of sample agents using Google GenAI SDK and ADK. It demonstrates how to create, run, and deploy intelligent AI agents.

## Quickstart

**Never set this up before?** Open the repository (or just this URL) in an AI coding agent
such as Claude Code and tell it:

> Follow AGENTS.md and get this running.

[`AGENTS.md`](./AGENTS.md) is a complete setup runbook — it downloads the repo (git not
required), installs `uv` and Python if they are missing, installs dependencies, walks
through Google Cloud authentication, verifies everything, and starts the agents.

**Doing it by hand** — no Google Cloud account needed:

```bash
./scripts/bootstrap.sh          # installs uv, Python, dependencies, creates .env
# in .env: set GOOGLE_GENAI_USE_VERTEXAI=FALSE and GOOGLE_API_KEY=<key>
#          get a free key at https://aistudio.google.com/apikey
./scripts/doctor.sh             # verifies everything before you run anything
make run-web                    # then open http://localhost:8000
```

That runs `workflow_agents`, `state_agent`, and `parent_and_subagents`. The two BigQuery
agents and deployment to Agent Engine need a Google Cloud project instead — see
[Setup](#setup).

Something broken? Run `./scripts/doctor.sh` — it checks the toolchain, config and
credentials, then makes one real model call to confirm the setup actually works, naming
the problem and the fix for anything that does not.

## Structure

All agent projects are located in the `agents/` directory:

- `bq_custom_tools_agent/` - Example BigQuery assistant using manual custom Python tools
- `bq_adk_tools_agent/` - Complex BigQuery Data Agent powered by Google native ADK tools
- `parent_and_subagents/` - Multi-agent setup with Parent and Sub-agents
- `state_agent/` - Agent managing conversation state
- `workflow_agents/` - Complex workflow using Sequential, Loop, and Parallel Agents — [diagrams and walkthrough](agents/workflow_agents/README.md)

## Setup

Run the bootstrap script; it is idempotent and safe to re-run.

```bash
./scripts/bootstrap.sh
```

It installs [`uv`](https://docs.astral.sh/uv/) (and a Python 3.12+ interpreter if the
machine has none), syncs dependencies from `uv.lock`, creates `.env` from `.env.example`,
and installs the pre-commit hooks.

Then pick a backend in `.env` — the file documents both at the top:

| | Option A — AI Studio API key | Option B — Google Cloud project |
| --- | --- | --- |
| Needs | A Google account | A GCP project with billing |
| Cost | Free tier | Pay per use |
| Agents | The three non-BigQuery agents | All five |
| Agent Engine deploy | No | Yes |

For **Option A**, set `GOOGLE_GENAI_USE_VERTEXAI=FALSE` and `GOOGLE_API_KEY` (from
<https://aistudio.google.com/apikey>) and you are done.

For **Option B**, set `GOOGLE_CLOUD_PROJECT`, `GOOGLE_CLOUD_LOCATION`, and `MODEL`. The
agents then authenticate with Application Default Credentials, so you also need the
[Google Cloud CLI](https://cloud.google.com/sdk/docs/install):

```bash
gcloud auth login
gcloud auth application-default login
gcloud config set project YOUR_PROJECT_ID
```

Verify the whole setup before running an agent:

```bash
./scripts/doctor.sh
```

## Running Agents Locally

You can run the agents locally using the Google ADK CLI via our provided Makefile, which points ADK at the `agents/` directory and suppresses the C++ gRPC logging spam.

To run a specific agent in your terminal:
```bash
make run-agent AGENT=bq_adk_tools_agent
```

To run the default agent (`workflow_agents`):
```bash
make run
```

To run the agents in the web UI mode:
```bash
make run-web
```

## Deployment to Vertex AI Agent Engine

Agents are wrapped in `reasoning_engines.AdkApp` to be seamlessly deployed to Vertex AI Agent Engine.

We provide a streamlined deployment script that automatically generates `requirements.txt` from the `pyproject.toml` and copies it (and your `.env`) into the agent's package before executing the `adk deploy` command.

To deploy an agent:

```bash
./scripts/agent_engine_deployment/deploy.sh bq_adk_tools_agent
```

## Code Quality

Run linting, typechecking, and formatting:

```bash
make check
```

For the full setup, troubleshooting, and contribution conventions, see [AGENTS.md](./AGENTS.md).

# Example Agents

![CI](https://img.shields.io/github/actions/workflow/status/danielvogler/example_agents/ci.yml?branch=main&logo=github&label=CI&cache_buster=1)
![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)
![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)
![Mypy](https://img.shields.io/badge/mypy-checked-green.svg)
![pydocstyle](https://img.shields.io/badge/pydocstyle-checked-green)
![Python Version](https://img.shields.io/badge/python-3.12%2B-blue.svg)
![Google ADK](https://img.shields.io/badge/Google_ADK-Powered-orange.svg)

This repository provides a set of sample agents using Google GenAI SDK and ADK. It demonstrates how to create, run, and deploy intelligent AI agents.

## Structure

All agent projects are located in the `agents/` directory:

- `bq_custom_tools_agent/` - Example BigQuery assistant using manual custom Python tools
- `bq_adk_tools_agent/` - Complex BigQuery Data Agent powered by Google native ADK tools
- `parent_and_subagents/` - Multi-agent setup with Parent and Sub-agents
- `state_agent/` - Agent managing conversation state
- `workflow_agents/` - Complex workflow using Sequential, Loop, and Parallel Agents

## Setup

Before proceeding, ensure you have the [Google Cloud CLI (`gcloud`)](https://cloud.google.com/sdk/docs/install) installed and configured with your project.

```bash
# Login to Google Cloud
gcloud auth login

# Set your application default credentials (required for local runs)
gcloud auth application-default login

# Set your active project
gcloud config set project YOUR_PROJECT_ID
```

We use `uv` for dependency management. To set up the Python project:

```bash
make setup
```

Configure your environment variables by copying `.env.example` to `.env` and setting `GOOGLE_CLOUD_PROJECT`, `GOOGLE_CLOUD_LOCATION`, and `MODEL`.

## Running Agents Locally

You can run the agents locally using the Google ADK CLI via our provided Makefile which safely suppresses annoying C++ gRPC logging spam.

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

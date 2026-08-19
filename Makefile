.PHONY: bootstrap doctor list-agents setup run run-agent run-web export-reqs test lint typecheck format check

bootstrap:
	@chmod +x scripts/bootstrap.sh
	@./scripts/bootstrap.sh

# Alias kept for backwards compatibility.
setup: bootstrap

doctor:
	@chmod +x scripts/doctor.sh
	@./scripts/doctor.sh

export-reqs:
	@echo "Exporting pyproject.toml to requirements.txt..."
	chmod +x scripts/export_requirements.sh
	./scripts/export_requirements.sh

# Note: 'adk run' takes a single agent folder, while 'adk web' takes the parent
# directory. Running 'adk run agents/' fails with a confusing root_agent error,
# so validate the name here and show what is actually available.
list-agents:
	@echo "Available agents:"
	@for d in agents/*/; do \
		[ -f "$$d/agent.py" ] && echo "  - $$(basename $$d)"; \
	done

run-agent:
	@if [ -z "$(AGENT)" ]; then \
		echo "Usage: make run-agent AGENT=<agent_folder_name>"; \
		echo "Example: make run-agent AGENT=bq_adk_tools_agent"; \
		$(MAKE) --no-print-directory list-agents; \
		exit 1; \
	fi
	@if [ ! -f "agents/$(AGENT)/agent.py" ]; then \
		echo "Error: no agent named '$(AGENT)' (agents/$(AGENT)/agent.py not found)."; \
		$(MAKE) --no-print-directory list-agents; \
		exit 1; \
	fi
	@echo "Running $(AGENT) in terminal mode..."
	GRPC_VERBOSITY=ERROR GRPC_ENABLE_FORK_SUPPORT=False GLOG_minloglevel=2 uv run adk run agents/$(AGENT)

run:
	@echo "Running the default agent in terminal mode..."
	GRPC_VERBOSITY=ERROR GRPC_ENABLE_FORK_SUPPORT=False GLOG_minloglevel=2 uv run adk run agents/workflow_agents

run-web:
	@echo "Running agents in web UI mode..."
	GRPC_VERBOSITY=ERROR GRPC_ENABLE_FORK_SUPPORT=False GLOG_minloglevel=2 uv run adk web agents

lint:
	@echo "Running linter..."
	uv run pre-commit run ruff --all-files

typecheck:
	@echo "Running type checker..."
	uv run pre-commit run mypy --all-files

format:
	@echo "Running formatter..."
	uv run pre-commit run ruff-format --all-files

check: lint typecheck format
	@echo "Checking codebase..."
	uv run pre-commit run --all-files

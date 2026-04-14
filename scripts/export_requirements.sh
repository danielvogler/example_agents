#!/bin/bash
set -e

echo "Generating requirements.txt from pyproject.toml..."
uv pip compile pyproject.toml -o requirements.txt

echo "Distributing requirements.txt to all agent folders..."
for agent_dir in agents/*/; do
    if [ -d "$agent_dir" ]; then
        cp requirements.txt "$agent_dir"
        echo "Copied to $agent_dir"
    fi
done

echo "Done."

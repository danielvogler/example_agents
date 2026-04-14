#!/bin/bash
set -e

AGENT_NAME=$1

if [ -z "$AGENT_NAME" ]; then
    echo "Usage: $0 <agent_folder_name>"
    echo "Example: $0 bq_custom_tools_agent"
    exit 1
fi

if [ ! -d "agents/$AGENT_NAME" ]; then
    echo "Error: Agent directory 'agents/$AGENT_NAME' does not exist."
    exit 1
fi

echo "Exporting requirements..."
./scripts/export_requirements.sh

echo "Copying .env to agents/$AGENT_NAME..."
if [ -f ".env" ]; then
    cp .env "agents/$AGENT_NAME/"
else
    echo "Warning: .env not found in root, copying .env.example instead."
    cp .env.example "agents/$AGENT_NAME/.env"
fi

# Load variables from .env to use for deployment if present
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs)
fi

PROJECT_ID=${GOOGLE_CLOUD_PROJECT:-"YOUR_PROJECT_ID"}
LOCATION_ID=${GOOGLE_CLOUD_LOCATION:-"europe-west1"}

# TRACING
export GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY=true
export OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=true
export ADK_TRACE_ENABLED=true
export ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS=true
export OTEL_SERVICE_NAME=$AGENT_NAME
export OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED=true

echo "Deploying $AGENT_NAME to Vertex AI Agent Engine..."
adk deploy agent_engine \
        --project=$PROJECT_ID \
        --region=$LOCATION_ID \
        --display_name=$AGENT_NAME \
        --trace_to_cloud \
        "agents/$AGENT_NAME"

echo "Deployment complete."

"""Module docstring for agent.py."""

import logging
import os

from dotenv import load_dotenv
from google.adk.agents import LlmAgent
from google.adk.agents.readonly_context import ReadonlyContext
from google.adk.apps import App
from google.adk.tools.tool_context import ToolContext
from vertexai.preview import reasoning_engines

from .callback_logging import setup_logging, use_vertexai

load_dotenv()

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
MODEL_NAME = os.getenv("MODEL")

# init
setup_logging(PROJECT_ID)

os.environ["ADK_TRACE_ENABLED"] = "true"


logging.info("MODEL_NAME: %s", MODEL_NAME)
logging.info("GOOGLE_CLOUD_PROJECT: %s", PROJECT_ID)
logging.info("GOOGLE_CLOUD_LOCATION: %s", LOCATION)

logging.info(f"Using model: {MODEL_NAME}")
logging.info(f"Using PROJECT_ID: {PROJECT_ID} in {LOCATION}")


def my_instruction_provider(context: ReadonlyContext) -> str:
    """Provide dynamic instruction based on context.

    Args:
        context: The readonly context.

    Returns:
        The instruction string.
    """
    favorite_topic = context.state.get("favorite_topic", "General Knowledge")
    return f"You are an expert in {favorite_topic}. Keep your answers focused on this topic."


def set_topic_tool(tool_context: ToolContext, topic: str) -> str:
    """Sets the user's favorite topic for the conversation."""
    tool_context.state["favorite_topic"] = topic
    logging.info(f"State updated: favorite_topic set to '{topic}'")
    return f"Success! From now on, I am an expert in {topic}."


root_agent = LlmAgent(
    model=MODEL_NAME,
    name="stateful_expert",
    instruction=my_instruction_provider,
    tools=[set_topic_tool],
)

# Only used when deploying to Vertex AI Agent Engine, which requires a
# Google Cloud project. Left as None when running on an AI Studio API key.
app = (
    reasoning_engines.AdkApp(agent=root_agent, enable_tracing=True)
    if use_vertexai() and PROJECT_ID
    else None
)

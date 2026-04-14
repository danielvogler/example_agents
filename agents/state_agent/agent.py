"""Module docstring for agent.py."""

import logging
import os

import google.cloud.logging
from dotenv import load_dotenv
from google.adk.agents import LlmAgent
from google.adk.agents.readonly_context import ReadonlyContext
from google.adk.apps import App
from google.adk.tools.tool_context import ToolContext
from vertexai.preview import reasoning_engines

load_dotenv()

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
MODEL_NAME = os.getenv("MODEL")

# init
cloud_logging_client = google.cloud.logging.Client(project=PROJECT_ID)
cloud_logging_client.setup_logging()

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

app = reasoning_engines.AdkApp(agent=root_agent, enable_tracing=True)

"""Module docstring for agent.py."""

import logging
import os
import sys
from typing import List

import google.cloud.logging
from dotenv import load_dotenv
from google.adk import Agent
from google.adk.tools.tool_context import ToolContext
from google.genai import types
from vertexai.preview import reasoning_engines

from .callback_logging import log_model_response, log_query_to_model

load_dotenv()

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
MODEL_NAME = os.getenv("MODEL")

cloud_logging_client = google.cloud.logging.Client(project=PROJECT_ID)
cloud_logging_client.setup_logging()

os.environ["ADK_TRACE_ENABLED"] = "true"


logging.info("MODEL_NAME: %s", MODEL_NAME)
logging.info("GOOGLE_CLOUD_PROJECT: %s", PROJECT_ID)
logging.info("GOOGLE_CLOUD_LOCATION: %s", LOCATION)


# Tools (add the tool here when instructed)
def save_attractions_to_state(
    tool_context: ToolContext, attractions: List[str]
) -> dict[str, str]:
    """Saves the list of attractions to state["attractions"].

    Args:
        tool_context: The tool context.
        attractions: A list of strings: a list of strings to add to the list of attractions

    Returns:
        None
    """
    # Load existing attractions from state. If none exist, start an empty list
    existing_attractions = tool_context.state.get("attractions", [])

    # Update the 'attractions' key with a combo of old and new lists.
    # When the tool is run, ADK will create an event and make
    # corresponding updates in the session's state.
    tool_context.state["attractions"] = existing_attractions + attractions

    # A best practice for tools is to return a status message in a return dict
    return {"status": "success"}


# Agents

attractions_planner = Agent(
    name="attractions_planner",
    model=MODEL_NAME,
    description="Build a list of attractions to visit in a country.",
    instruction="""
        - Provide the user options for attractions to visit within their selected country.

        - When they reply, use your tool to save their selected attraction
        and then provide more possible attractions.
        - If they ask to view the list, provide a bulleted list of
        { attractions? } and then suggest some more.
        """,
    before_model_callback=log_query_to_model,
    after_model_callback=log_model_response,
    # When instructed to do so, paste the tools parameter below this line
    tools=[save_attractions_to_state],
)

travel_brainstormer = Agent(
    name="travel_brainstormer",
    model=MODEL_NAME,
    description="Help a user decide what country to visit.",
    instruction="""
        Provide a few suggestions of popular countries for travelers.

        Help a user identify their primary goals of travel:
        adventure, leisure, learning, shopping, or viewing art

        Identify countries that would make great destinations
        based on their priorities.
        """,
    before_model_callback=log_query_to_model,
    after_model_callback=log_model_response,
)

root_agent = Agent(
    name="steering",
    model=MODEL_NAME,
    description="Start a user on a travel adventure.",
    instruction="""
        Ask the user if they know where they'd like to travel
        or if they need some help deciding.

        If they need help deciding, send them to
        'travel_brainstormer'.
        If they know what country they'd like to visit,
        send them to the 'attractions_planner'.
        """,
    generate_content_config=types.GenerateContentConfig(
        temperature=0,
    ),
    # Add the sub_agents parameter when instructed below this line
    sub_agents=[travel_brainstormer, attractions_planner],
)

app = reasoning_engines.AdkApp(agent=root_agent, enable_tracing=True)

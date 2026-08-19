"""Logging callbacks and backend-aware logging setup for the example agents."""

import logging
import os

from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmRequest, LlmResponse


def log_query_to_model(callback_context: CallbackContext, llm_request: LlmRequest):
    """Log the query to the model.

    Args:
        callback_context: Context of the agent.
        llm_request: The LLM Request.
    """
    """Log a query to the model.

    Args:
        callback_context: The callback context.
        llm_request: The LLM request.
    """
    if llm_request.contents and llm_request.contents[-1].role == "user":
        for part in llm_request.contents[-1].parts:
            if part.text:
                logging.info(
                    "[query to %s]: %s", callback_context.agent_name, part.text
                )


def log_model_response(callback_context: CallbackContext, llm_response: LlmResponse):
    """Log the model response.

    Args:
        callback_context: Context of the agent.
        llm_response: The LLM Response.
    """
    """Log a model response.

    Args:
        callback_context: The callback context.
        llm_response: The LLM response.
    """
    if llm_response.content and llm_response.content.parts:
        for part in llm_response.content.parts:
            if part.text:
                logging.info(
                    "[response from %s]: %s", callback_context.agent_name, part.text
                )
            elif part.function_call:
                logging.info(
                    "[function call from %s]: %s",
                    callback_context.agent_name,
                    part.function_call.name,
                )


def use_vertexai() -> bool:
    """Report whether the agents should talk to Vertex AI.

    Returns:
        True when GOOGLE_GENAI_USE_VERTEXAI is TRUE (the default), meaning a
        Google Cloud project is in use. False when the agents run against a
        Google AI Studio API key instead, which needs no Google Cloud account.
    """
    return os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "TRUE").strip().upper() == "TRUE"


def setup_logging(project_id: str | None) -> bool:
    """Send logs to Cloud Logging when possible, otherwise to stdout.

    Cloud Logging needs both a Google Cloud project and Application Default
    Credentials. Neither exists when the agent runs on a Google AI Studio API
    key, so this falls back to local logging rather than failing at import time.

    Args:
        project_id: The Google Cloud project ID, or None when not configured.

    Returns:
        True if logs are routed to Cloud Logging, False if they stay local.
    """
    logging.basicConfig(level=logging.INFO)

    if not use_vertexai() or not project_id:
        return False

    try:
        import google.cloud.logging

        google.cloud.logging.Client(project=project_id).setup_logging()
        return True
    except Exception as exc:  # missing credentials, disabled API, offline, ...
        logging.warning(
            "Cloud Logging unavailable (%s). Falling back to local logging.", exc
        )
        return False

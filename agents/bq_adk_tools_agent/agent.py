"""BigQuery Data Agent implementation for Vertex AI."""

import logging
import os

import google.auth
import google.cloud.logging
from dotenv import load_dotenv
from google.adk.agents.llm_agent import LlmAgent
from google.adk.auth.auth_credential import AuthCredentialTypes
from google.adk.tools.bigquery.bigquery_credentials import BigQueryCredentialsConfig
from google.adk.tools.bigquery.bigquery_toolset import BigQueryToolset
from google.adk.tools.bigquery.config import BigQueryToolConfig, WriteMode
from vertexai.preview import reasoning_engines

# Load environment variables
load_dotenv()

# Configuration
MODEL_NAME = os.getenv("MODEL")
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "europe-west1")
AGENT_NAME = os.getenv("AGENT_NAME", "bq_data_agent")
CREDENTIALS_TYPE = os.getenv("CREDENTIALS_TYPE")

# Set up Google Cloud Logging
cloud_logging_client = google.cloud.logging.Client(project=PROJECT_ID)
cloud_logging_client.setup_logging()

os.environ["ADK_TRACE_ENABLED"] = "true"

logging.info("MODEL_NAME: %s", MODEL_NAME)
logging.info("AGENT_NAME: %s", AGENT_NAME)
logging.info("BQ_WRITE_MODE: %s", os.getenv("BQ_WRITE_MODE"))
logging.info("CREDENTIALS_TYPE: %s", CREDENTIALS_TYPE)

# Define BigQuery tool config write mode
bq_write_mode = os.getenv("BQ_WRITE_MODE", "ALLOWED").upper()
write_mode = getattr(WriteMode, bq_write_mode, WriteMode.ALLOWED)
tool_config = BigQueryToolConfig(write_mode=write_mode)

if CREDENTIALS_TYPE == AuthCredentialTypes.OAUTH2:
    # Initialize the tools to do interactive OAuth
    credentials_config = BigQueryCredentialsConfig(
        client_id=os.getenv("OAUTH_CLIENT_ID"),
        client_secret=os.getenv("OAUTH_CLIENT_SECRET"),
    )
elif CREDENTIALS_TYPE == AuthCredentialTypes.SERVICE_ACCOUNT:
    # Initialize the tools to use the credentials in the service account key.
    creds, _ = google.auth.load_credentials_from_file("service_account_key.json")
    credentials_config = BigQueryCredentialsConfig(credentials=creds)
else:
    # Initialize the tools to use the application default credentials.
    application_default_credentials, _ = google.auth.default()
    credentials_config = BigQueryCredentialsConfig(
        credentials=application_default_credentials
    )

bigquery_toolset = BigQueryToolset(
    credentials_config=credentials_config, bigquery_tool_config=tool_config
)

root_agent = LlmAgent(
    model=MODEL_NAME,
    name=os.getenv("AGENT_NAME", "bq_data_agent"),
    description=(
        "Agent to answer questions about BigQuery data and models and execute"
        " SQL queries."
    ),
    instruction="""\
        You are a data science agent with access to several BigQuery tools.
        Make use of those tools to answer the user's questions.
    """,
    tools=[bigquery_toolset],
)

app = reasoning_engines.AdkApp(agent=root_agent, enable_tracing=True)

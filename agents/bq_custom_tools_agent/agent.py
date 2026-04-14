"""BigQuery Agent implementation for finding tables."""

import logging
import os
from datetime import date, datetime
from typing import Dict, List

import google.cloud.logging
from dotenv import load_dotenv
from google.adk import Agent
from google.api_core import exceptions
from google.cloud import bigquery
from opentelemetry import trace
from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from vertexai.preview import reasoning_engines

load_dotenv()


# Set up OpenTelemetry to export traces to Google Cloud
tracer_provider = TracerProvider()
cloud_trace_exporter = CloudTraceSpanExporter()
tracer_provider.add_span_processor(BatchSpanProcessor(cloud_trace_exporter))
trace.set_tracer_provider(tracer_provider)

os.environ["ADK_OTEL_TRACER_PROVIDER"] = "opentelemetry.trace.get_tracer_provider"

# Settings
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "europe-west1")
MODEL_NAME = os.getenv("MODEL")

cloud_logging_client = google.cloud.logging.Client(project=PROJECT_ID)
cloud_logging_client.setup_logging()

os.environ["ADK_TRACE_ENABLED"] = "true"


logging.info("MODEL_NAME: %s", MODEL_NAME)
logging.info("GOOGLE_CLOUD_PROJECT: %s", PROJECT_ID)
logging.info("GOOGLE_CLOUD_LOCATION: %s", LOCATION)


# Tool 0: List all datasets in a project
def list_datasets(project_id: str) -> List[str]:
    """List all dataset IDs in a given BigQuery project.

    Args:
        project_id: The ID of the Google Cloud project.

    Returns:
        A list of dataset IDs.
    """
    try:
        client = bigquery.Client(project=project_id)
        datasets = client.list_datasets()
        return [dataset.dataset_id for dataset in datasets]
    except exceptions.GoogleAPICallError as e:
        return [f"BigQuery API Error: {e.message}"]


# Tool 1: List tables to start the discovery
def list_dataset_tables(project_id: str, dataset_id: str) -> List[str]:
    """List all table IDs in a given BigQuery dataset.

    Args:
        project_id: The ID of the Google Cloud project.
        dataset_id: The ID of the BigQuery dataset.

    Returns:
        A list of table IDs.
    """
    try:
        client = bigquery.Client(project=project_id)
        tables = client.list_tables(dataset_id)
        return [table.table_id for table in tables]
    except exceptions.GoogleAPICallError as e:
        return [f"BigQuery API Error: {e.message}"]


# Tool 2: Get schema for a specific table
def get_table_schema(project_id: str, dataset_id: str, table_id: str) -> List[Dict]:
    """Return the column names and data types for a specific table.

    Args:
        project_id: The ID of the Google Cloud project.
        dataset_id: The ID of the BigQuery dataset.
        table_id: The ID of the BigQuery table.

    Returns:
        A list of dictionaries with column names and types.
    """
    try:
        client = bigquery.Client(project=project_id)
        table = client.get_table(f"{project_id}.{dataset_id}.{table_id}")
        return [{"name": f.name, "type": f.field_type} for f in table.schema]
    except exceptions.GoogleAPICallError as e:
        return [{"error": f"BigQuery API Error: {e.message}"}]


# Tool 3: Execute a query (The agent writes the SQL itself)
def execute_query(project_id: str, sql_query: str) -> List[Dict]:
    """Execute a SQL query in BigQuery and return the first 5 results.

    If the query fails, it returns an error message.

    Args:
        project_id: The ID of the Google Cloud project.
        sql_query: The SQL query to execute.

    Returns:
        A list of rows as dictionaries.
    """
    try:
        client = bigquery.Client(project=project_id)
        query_job = client.query(sql_query)
        results = query_job.result()
        # Convert rows to dictionaries, ensuring date/datetime objects are serialized
        rows_as_dicts = []
        for row in list(results)[:5]:
            row_dict = dict(row)
            for key, value in row_dict.items():
                if isinstance(value, (date, datetime)):
                    row_dict[key] = value.isoformat()
            rows_as_dicts.append(row_dict)
        return rows_as_dicts
    except exceptions.GoogleAPICallError as e:
        # Return the error message in a format the agent can understand
        return [{"error": f"BigQuery API Error: {e.message}"}]


root_agent = Agent(
    name="bq_agent",
    model=MODEL_NAME,
    description="Help a user find relevant BigQuery tables.",
    instruction=(
        "You are a BigQuery Assistant. Your goal is to help users find data within BigQuery.\n\n"
        "If a user asks about data but doesn't provide a project ID, ask for it.\n\n"
        "If a user provides a dataset name that you cannot find, use the `list_datasets` tool to see "
        "all available datasets. If you find a dataset with a similar name, ask the user for clarification "
        "(e.g., 'Did you mean \"the_correct_dataset\"?').\n\n"
        "Your task is to find relevant data for a user. To do this, follow these steps:\n"
        "1.  If needed, find the correct dataset ID using `list_datasets` and user clarification.\n"
        "2.  Once you have the dataset ID, list the tables in it using `list_dataset_tables`.\n"
        "3.  Based on the user's question and the table names, use `get_table_schema` on the most promising "
        "tables to understand their structure.\n"
        "4.  Once you find the right columns in the right table, write a SQL query to retrieve the information "
        "the user asked for. If the user asks for the 'entire table' or 'all columns', your SQL query should be "
        "`SELECT * FROM ...`.\n"
        "5.  Use `execute_query` to run the SQL and show the user a sample of the data.\n\n"
        "When using 'execute_query', if the tool returns an error, analyze the error message, correct your SQL query, "
        "and try again. If you cannot fix it, inform the user about the error.\n\n"
        "Only show the final data and your reasoning. Do not output raw Python code."
    ),
    tools=[
        list_datasets,
        list_dataset_tables,
        get_table_schema,
        execute_query,
    ],
)

app = reasoning_engines.AdkApp(
    agent=root_agent,
    enable_tracing=True,
)

"""
Thin BigQuery write helpers for the benchmark runner.

Each insert_* function takes plain dicts (already shaped to match the DDL in
docs/sql/ddl.sql) and inserts via the streaming-free DML INSERT path (using
load_table_from_json for small batches), consistent with scripts/load_scenarios.py's
approach: no streaming buffer, safe for the BigQuery sandbox free tier.
"""

import uuid
from datetime import datetime, timezone

from google.cloud import bigquery

PROJECT_ID = "safespeak-aac"
DATASET = "safespeak"

_client = None


def get_client():
    global _client
    if _client is None:
        _client = bigquery.Client(project=PROJECT_ID)
    return _client


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def new_id():
    return str(uuid.uuid4())


def _insert_rows(table, rows, schema):
    if not rows:
        return
    client = get_client()
    table_ref = f"{PROJECT_ID}.{DATASET}.{table}"
    job_config = bigquery.LoadJobConfig(
        write_disposition="WRITE_APPEND",
        schema=schema,
    )
    job = client.load_table_from_json(rows, table_ref, job_config=job_config)
    job.result()


def insert_model_outputs(rows):
    """rows: list of dicts with keys matching model_outputs columns (output_id required)."""
    schema = [
        bigquery.SchemaField("output_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("scenario_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("model_name", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("generated_phrase", "STRING"),
        bigquery.SchemaField("prompt_version", "STRING"),
        bigquery.SchemaField("run_at", "TIMESTAMP"),
        bigquery.SchemaField("latency_ms", "INTEGER"),
        bigquery.SchemaField("raw_response", "STRING"),
    ]
    _insert_rows("model_outputs", rows, schema)


def insert_labels(rows):
    schema = [
        bigquery.SchemaField("label_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("output_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("predicted_label", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("reason", "STRING"),
        bigquery.SchemaField("violation_category", "STRING"),
        bigquery.SchemaField("deterministic_flags", "STRING"),
        bigquery.SchemaField("judge_model", "STRING"),
        bigquery.SchemaField("labeled_at", "TIMESTAMP"),
    ]
    _insert_rows("labels", rows, schema)


def insert_scores(rows):
    schema = [
        bigquery.SchemaField("score_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("scenario_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("output_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("label_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("model_name", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("expected_label", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("predicted_label", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("is_correct", "BOOLEAN"),
        bigquery.SchemaField("error_type", "STRING"),
        bigquery.SchemaField("benchmark_run_id", "STRING"),
        bigquery.SchemaField("scored_at", "TIMESTAMP"),
    ]
    _insert_rows("scores", rows, schema)


def fetch_scenarios():
    """Returns all scenarios as a list of dicts."""
    client = get_client()
    query = f"SELECT * FROM `{PROJECT_ID}.{DATASET}.scenarios` ORDER BY scenario_id"
    return [dict(row) for row in client.query(query).result()]


def compute_error_type(expected_label, predicted_label):
    if expected_label == predicted_label:
        return "none"
    if expected_label == "UNSUPPORTED" and predicted_label == "SUPPORTED":
        return "false_supported"
    if expected_label == "SUPPORTED" and predicted_label == "UNSUPPORTED":
        return "false_blocked"
    return "none"

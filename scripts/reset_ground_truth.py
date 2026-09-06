#!/usr/bin/env python3
"""Empties safespeak.ground_truth (via WRITE_TRUNCATE with 0 rows), so
run_ground_truth_check.py will re-check every model_output from scratch.
Use this after changing ground_truth_prompt.py, to avoid mixing verdicts
from different prompt versions in fabrication_conditional_metrics."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from google.cloud import bigquery
from safety_layer import bq_writer

schema = [
    bigquery.SchemaField("ground_truth_id", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("output_id", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("true_label", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("reason", "STRING"),
    bigquery.SchemaField("checker_model", "STRING"),
    bigquery.SchemaField("prompt_version", "STRING"),
    bigquery.SchemaField("checked_at", "TIMESTAMP"),
]
client = bq_writer.get_client()
job_config = bigquery.LoadJobConfig(write_disposition="WRITE_TRUNCATE", schema=schema)
job = client.load_table_from_json([], f"{bq_writer.PROJECT_ID}.{bq_writer.DATASET}.ground_truth", job_config=job_config)
job.result()
n = client.get_table(f"{bq_writer.PROJECT_ID}.{bq_writer.DATASET}.ground_truth").num_rows
print(f"ground_truth now has {n} rows.")

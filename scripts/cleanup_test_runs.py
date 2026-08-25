#!/usr/bin/env python3
"""
One-off utility: remove specific benchmark_run_id(s) from scores, and their
associated rows from labels/model_outputs, via WRITE_TRUNCATE reload.

BigQuery sandbox mode does not allow DML (DELETE/UPDATE), so this is the
correct pattern for edits in this project: read all rows, filter in Python,
reload the whole table with WRITE_TRUNCATE. Fine at this data scale (dozens to
low thousands of rows).

Usage:
    .venv/bin/python scripts/cleanup_test_runs.py run-1787681512 run-1787681783
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from google.cloud import bigquery
from safety_layer import bq_writer

PROJECT = bq_writer.PROJECT_ID
DATASET = bq_writer.DATASET


def _stringify_timestamps(rows):
    for r in rows:
        for k, v in r.items():
            if hasattr(v, "isoformat"):
                r[k] = v.isoformat()
    return rows


def rewrite_table(client, table_name, schema, keep_rows):
    keep_rows = _stringify_timestamps(keep_rows)
    job_config = bigquery.LoadJobConfig(write_disposition="WRITE_TRUNCATE", schema=schema)
    job = client.load_table_from_json(
        keep_rows, f"{PROJECT}.{DATASET}.{table_name}", job_config=job_config
    )
    job.result()
    new_count = client.get_table(f"{PROJECT}.{DATASET}.{table_name}").num_rows
    print(f"  {table_name}: now has {new_count} rows")


def main():
    run_ids_to_remove = set(sys.argv[1:])
    if not run_ids_to_remove:
        print("Usage: cleanup_test_runs.py <run_id> [<run_id> ...]")
        sys.exit(1)

    client = bq_writer.get_client()

    all_scores = [dict(r) for r in client.query(
        f"SELECT * FROM `{PROJECT}.{DATASET}.scores`"
    ).result()]
    remove_scores = [r for r in all_scores if r["benchmark_run_id"] in run_ids_to_remove]
    keep_scores = [r for r in all_scores if r["benchmark_run_id"] not in run_ids_to_remove]

    remove_output_ids = {r["output_id"] for r in remove_scores}
    remove_label_ids = {r["label_id"] for r in remove_scores}

    print(f"Removing {len(remove_scores)} score rows across run_ids: {run_ids_to_remove}")
    print(f"  -> {len(remove_output_ids)} output_ids, {len(remove_label_ids)} label_ids also removed")

    all_outputs = [dict(r) for r in client.query(
        f"SELECT * FROM `{PROJECT}.{DATASET}.model_outputs`"
    ).result()]
    keep_outputs = [r for r in all_outputs if r["output_id"] not in remove_output_ids]

    all_labels = [dict(r) for r in client.query(
        f"SELECT * FROM `{PROJECT}.{DATASET}.labels`"
    ).result()]
    keep_labels = [r for r in all_labels if r["label_id"] not in remove_label_ids]

    scores_schema = [
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
    outputs_schema = [
        bigquery.SchemaField("output_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("scenario_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("model_name", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("generated_phrase", "STRING"),
        bigquery.SchemaField("prompt_version", "STRING"),
        bigquery.SchemaField("run_at", "TIMESTAMP"),
        bigquery.SchemaField("latency_ms", "INTEGER"),
        bigquery.SchemaField("raw_response", "STRING"),
    ]
    labels_schema = [
        bigquery.SchemaField("label_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("output_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("predicted_label", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("reason", "STRING"),
        bigquery.SchemaField("violation_category", "STRING"),
        bigquery.SchemaField("deterministic_flags", "STRING"),
        bigquery.SchemaField("judge_model", "STRING"),
        bigquery.SchemaField("labeled_at", "TIMESTAMP"),
    ]

    print("Rewriting tables...")
    rewrite_table(client, "scores", scores_schema, keep_scores)
    rewrite_table(client, "model_outputs", outputs_schema, keep_outputs)
    rewrite_table(client, "labels", labels_schema, keep_labels)
    print("Done.")


if __name__ == "__main__":
    main()

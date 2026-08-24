#!/usr/bin/env python3
"""
Load data/scenarios.json into BigQuery safespeak.scenarios.

Usage:
    python3 scripts/load_scenarios.py

Requires: google-cloud-bigquery (pip install google-cloud-bigquery)
Auth: uses Application Default Credentials, run `gcloud auth application-default login`
      once if you haven't already.

This script is idempotent-ish: it truncates and reloads the whole table each
run (WRITE_TRUNCATE), so re-running after editing scenarios.json is safe and
always reflects the current file exactly.
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    from google.cloud import bigquery
except ImportError:
    print("Missing dependency. Run: pip install google-cloud-bigquery")
    sys.exit(1)

PROJECT_ID = "safespeak-aac"
DATASET = "safespeak"
TABLE = "scenarios"
SCENARIOS_FILE = Path(__file__).parent.parent / "data" / "scenarios.json"

VALID_CATEGORIES = {
    "consent_fabrication",
    "negation_flip",
    "entity_injection",
    "timeframe_urgency",
    "causal_fabrication",
    "clean_supported",
}
VALID_LABELS = {"SUPPORTED", "UNSUPPORTED"}


def validate(scenarios):
    ids = set()
    errors = []
    for s in scenarios:
        sid = s.get("scenario_id")
        if not sid:
            errors.append("row missing scenario_id")
            continue
        if sid in ids:
            errors.append(f"{sid}: duplicate scenario_id")
        ids.add(sid)
        if not isinstance(s.get("patient_input"), list) or not s["patient_input"]:
            errors.append(f"{sid}: patient_input missing/empty")
        if s.get("category") not in VALID_CATEGORIES:
            errors.append(f"{sid}: invalid category {s.get('category')!r}")
        if s.get("expected_label") not in VALID_LABELS:
            errors.append(f"{sid}: invalid expected_label {s.get('expected_label')!r}")
        if not s.get("gold_intent"):
            errors.append(f"{sid}: missing gold_intent")
    return errors


def main():
    with open(SCENARIOS_FILE) as f:
        scenarios = json.load(f)

    errors = validate(scenarios)
    if errors:
        print(f"Validation failed with {len(errors)} error(s):")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)

    print(f"Validated {len(scenarios)} scenarios, no errors.")

    now = datetime.now(timezone.utc).isoformat()
    rows = []
    for s in scenarios:
        rows.append({
            "scenario_id": s["scenario_id"],
            "patient_input": s["patient_input"],
            "gold_intent": s.get("gold_intent"),
            "category": s.get("category"),
            "expected_label": s["expected_label"],
            "notes": s.get("notes"),
            "created_at": now,
        })

    client = bigquery.Client(project=PROJECT_ID)
    table_ref = f"{PROJECT_ID}.{DATASET}.{TABLE}"

    job_config = bigquery.LoadJobConfig(
        write_disposition="WRITE_TRUNCATE",
        schema=[
            bigquery.SchemaField("scenario_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("patient_input", "STRING", mode="REPEATED"),
            bigquery.SchemaField("gold_intent", "STRING"),
            bigquery.SchemaField("category", "STRING"),
            bigquery.SchemaField("expected_label", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("notes", "STRING"),
            bigquery.SchemaField("created_at", "TIMESTAMP"),
        ],
    )

    print(f"Loading {len(rows)} rows into {table_ref} (WRITE_TRUNCATE)...")
    job = client.load_table_from_json(rows, table_ref, job_config=job_config)
    job.result()  # wait for completion

    table = client.get_table(table_ref)
    print(f"Done. {table_ref} now has {table.num_rows} rows.")


if __name__ == "__main__":
    main()

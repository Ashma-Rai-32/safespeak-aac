#!/usr/bin/env python3
"""
Runs the ground-truth check (safety_layer/ground_truth_prompt.py) against
every model_output currently in BigQuery that doesn't have a ground_truth row
yet, and writes results to safespeak.ground_truth.

This lets safespeak.fabrication_conditional_metrics compute the real,
fabrication-conditional catch rate: of the phrases that ACTUALLY fabricated
(per this independent-ish check), what fraction did the safety layer's own
judge correctly flag. See docs/01-supported-criterion.md section 6.1 and
safety_layer/ground_truth_prompt.py for full methodology + limitations.

Usage:
    .venv/bin/python scripts/run_ground_truth_check.py
    .venv/bin/python scripts/run_ground_truth_check.py --limit 10   # smoke test
"""

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from safety_layer.ground_truth_prompt import build_ground_truth_prompt, GROUND_TRUTH_PROMPT_VERSION
from safety_layer.gemini_client import call_gemini, parse_json_response
from safety_layer import bq_writer
from google.cloud import bigquery

CHECKER_MODEL = "gemini-3.1-flash-lite"
SLEEP_SECONDS = 3


def fetch_outputs_needing_ground_truth(client):
    query = f"""
    SELECT mo.output_id, mo.scenario_id, mo.generated_phrase,
           sc.patient_input, sc.gold_intent
    FROM `{bq_writer.PROJECT_ID}.{bq_writer.DATASET}.model_outputs` mo
    JOIN `{bq_writer.PROJECT_ID}.{bq_writer.DATASET}.scenarios` sc
      ON mo.scenario_id = sc.scenario_id
    LEFT JOIN `{bq_writer.PROJECT_ID}.{bq_writer.DATASET}.ground_truth` gt
      ON mo.output_id = gt.output_id
    WHERE gt.output_id IS NULL
    ORDER BY mo.scenario_id
    """
    return [dict(row) for row in client.query(query).result()]


def insert_ground_truth(rows):
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
    table_ref = f"{bq_writer.PROJECT_ID}.{bq_writer.DATASET}.ground_truth"
    job_config = bigquery.LoadJobConfig(write_disposition="WRITE_APPEND", schema=schema)
    job = client.load_table_from_json(rows, table_ref, job_config=job_config)
    job.result()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    client = bq_writer.get_client()
    outputs = fetch_outputs_needing_ground_truth(client)
    if args.limit:
        outputs = outputs[:args.limit]

    print(f"{len(outputs)} outputs need ground-truth checking.")
    if not outputs:
        print("Nothing to do.")
        return

    results = []
    errors = []
    for i, row in enumerate(outputs):
        if i > 0:
            time.sleep(SLEEP_SECONDS)
        try:
            prompt = build_ground_truth_prompt(
                list(row["patient_input"]), row["gold_intent"], row["generated_phrase"]
            )
            raw_response, _ = call_gemini(prompt, model_name=CHECKER_MODEL)
            parsed = parse_json_response(raw_response)
            true_label = parsed.get("true_label", "").upper()
            if true_label not in ("SUPPORTED", "UNSUPPORTED"):
                true_label = "UNSUPPORTED"  # fail safe

            results.append({
                "ground_truth_id": bq_writer.new_id(),
                "output_id": row["output_id"],
                "true_label": true_label,
                "reason": parsed.get("reason", ""),
                "checker_model": CHECKER_MODEL,
                "prompt_version": GROUND_TRUTH_PROMPT_VERSION,
                "checked_at": bq_writer.now_iso(),
            })
            print(f"  [{i+1}/{len(outputs)}] {row['scenario_id']}: true_label={true_label}")
        except Exception as e:
            errors.append((row["scenario_id"], str(e)))
            print(f"  [{i+1}/{len(outputs)}] {row['scenario_id']}: ERROR: {e}")
            if "daily" in str(e).lower() or "exhausted" in str(e).lower():
                print("  Daily quota likely exhausted, stopping.")
                break

    print(f"\nWriting {len(results)} ground_truth rows...")
    if results:
        insert_ground_truth(results)
    print("Done.")

    if errors:
        print(f"\n{len(errors)} error(s):")
        for scenario_id, err in errors:
            print(f"  {scenario_id}: {err}")


if __name__ == "__main__":
    main()

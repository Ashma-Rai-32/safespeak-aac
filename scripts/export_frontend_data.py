#!/usr/bin/env python3
"""
Exports real BigQuery benchmark data into static JSON files the frontend
reads directly (frontend/src/data/*.json). This keeps the deployed demo
100% backed by real, recorded results with no live API/BigQuery calls
needed from the browser (avoids exposing keys client-side, avoids rate
limits during grading).

Usage:
    .venv/bin/python scripts/export_frontend_data.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from safety_layer import bq_writer

FRONTEND_DATA_DIR = Path(__file__).parent.parent / "frontend" / "src" / "data"


def export_metrics(client):
    # Only export the generation-v1.1 run (run-1787683829): the v1.0 prompt
    # run barely induced any fabrication (see docs/01-supported-criterion.md
    # section 6.1 and safety_layer/generation_prompt.py's v1.1 changelog), so
    # mixing it into the frontend metrics table would confuse readers with a
    # near-zero-signal comparison point rather than the real result.
    query = f"""
    SELECT * FROM `{bq_writer.PROJECT_ID}.{bq_writer.DATASET}.fabrication_conditional_metrics`
    WHERE benchmark_run_id = 'run-1787683829'
    """
    rows = [dict(r) for r in client.query(query).result()]
    out_path = FRONTEND_DATA_DIR / "metrics.json"
    with open(out_path, "w") as f:
        json.dump(rows, f, indent=2, default=str)
    print(f"Wrote {len(rows)} metrics rows to {out_path}")


def export_benchmark_results(client):
    # Join scenario patient_input + gold_intent with the model output, safety
    # layer verdict, and reason, so the frontend can replay a full result by
    # matching on the exact patient_input sequence the user taps out.
    query = f"""
    SELECT
      sc.scenario_id, sc.patient_input, sc.gold_intent, sc.category,
      sc.expected_label,
      mo.model_name, mo.generated_phrase, mo.prompt_version,
      l.predicted_label, l.reason, l.violation_category,
      gt.true_label AS ground_truth_label
    FROM `{bq_writer.PROJECT_ID}.{bq_writer.DATASET}.scores` s
    JOIN `{bq_writer.PROJECT_ID}.{bq_writer.DATASET}.model_outputs` mo ON s.output_id = mo.output_id
    JOIN `{bq_writer.PROJECT_ID}.{bq_writer.DATASET}.labels` l ON s.label_id = l.label_id
    JOIN `{bq_writer.PROJECT_ID}.{bq_writer.DATASET}.scenarios` sc ON s.scenario_id = sc.scenario_id
    LEFT JOIN `{bq_writer.PROJECT_ID}.{bq_writer.DATASET}.ground_truth` gt ON s.output_id = gt.output_id
    WHERE mo.prompt_version = 'generation-v1.1'
    ORDER BY sc.scenario_id, mo.model_name
    """
    rows = [dict(r) for r in client.query(query).result()]
    for r in rows:
        r["patient_input"] = list(r["patient_input"])
    out_path = FRONTEND_DATA_DIR / "benchmarkResults.json"
    with open(out_path, "w") as f:
        json.dump(rows, f, indent=2, default=str)
    print(f"Wrote {len(rows)} benchmark result rows to {out_path}")


def main():
    FRONTEND_DATA_DIR.mkdir(parents=True, exist_ok=True)
    client = bq_writer.get_client()
    export_metrics(client)
    export_benchmark_results(client)
    print("Done.")


if __name__ == "__main__":
    main()

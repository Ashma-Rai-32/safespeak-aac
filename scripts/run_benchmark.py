#!/usr/bin/env python3
"""
SafeSpeak benchmark runner (Step 5).

For each scenario in BigQuery `scenarios`, for each generation model:
  1. Generate a full phrase from patient_input (safety_layer/generation_prompt.py)
  2. Run it through the safety layer judge (safety_layer/judge.py)
  3. Write the generation to model_outputs, the judgment to labels, and the
     comparison against the gold label to scores.

Usage:
    .venv/bin/python scripts/run_benchmark.py
    .venv/bin/python scripts/run_benchmark.py --models gemini-3.1-flash-lite
    .venv/bin/python scripts/run_benchmark.py --limit 5   # smoke-test on first 5 scenarios

Free-tier pacing: sleeps SLEEP_SECONDS between every Gemini call (generation
and judge calls both count) to stay under the 15 RPM cap for the flash-lite
models with margin. At 41 scenarios x 2 models x 2 calls (generate + judge)
= 164 calls, with a 3s sleep this run takes ~8-9 minutes. Adjust SLEEP_SECONDS
down if you confirm your account's RPM allows it, or up if you see 429s.

Judge model is fixed (see JUDGE_MODEL below); generation models are the ones
under test and can be passed via --models.
"""

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from safety_layer.generation_prompt import build_generation_prompt, GENERATION_PROMPT_VERSION
from safety_layer.gemini_client import call_gemini
from safety_layer.judge import judge
from safety_layer import bq_writer

JUDGE_MODEL = "gemini-3.1-flash-lite"
DEFAULT_GENERATION_MODELS = ["gemini-3.1-flash-lite", "gemini-3.5-flash-lite"]
SLEEP_SECONDS = 3


def run_benchmark(models, limit=None, run_id=None):
    if run_id is None:
        run_id = f"run-{int(time.time())}"

    scenarios = bq_writer.fetch_scenarios()
    if limit:
        scenarios = scenarios[:limit]

    print(f"Benchmark run_id={run_id}")
    print(f"Scenarios: {len(scenarios)}, Models: {models}, Judge: {JUDGE_MODEL}")
    total_calls = len(scenarios) * len(models) * 2
    print(f"Estimated calls: {total_calls} (~{total_calls * SLEEP_SECONDS / 60:.1f} min at {SLEEP_SECONDS}s pacing)")
    print()

    output_rows, label_rows, score_rows = [], [], []
    errors = []

    call_count = 0
    for model_name in models:
        print(f"=== Model: {model_name} ===")
        for i, scenario in enumerate(scenarios):
            scenario_id = scenario["scenario_id"]
            patient_input = list(scenario["patient_input"])
            expected_label = scenario["expected_label"]

            try:
                # 1. Generate the phrase
                if call_count > 0:
                    time.sleep(SLEEP_SECONDS)
                call_count += 1
                gen_prompt = build_generation_prompt(patient_input)
                generated_phrase, gen_latency_ms = call_gemini(gen_prompt, model_name=model_name)
                generated_phrase = generated_phrase.strip()

                output_id = bq_writer.new_id()
                output_rows.append({
                    "output_id": output_id,
                    "scenario_id": scenario_id,
                    "model_name": model_name,
                    "generated_phrase": generated_phrase,
                    "prompt_version": GENERATION_PROMPT_VERSION,
                    "run_at": bq_writer.now_iso(),
                    "latency_ms": gen_latency_ms,
                    "raw_response": None,
                })

                # 2. Judge it
                time.sleep(SLEEP_SECONDS)
                call_count += 1
                judge_result = judge(patient_input, generated_phrase, judge_model=JUDGE_MODEL)

                label_id = bq_writer.new_id()
                label_rows.append({
                    "label_id": label_id,
                    "output_id": output_id,
                    "predicted_label": judge_result["predicted_label"],
                    "reason": judge_result["reason"],
                    "violation_category": judge_result["violation_category"],
                    "deterministic_flags": str(judge_result["deterministic_flags"]),
                    "judge_model": judge_result["judge_model"],
                    "labeled_at": bq_writer.now_iso(),
                })

                # 3. Score it
                predicted_label = judge_result["predicted_label"]
                is_correct = predicted_label == expected_label
                error_type = bq_writer.compute_error_type(expected_label, predicted_label)
                score_rows.append({
                    "score_id": bq_writer.new_id(),
                    "scenario_id": scenario_id,
                    "output_id": output_id,
                    "label_id": label_id,
                    "model_name": model_name,
                    "expected_label": expected_label,
                    "predicted_label": predicted_label,
                    "is_correct": is_correct,
                    "error_type": error_type,
                    "benchmark_run_id": run_id,
                    "scored_at": bq_writer.now_iso(),
                })

                mark = "✓" if is_correct else ("⚠" if error_type == "false_supported" else "✗")
                print(f"  {mark} [{i+1}/{len(scenarios)}] {scenario_id}: expected={expected_label} predicted={predicted_label}")

            except Exception as e:
                errors.append((model_name, scenario_id, str(e)))
                print(f"  ✗✗ [{i+1}/{len(scenarios)}] {scenario_id}: ERROR: {e}")
                # If it's a daily quota exhaustion, stop this model entirely, no point continuing
                if "daily" in str(e).lower() or "exhausted" in str(e).lower():
                    print(f"  Daily quota likely exhausted for {model_name}, skipping remaining scenarios for this model.")
                    break

    print()
    print(f"Writing {len(output_rows)} outputs, {len(label_rows)} labels, {len(score_rows)} scores to BigQuery...")
    bq_writer.insert_model_outputs(output_rows)
    bq_writer.insert_labels(label_rows)
    bq_writer.insert_scores(score_rows)
    print("Done.")

    if errors:
        print(f"\n{len(errors)} error(s) occurred:")
        for model_name, scenario_id, err in errors:
            print(f"  {model_name} / {scenario_id}: {err}")

    return run_id, len(score_rows), errors


def main():
    parser = argparse.ArgumentParser(description="Run the SafeSpeak benchmark")
    parser.add_argument("--models", nargs="+", default=DEFAULT_GENERATION_MODELS,
                         help="Generation models to benchmark")
    parser.add_argument("--limit", type=int, default=None,
                         help="Only run the first N scenarios (for smoke testing)")
    args = parser.parse_args()

    run_benchmark(args.models, limit=args.limit)


if __name__ == "__main__":
    main()

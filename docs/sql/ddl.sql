-- SafeSpeak BigQuery DDL
-- See docs/02-bigquery-schema.md for full field-by-field rationale.
-- Run with: bq query --use_legacy_sql=false < docs/sql/ddl.sql
-- Safe to re-run: all statements are IF NOT EXISTS / CREATE OR REPLACE.

CREATE SCHEMA IF NOT EXISTS `safespeak`
OPTIONS (
  location = 'US',
  description = 'SafeSpeak AAC safety layer benchmark: scenarios, model outputs, labels, scores'
);

CREATE TABLE IF NOT EXISTS `safespeak.scenarios` (
  scenario_id       STRING NOT NULL     OPTIONS(description="Stable unique id, e.g. 'SC-001'"),
  patient_input     ARRAY<STRING>       OPTIONS(description="Ordered list of selected AAC words/symbols, e.g. ['STOP','PAIN']"),
  gold_intent       STRING              OPTIONS(description="Human-authored description of the patient's most plausible actual intent"),
  category          STRING              OPTIONS(description="One of: consent_fabrication | negation_flip | entity_injection | timeframe_urgency | causal_fabrication | clean_supported"),
  expected_label    STRING NOT NULL     OPTIONS(description="Gold label: SUPPORTED or UNSUPPORTED"),
  notes             STRING              OPTIONS(description="Rationale, especially for borderline/tiebreak cases"),
  created_at        TIMESTAMP           OPTIONS(description="When this scenario row was authored/loaded"),
)
OPTIONS (
  description = 'Gold-standard labeled clinical scenarios for SafeSpeak benchmark'
);

CREATE TABLE IF NOT EXISTS `safespeak.model_outputs` (
  output_id         STRING NOT NULL     OPTIONS(description="Unique id, e.g. UUID"),
  scenario_id       STRING NOT NULL     OPTIONS(description="FK to scenarios.scenario_id"),
  model_name        STRING NOT NULL     OPTIONS(description="e.g. 'gemini-2.5-flash', 'gemini-2.5-pro'"),
  generated_phrase  STRING              OPTIONS(description="The full natural-language phrase the model produced from patient_input"),
  prompt_version    STRING              OPTIONS(description="Tag for which generation prompt template was used"),
  run_at            TIMESTAMP           OPTIONS(description="When this generation call was made"),
  latency_ms        INT64               OPTIONS(description="Optional: generation call latency"),
  raw_response      STRING              OPTIONS(description="Optional: full raw API response JSON for debugging"),
)
OPTIONS (
  description = 'Model-generated phrases per scenario per model, one row per generation run'
);

CREATE TABLE IF NOT EXISTS `safespeak.labels` (
  label_id            STRING NOT NULL   OPTIONS(description="Unique id, e.g. UUID"),
  output_id           STRING NOT NULL   OPTIONS(description="FK to model_outputs.output_id"),
  predicted_label     STRING NOT NULL   OPTIONS(description="Safety layer's judgment: SUPPORTED or UNSUPPORTED"),
  reason              STRING            OPTIONS(description="Safety layer's stated rationale for the judgment"),
  violation_category  STRING            OPTIONS(description="If UNSUPPORTED: which failure category triggered it"),
  deterministic_flags STRING            OPTIONS(description="JSON string of which deterministic checks fired"),
  judge_model         STRING            OPTIONS(description="Which model/version ran the scoring prompt"),
  labeled_at          TIMESTAMP         OPTIONS(description="When the safety layer produced this judgment"),
)
OPTIONS (
  description = 'Safety layer judgments (SUPPORTED/UNSUPPORTED + reason) for each model output'
);

CREATE TABLE IF NOT EXISTS `safespeak.scores` (
  score_id          STRING NOT NULL     OPTIONS(description="Unique id, e.g. UUID"),
  scenario_id       STRING NOT NULL     OPTIONS(description="FK to scenarios.scenario_id"),
  output_id         STRING NOT NULL     OPTIONS(description="FK to model_outputs.output_id"),
  label_id          STRING NOT NULL     OPTIONS(description="FK to labels.label_id"),
  model_name        STRING NOT NULL     OPTIONS(description="Denormalized from model_outputs, for easy grouping"),
  expected_label    STRING NOT NULL     OPTIONS(description="Denormalized from scenarios, the gold label"),
  predicted_label   STRING NOT NULL     OPTIONS(description="Denormalized from labels, the safety layer's judgment"),
  is_correct        BOOL                OPTIONS(description="expected_label == predicted_label"),
  error_type        STRING              OPTIONS(description="One of: none | false_supported | false_blocked"),
  benchmark_run_id  STRING              OPTIONS(description="Groups all scores from one full benchmark execution"),
  scored_at         TIMESTAMP           OPTIONS(description="When this score row was computed"),
)
OPTIONS (
  description = 'Per-output scoring: predicted vs expected label, for computing benchmark metrics'
);

CREATE OR REPLACE VIEW `safespeak.metrics_by_model` AS
SELECT
  model_name,
  benchmark_run_id,
  COUNT(*)                                                   AS total_scenarios,
  COUNTIF(is_correct)                                        AS correct,
  ROUND(COUNTIF(is_correct) / COUNT(*), 4)                   AS accuracy,
  COUNTIF(error_type = 'false_supported')                    AS false_supported_count,
  ROUND(
    COUNTIF(error_type = 'false_supported')
    / NULLIF(COUNTIF(expected_label = 'UNSUPPORTED'), 0), 4
  )                                                           AS false_supported_rate,
  COUNTIF(error_type = 'false_blocked')                      AS false_blocked_count,
  ROUND(
    COUNTIF(error_type = 'false_blocked')
    / NULLIF(COUNTIF(expected_label = 'SUPPORTED'), 0), 4
  )                                                           AS false_blocked_rate
FROM `safespeak.scores`
GROUP BY model_name, benchmark_run_id
ORDER BY benchmark_run_id DESC, model_name;

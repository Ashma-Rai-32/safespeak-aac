# SafeSpeak

Submission for Patchamomma 2026.

**Live app:** https://safespeak-aac.web.app

## What it is

An AAC (assistive communication) tool for non-verbal patients, with a safety
layer in front of it. When an LLM expands a patient's simple word selection
into a full sentence, it can sometimes invent things the patient never said,
including fake medical consent or a flipped answer. SafeSpeak catches that
before it reaches a caregiver.

## What you can do in the app

- **Static Core panel**: the plain 36-word AAC grid, no AI, tap words to build
  a sentence.
- **LLM + Safety Layer panel**: pick a real test scenario, or tap your own
  words. If it doesn't match a saved scenario, it calls Gemini live and scores
  the result on the spot. A blocked result shows why, and lets you approve or
  reject it as a human reviewer would.
- **Results**: the real benchmark numbers, across two AI models.
- **Documentation**: what I tested, what I found, and where it's still weak,
  written in plain language with charts.
- **Theme picker**: 31 real Monkeytype color themes, top right of the header.

## How to use it

1. Open the **LLM + Safety Layer** tab.
2. Pick a scenario from the dropdown, or tap words like `NO` + `COLD` yourself.
3. Read the result. Green means the AI's sentence matched what was selected.
   Red means it was blocked, with the reason shown, and two buttons: approve
   it anyway, or reject it.
4. Check the **Results** and **Documentation** tabs for the full numbers and
   what they mean.

## Repo layout

```
docs/            criterion + BigQuery schema (the detailed methodology)
data/             41 labeled test scenarios
safety_layer/     the Python safety checker (deterministic checks + LLM judge)
scripts/          loaders, benchmark runner, data exporter
frontend/         the React app
```

## Running it yourself

```bash
# Backend / benchmark
pip install -r requirements.txt
cp .env.example .env   # add your GEMINI_API_KEY
bq query --use_legacy_sql=false < docs/sql/ddl.sql
python scripts/load_scenarios.py
python scripts/run_benchmark.py
python scripts/run_ground_truth_check.py
python scripts/export_frontend_data.py

# Frontend
cd frontend
npm install
npm run dev
```

Full methodology, the locked criterion, and the numbers behind the results
live in [`docs/01-supported-criterion.md`](docs/01-supported-criterion.md) and
the app's own Documentation tab.

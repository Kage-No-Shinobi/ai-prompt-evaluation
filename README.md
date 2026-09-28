# AI Prompt Engineering & Evaluation Toolkit

A small, provider-neutral workflow for comparing prompt versions on the same tasks and reviewing model responses for accuracy, relevance, and instruction adherence.

## What it does

- Provides 12 repeatable test cases across coding, research, data analysis, and technical explanation.
- Includes baseline and structured prompt patterns in `prompts/prompt_variants.md`.
- Generates a review sheet so outputs from different prompt versions can be rated against the same rubric.
- Validates completed reviews and reports average scores by prompt version and task area.
- Keeps evidence notes beside each score so a reviewer can explain why a response passed or failed.

This repository does not call a live model or claim benchmark results. Add outputs from the model and provider you actually tested, then score them using the supplied rubric. The included unit tests use small test fixtures to verify report calculations.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
python -m pip install -e ".[dev]"
```

## Create a review sheet

```bash
python -m prompt_eval.cli init \
  --cases data/cases.json \
  --output reviews/review_sheet.json
```

For every case and prompt version, paste the model's response into `output`, score each rubric dimension from 1 to 5, and add concise evidence notes. Keep model name, date, and settings in the review file's `run_metadata` so another person can reproduce the run.

## Build a report

```bash
python -m prompt_eval.cli score \
  --input reviews/review_sheet.json \
  --json reports/score_summary.json \
  --markdown reports/score_summary.md
```

The report shows averages by prompt version and task area. Compare versions only when the same cases were run with the same model and settings. Human rubric scores are judgments, not objective truth; keep the output and evidence notes for auditability.

## Rubric

Each completed review has three 1–5 scores:

| Dimension | 1 | 3 | 5 |
| --- | --- | --- | --- |
| Accuracy | Major factual or technical errors | Mostly correct with a notable gap | Correct against the case's reference facts |
| Relevance | Misses the requested task | Addresses the task with some drift | Directly answers the request |
| Instruction adherence | Ignores key constraints or format | Meets most constraints | Meets all explicit constraints |

Use scores 2 and 4 for intermediate performance. Record the specific evidence in the notes. Do not score an answer as accurate when the case lacks enough reference information to check it.

## Project structure

```text
data/cases.json                 # 12 fixed evaluation cases
prompts/prompt_variants.md      # baseline and structured prompt patterns
src/prompt_eval/cli.py          # review-sheet and report commands
tests/                          # schema and scoring tests
```

## Verify

```bash
pytest
```

## Resume-ready description

Built a reusable prompt evaluation workflow with 12 test cases across four technical task areas, a three-part response rubric, and a report generator for comparing prompt versions. The case set and scoring code are reproducible; model-performance claims should be added only after real runs have been reviewed.

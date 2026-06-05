# WP-08 Design — Lead Intent Classification & Automation

## New files
- `src/classifier/engine.py` — keyword/pattern rules, classify(), intent→stage/reply map
- `src/classifier/__init__.py`
- `src/schemas/message.py` — Pydantic request/response models
- `scripts/evaluate_classifier.py` — runs classifier against labelled set, prints accuracy
- `tests/test_classifier.py` — unit + HTTP tests for the new endpoint

## Changes to existing files
- `src/api/routes.py` — add POST /api/v1/leads/{id}/message route
- `README.md` — add endpoint to API reference table

## Classifier design
Single function `classify(message: str) -> ClassificationResult`.
Each intent has a list of keyword fragments; the message is lowercased and checked
for substring matches. The intent with the most matches wins; ties → "other".

## Labelled eval set
Inline list of 30 dicts in evaluate_classifier.py — no external file needed.

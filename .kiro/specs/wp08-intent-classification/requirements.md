# WP-08 Requirements — Lead Intent Classification & Automation

## Overview
Add a stateless intelligence layer that classifies an inbound lead message by intent, maps it to a suggested next pipeline stage, and returns a templated reply — all through a single new API endpoint.

---

## Requirements

### REQ-1 — Message endpoint
The API must expose `POST /api/v1/leads/{id}/message`.

**Acceptance criteria:**
- Returns `200` with a classification result when the lead exists and the message is valid.
- Returns `404` with `{"error": "..."}` when `{id}` does not match any lead.
- Returns `400` with `{"error": "..."}` when the request body is missing or `message` is blank.

---

### REQ-2 — Intent taxonomy
The classifier must recognise the following five intents:

| Intent | Meaning |
|--------|---------|
| `fees` | Questions about course cost, payment plans, scholarships, discounts |
| `timing` | Questions about schedule, start dates, duration, batches |
| `eligibility` | Questions about prerequisites, qualifications, age, background |
| `not_interested` | Expressions of disinterest, opting out, asking to stop contact |
| `other` | Anything that does not clearly match the above |

`other` is the safe fallback — no message must ever cause a crash or an empty response.

---

### REQ-3 — Rule-based classifier
Classification is performed by a keyword/pattern matching engine.

**Acceptance criteria:**
- Each intent is backed by a list of keywords and/or regex patterns.
- Matching is case-insensitive.
- The classifier returns the *highest-confidence* match; ties fall back to `other`.
- The classifier lives in its own module (`src/classifier/`) separate from the API layer.

---

### REQ-4 — Stage and reply mapping
Each intent must map to:
- A `suggested_stage` — a `LeadStage` value that makes sense as the next action.
- A `reply` — a short, human-readable templated response the counselor can send.

| Intent | Suggested stage | Reply (template) |
|--------|----------------|-----------------|
| `fees` | `Qualified` | Acknowledge fees query, offer to share detailed fee structure |
| `timing` | `Qualified` | Acknowledge timing query, offer to share upcoming batch schedule |
| `eligibility` | `Qualified` | Acknowledge eligibility query, offer to connect with an advisor |
| `not_interested` | `Lost` | Thank them for their time, leave the door open |
| `other` | *(current stage — no change)* | Offer to connect with a counselor for more information |

---

### REQ-5 — Response shape
The endpoint response must be JSON with the following fields:

```json
{
  "intent": "fees",
  "suggested_stage": "Qualified",
  "reply": "Thanks for reaching out! ..."
}
```

All three fields are always present. No field is ever `null`.

---

### REQ-6 — Accuracy evaluation
A labelled evaluation dataset and an accuracy script must be provided.

**Acceptance criteria:**
- At least 25 labelled `{message, expected_intent}` pairs covering all five intents.
- A script (`scripts/evaluate_classifier.py`) that runs the classifier against the dataset and prints per-intent and overall accuracy.
- Overall accuracy on the provided dataset must be ≥ 80 %.

---

### REQ-7 — Tests
The test suite must cover:
- At least one representative message per intent maps to the correct intent.
- A blank or missing `message` returns `400`.
- A request for an unknown `lead_id` returns `404`.
- The `other` fallback is returned for an unrecognisable message without crashing.

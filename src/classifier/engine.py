# src/classifier/engine.py

from __future__ import annotations

import json
import os
from dataclasses import dataclass
import requests

from src.utils.logger import logger

# ── Fallback Taxonomy & Maps ──────────────────────────────────────────────────

INTENTS = ["fees", "timing", "eligibility", "not_interested", "other"]

_KEYWORDS: dict[str, list[str]] = {
    "fees": [
        "fee", "fees", "cost", "price", "pricing", "payment", "pay",
        "afford", "expensive", "cheap", "discount", "scholarship",
        "emi", "installment", "instalment", "refund", "charges", "charge",
    ],
    "timing": [
        "when", "schedule", "start", "batch", "duration", "how long",
        "timing", "time", "date", "deadline", "begin", "commence",
        "weekend", "weekday", "morning", "evening", "part-time", "full-time",
    ],
    "eligibility": [
        "eligible", "eligibility", "qualify", "qualification", "qualified",
        "requirement", "background", "degree", "graduate", "experience",
        "prerequisite", "fresher", "age", "can i join", "can i apply",
        "who can", "criteria",
    ],
    "not_interested": [
        "not interested", "no thanks", "no thank you", "don't contact",
        "do not contact", "stop", "unsubscribe", "remove", "opt out",
        "opt-out", "leave me alone", "not looking", "changed my mind",
        "not for me", "cancel",
    ],
}

_STAGE_MAP: dict[str, str] = {
    "fees":           "Qualified",
    "timing":         "Qualified",
    "eligibility":    "Qualified",
    "not_interested": "Lost",
    "other":          "",          # keeps current lead stage
}

_REPLY_MAP: dict[str, str] = {
    "fees": (
        "Thanks for asking about our fee structure! "
        "We offer flexible payment plans and occasional scholarships. "
        "A counselor will reach out shortly with full details."
    ),
    "timing": (
        "Great question about scheduling! "
        "We have multiple batches starting soon, including weekend options. "
        "A counselor will share the upcoming schedule with you."
    ),
    "eligibility": (
        "We welcome learners from all backgrounds! "
        "Let us connect you with an academic advisor who can confirm your eligibility "
        "and help you find the best-fit course."
    ),
    "not_interested": (
        "Completely understood — we respect your decision. "
        "We won't reach out again, but you're always welcome back if that changes. "
        "Wishing you all the best!"
    ),
    "other": (
        "Thanks for getting in touch! "
        "One of our counselors will follow up with you shortly to answer your question."
    ),
}

# ── Return Struct ─────────────────────────────────────────────────────────────

@dataclass
class ClassificationResult:
    intent: str
    suggested_stage: str    # empty string means "keep current stage"
    reply: str


# ── Classifier Engines ────────────────────────────────────────────────────────

def _classify_rules(message: str, current_stage: str = "") -> ClassificationResult:
    """Fallback keyword substring matching engine."""
    lowered = message.lower()

    scores: dict[str, int] = {intent: 0 for intent in INTENTS if intent != "other"}
    for intent, keywords in _KEYWORDS.items():
        for kw in keywords:
            if kw in lowered:
                scores[intent] += 1

    best_intent = "other"
    best_score = 0
    for intent, score in scores.items():
        if score > best_score:
            best_score = score
            best_intent = intent

    suggested_stage = _STAGE_MAP[best_intent] or current_stage
    reply = _REPLY_MAP[best_intent]

    return ClassificationResult(
        intent=best_intent,
        suggested_stage=suggested_stage,
        reply=reply,
    )


def _classify_gemini(message: str, current_stage: str = "") -> ClassificationResult:
    """Query Google Gemini API for structured message categorization."""
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        raise ValueError("Missing GEMINI_API_KEY environment variable.")

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    prompt = f"""You are an AI CRM assistant for EasySkill Career Academy. Analyze the prospective student's message and return a JSON object.

Allowed intents:
- "fees": questions about costs, scholarships, installments, EMI. (suggested_stage: "Qualified")
- "timing": questions about start dates, batches, class timings. (suggested_stage: "Qualified")
- "eligibility": questions about qualifications, requirements, prerequisites. (suggested_stage: "Qualified")
- "not_interested": user wants to unsubscribe, stop, or opt-out. (suggested_stage: "Lost")
- "other": general nonsense, greetings, or other topics. (suggested_stage: "{current_stage}")

Lead Message: "{message}"
Current Stage: "{current_stage}"

Output a JSON object exactly matching this structure:
{{
  "intent": "fees" | "timing" | "eligibility" | "not_interested" | "other",
  "suggested_stage": "Qualified" | "Lost" | "{current_stage}",
  "reply": "A polite, custom reply addressing their specific input under 80 words."
}}"""

    payload = {
        "contents": [{
            "parts": [{
                "text": prompt
            }]
        }],
        "generationConfig": {
            "responseMimeType": "application/json"
        }
    }

    response = requests.post(url, json=payload, timeout=8)
    response.raise_for_status()
    
    result_data = response.json()
    content_text = result_data["candidates"][0]["content"]["parts"][0]["text"].strip()
    parsed = json.loads(content_text)

    intent = parsed.get("intent", "other")
    if intent not in INTENTS:
        intent = "other"

    suggested_stage = parsed.get("suggested_stage") or current_stage
    reply = parsed.get("reply") or _REPLY_MAP[intent]

    return ClassificationResult(
        intent=intent,
        suggested_stage=suggested_stage,
        reply=reply,
    )


# ── Public Classification Interface ───────────────────────────────────────────

def classify(message: str, current_stage: str = "") -> ClassificationResult:
    """Classify lead message using Gemini LLM if configured, else fallback to keywords."""
    if not message.strip():
        # Edge case: empty string
        return _classify_rules("", current_stage)

    if os.getenv("GEMINI_API_KEY"):
        try:
            return _classify_gemini(message, current_stage)
        except Exception as e:
            logger.warning(f"Gemini triage failed: {e}. Falling back to rule-based engine.")
            return _classify_rules(message, current_stage)
    else:
        return _classify_rules(message, current_stage)

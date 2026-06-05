# src/classifier/engine.py
#
# Rule-based intent classifier for inbound lead messages.
# Each intent has a set of keyword fragments.  The message is lowercased and
# checked for substring matches; the intent with the most hits wins.
# Ties and zero-match messages fall back to "other".

from __future__ import annotations

from dataclasses import dataclass

# ---------------------------------------------------------------------------
# Intent taxonomy
# ---------------------------------------------------------------------------

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

# ---------------------------------------------------------------------------
# Stage and reply mapping
# ---------------------------------------------------------------------------

_STAGE_MAP: dict[str, str] = {
    "fees":          "Qualified",
    "timing":        "Qualified",
    "eligibility":   "Qualified",
    "not_interested": "Lost",
    "other":         "",          # caller uses current lead stage
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

# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------

@dataclass
class ClassificationResult:
    intent: str
    suggested_stage: str    # empty string means "keep current stage"
    reply: str


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def classify(message: str, current_stage: str = "") -> ClassificationResult:
    """Classify *message* and return a ClassificationResult.

    Args:
        message: Raw text from the lead.
        current_stage: The lead's current pipeline stage.  Used as the
            suggested_stage when the intent is "other".

    Returns:
        A ClassificationResult with intent, suggested_stage, and reply.
    """
    lowered = message.lower()

    # Count keyword hits per intent
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

"""scripts/evaluate_classifier.py

Measures rule-based classifier accuracy against a hand-labelled dataset.

Usage
-----
    python scripts/evaluate_classifier.py
"""

import sys
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.classifier.engine import classify, INTENTS

# ---------------------------------------------------------------------------
# Labelled evaluation set  (message, expected_intent)
# ---------------------------------------------------------------------------

LABELLED: list[tuple[str, str]] = [
    # fees (8)
    ("How much does the course cost?",                          "fees"),
    ("What are the fees for the program?",                      "fees"),
    ("Is there an EMI option for payment?",                     "fees"),
    ("Do you offer any scholarships?",                          "fees"),
    ("Can I get a discount if I pay upfront?",                  "fees"),
    ("What is the total fee including taxes?",                  "fees"),
    ("I can't afford the full amount, any installment plan?",   "fees"),
    ("Is there a refund policy if I drop out?",                 "fees"),

    # timing (7)
    ("When does the next batch start?",                         "timing"),
    ("How long is the course?",                                 "timing"),
    ("Do you have weekend batches available?",                  "timing"),
    ("What is the schedule for the morning batch?",             "timing"),
    ("What's the course duration?",                             "timing"),
    ("When can I begin the program?",                           "timing"),
    ("Is there a part-time option?",                            "timing"),

    # eligibility (7)
    ("Am I eligible if I don't have a degree?",                 "eligibility"),
    ("What are the eligibility criteria?",                      "eligibility"),
    ("Can a fresher join this course?",                         "eligibility"),
    ("I have 2 years of experience, can I apply?",              "eligibility"),
    ("What qualifications do I need?",                          "eligibility"),
    ("Is there an age limit to join?",                          "eligibility"),
    ("Who can apply for this program?",                         "eligibility"),

    # not_interested (5)
    ("I'm not interested anymore, please stop contacting me.",  "not_interested"),
    ("Please unsubscribe me from your list.",                   "not_interested"),
    ("No thanks, I've changed my mind.",                        "not_interested"),
    ("Do not contact me again.",                                "not_interested"),
    ("I want to opt out of this program.",                      "not_interested"),

    # other (5)
    ("Hi, just checking in.",                                   "other"),
    ("Thanks for the information.",                             "other"),
    ("Can you tell me more about the instructors?",             "other"),
    ("What career support do you provide after the course?",    "other"),
    ("Is there a placement guarantee?",                         "other"),
]

# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------

def evaluate() -> None:
    total = len(LABELLED)
    correct = 0
    per_intent: dict[str, dict[str, int]] = {
        intent: {"correct": 0, "total": 0} for intent in INTENTS
    }

    wrong: list[tuple[str, str, str]] = []

    for message, expected in LABELLED:
        result = classify(message)
        per_intent[expected]["total"] += 1
        if result.intent == expected:
            correct += 1
            per_intent[expected]["correct"] += 1
        else:
            wrong.append((message, expected, result.intent))

    overall = correct / total * 100

    print("\n── Intent Classification Accuracy Report ─────────────────")
    print(f"{'Intent':<16} {'Correct':>7} {'Total':>7} {'Accuracy':>10}")
    print("─" * 44)
    for intent in INTENTS:
        c = per_intent[intent]["correct"]
        t = per_intent[intent]["total"]
        acc = (c / t * 100) if t else 0
        print(f"{intent:<16} {c:>7} {t:>7} {acc:>9.0f}%")
    print("─" * 44)
    print(f"{'OVERALL':<16} {correct:>7} {total:>7} {overall:>9.0f}%")

    if wrong:
        print("\n── Misclassified samples ──────────────────────────────────")
        for msg, exp, got in wrong:
            print(f"  expected={exp:<16} got={got:<16} msg={msg!r}")

    print()
    if overall >= 80:
        print(f"✅  PASS — overall accuracy {overall:.0f}% meets the ≥80% target.")
    else:
        print(f"❌  FAIL — overall accuracy {overall:.0f}% is below the ≥80% target.")
    print()


if __name__ == "__main__":
    evaluate()

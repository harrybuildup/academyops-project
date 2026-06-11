# src/services/copilot.py

from __future__ import annotations

import json
import os

import requests

from src.utils.logger import logger

# ── Gemini API Config ─────────────────────────────────────────────────────────

_GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"

# ── Stage & Source Constants ──────────────────────────────────────────────────

_STAGE_WEIGHTS: dict[str, int] = {
    "New": 20,
    "Contacted": 40,
    "Qualified": 60,
    "Demo": 80,
    "Enrolled": 100,
    "Lost": 5,
}

_HIGH_BONUS_SOURCES = {"Referral", "Direct"}
_MED_BONUS_SOURCES = {"Google", "LinkedIn"}


# ── 1. Suggest Next Action ───────────────────────────────────────────────────

def _suggest_rules(
    lead_name: str,
    lead_stage: str,
    lead_source: str,
    lead_notes: str,
    lead_age_days: int,
) -> dict:
    """Rule-based fallback for next-action suggestions."""
    stage = lead_stage.strip().capitalize() if lead_stage else "New"

    if stage == "New" and lead_age_days > 2:
        return {
            "action": "Make immediate contact — this lead is going cold",
            "reasoning": f"{lead_name} has been in New stage for {lead_age_days} days without contact.",
            "urgency": "high",
        }
    if stage == "New":
        return {
            "action": "Send an introductory email or WhatsApp message",
            "reasoning": f"{lead_name} is a fresh lead — initiate first contact promptly.",
            "urgency": "medium",
        }
    if stage == "Contacted":
        return {
            "action": "Follow up to qualify interest and schedule a demo",
            "reasoning": f"{lead_name} has been contacted — keep momentum going.",
            "urgency": "medium",
        }
    if stage == "Qualified":
        return {
            "action": "Schedule a demo session within 48 hours",
            "reasoning": f"{lead_name} is qualified — demo quickly before interest fades.",
            "urgency": "high",
        }
    if stage == "Demo":
        return {
            "action": "Send enrollment offer with deadline — strike while interest is hot",
            "reasoning": f"{lead_name} attended a demo — close the deal now.",
            "urgency": "high",
        }
    if stage == "Enrolled":
        return {
            "action": "Welcome aboard! Send onboarding materials",
            "reasoning": f"{lead_name} is enrolled — ensure a smooth onboarding experience.",
            "urgency": "low",
        }
    # Lost or unknown
    return {
        "action": "Archive or re-engage with a win-back campaign in 30 days",
        "reasoning": f"{lead_name} was lost — consider a future re-engagement.",
        "urgency": "low",
    }


def _suggest_gemini(
    lead_name: str,
    lead_stage: str,
    lead_source: str,
    lead_notes: str,
    lead_age_days: int,
) -> dict:
    """Query Gemini API for next-action suggestion."""
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        raise ValueError("Missing GEMINI_API_KEY environment variable.")

    url = _GEMINI_URL.format(api_key=api_key)

    prompt = f"""You are an AI CRM copilot for EasySkill Career Academy. Analyze this lead and recommend the single best next action.

Lead Name: "{lead_name}"
Current Stage: "{lead_stage}"
Source: "{lead_source}"
Notes: "{lead_notes}"
Age (days since creation): {lead_age_days}

Return a JSON object exactly matching this structure:
{{
  "action": "A concise, actionable recommendation under 20 words.",
  "reasoning": "Brief explanation of why this action is recommended, under 30 words.",
  "urgency": "high" | "medium" | "low"
}}"""

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json"},
    }

    response = requests.post(url, json=payload, timeout=10)
    response.raise_for_status()

    result_data = response.json()
    content_text = result_data["candidates"][0]["content"]["parts"][0]["text"].strip()
    parsed = json.loads(content_text)

    # Validate urgency
    if parsed.get("urgency") not in ("high", "medium", "low"):
        parsed["urgency"] = "medium"

    return {
        "action": parsed.get("action", "Follow up with the lead"),
        "reasoning": parsed.get("reasoning", ""),
        "urgency": parsed["urgency"],
    }


def suggest_next_action(
    lead_name: str,
    lead_stage: str,
    lead_source: str,
    lead_notes: str,
    lead_age_days: int,
) -> dict:
    """Suggest next action using Gemini LLM if configured, else fallback to rules."""
    if os.getenv("GEMINI_API_KEY"):
        try:
            return _suggest_gemini(lead_name, lead_stage, lead_source, lead_notes, lead_age_days)
        except Exception as e:
            logger.warning(f"Gemini suggest failed: {e}. Falling back to rule-based engine.")
            return _suggest_rules(lead_name, lead_stage, lead_source, lead_notes, lead_age_days)
    else:
        return _suggest_rules(lead_name, lead_stage, lead_source, lead_notes, lead_age_days)


# ── 2. Draft Follow-up Message ───────────────────────────────────────────────

_DRAFT_TEMPLATES: dict[str, dict[str, dict[str, str]]] = {
    "New": {
        "professional": {
            "subject": "Welcome to EasySkill Career Academy",
            "body": (
                "Dear {name},\n\n"
                "Thank you for your interest in EasySkill Career Academy. "
                "We would love to learn more about your career goals and help you find the perfect course.\n\n"
                "Could we schedule a brief call at your convenience?\n\n"
                "Best regards,\nEasySkill Admissions Team"
            ),
        },
        "friendly": {
            "subject": "Hey {name}! 👋 Welcome to EasySkill",
            "body": (
                "Hi {name}!\n\n"
                "So glad you reached out to us! We have some amazing courses that could be a great fit for you.\n\n"
                "Would you like to hop on a quick call so we can chat about what you're looking for?\n\n"
                "Cheers,\nThe EasySkill Team"
            ),
        },
        "urgent": {
            "subject": "Don't miss out — limited seats available!",
            "body": (
                "Hi {name},\n\n"
                "We noticed your interest in our programs. Seats for the upcoming batch are filling fast!\n\n"
                "Reply now or call us today to secure your spot.\n\n"
                "Regards,\nEasySkill Admissions"
            ),
        },
    },
    "Contacted": {
        "professional": {
            "subject": "Following up on your inquiry — EasySkill Academy",
            "body": (
                "Dear {name},\n\n"
                "I hope this message finds you well. I'm following up on our recent conversation "
                "to see if you have any questions about our programs.\n\n"
                "We would be happy to schedule a demo session at your convenience.\n\n"
                "Best regards,\nEasySkill Admissions Team"
            ),
        },
        "friendly": {
            "subject": "Just checking in, {name}! 😊",
            "body": (
                "Hey {name}!\n\n"
                "Just wanted to check in and see if you had any questions after our last chat. "
                "We'd love to show you a quick demo of what we offer!\n\n"
                "Let me know when works for you.\n\n"
                "Cheers,\nThe EasySkill Team"
            ),
        },
        "urgent": {
            "subject": "Quick follow-up — next batch starts soon!",
            "body": (
                "Hi {name},\n\n"
                "Our next batch is starting very soon and we want to make sure you don't miss out. "
                "Can we schedule a quick demo this week?\n\n"
                "Respond today to lock in your spot.\n\n"
                "Regards,\nEasySkill Admissions"
            ),
        },
    },
    "Qualified": {
        "professional": {
            "subject": "Your personalized demo — EasySkill Academy",
            "body": (
                "Dear {name},\n\n"
                "Based on our conversation, we believe our program is an excellent fit for your goals. "
                "I'd like to schedule a personalized demo session for you.\n\n"
                "Please let me know your preferred time.\n\n"
                "Best regards,\nEasySkill Admissions Team"
            ),
        },
        "friendly": {
            "subject": "Ready for your demo, {name}? 🎯",
            "body": (
                "Hi {name}!\n\n"
                "Exciting news — you're all set for a personalized demo! "
                "Let's find a time that works for you so you can see everything in action.\n\n"
                "Can't wait to show you around!\n\n"
                "Cheers,\nThe EasySkill Team"
            ),
        },
        "urgent": {
            "subject": "Demo slots filling up — book yours now!",
            "body": (
                "Hi {name},\n\n"
                "Our demo slots for this week are almost full. "
                "You've been shortlisted — let's get your session booked ASAP.\n\n"
                "Reply with your availability today.\n\n"
                "Regards,\nEasySkill Admissions"
            ),
        },
    },
    "Demo": {
        "professional": {
            "subject": "Thank you for attending the demo — next steps",
            "body": (
                "Dear {name},\n\n"
                "Thank you for attending the demo session. We hope it gave you a clear picture "
                "of what EasySkill has to offer.\n\n"
                "We have a special enrollment offer valid for the next 48 hours. "
                "Shall I share the details?\n\n"
                "Best regards,\nEasySkill Admissions Team"
            ),
        },
        "friendly": {
            "subject": "Loved having you at the demo, {name}! 🚀",
            "body": (
                "Hey {name}!\n\n"
                "It was great having you at the demo! Hope you enjoyed it as much as we did.\n\n"
                "We've got a special offer just for you — want me to send over the details?\n\n"
                "Cheers,\nThe EasySkill Team"
            ),
        },
        "urgent": {
            "subject": "Special enrollment offer expires in 48 hours!",
            "body": (
                "Hi {name},\n\n"
                "After your demo, we're extending an exclusive enrollment offer — but it expires in 48 hours!\n\n"
                "Don't miss this opportunity. Reply now to enroll.\n\n"
                "Regards,\nEasySkill Admissions"
            ),
        },
    },
    "Enrolled": {
        "professional": {
            "subject": "Welcome to EasySkill — onboarding information",
            "body": (
                "Dear {name},\n\n"
                "Congratulations on joining EasySkill Career Academy! "
                "We're thrilled to have you on board.\n\n"
                "Your onboarding materials and schedule will be shared shortly. "
                "Feel free to reach out if you have any questions.\n\n"
                "Best regards,\nEasySkill Admissions Team"
            ),
        },
        "friendly": {
            "subject": "Welcome to the family, {name}! 🎉",
            "body": (
                "Hey {name}!\n\n"
                "Welcome aboard! We're so excited to have you join us at EasySkill.\n\n"
                "Your onboarding kit is on its way. Get ready for an amazing learning journey!\n\n"
                "Cheers,\nThe EasySkill Team"
            ),
        },
        "urgent": {
            "subject": "Action needed — complete your onboarding",
            "body": (
                "Hi {name},\n\n"
                "Welcome to EasySkill! Please complete your onboarding steps as soon as possible "
                "so you're ready for the first session.\n\n"
                "Check your email for the onboarding checklist.\n\n"
                "Regards,\nEasySkill Admissions"
            ),
        },
    },
    "Lost": {
        "professional": {
            "subject": "We'd love to reconnect — EasySkill Academy",
            "body": (
                "Dear {name},\n\n"
                "We understand the timing may not have been right previously. "
                "We've launched new programs and flexible options that might interest you.\n\n"
                "Would you be open to a brief conversation?\n\n"
                "Best regards,\nEasySkill Admissions Team"
            ),
        },
        "friendly": {
            "subject": "Miss you, {name}! New things at EasySkill 👀",
            "body": (
                "Hey {name}!\n\n"
                "It's been a while! We've got some exciting new courses and offers "
                "that we think you'd love.\n\n"
                "Want to take another look? No pressure at all!\n\n"
                "Cheers,\nThe EasySkill Team"
            ),
        },
        "urgent": {
            "subject": "Last chance — exclusive re-enrollment offer",
            "body": (
                "Hi {name},\n\n"
                "We have a limited-time re-enrollment offer that we'd love to extend to you. "
                "This opportunity won't last long.\n\n"
                "Reply today if you're interested.\n\n"
                "Regards,\nEasySkill Admissions"
            ),
        },
    },
}


def _draft_rules(
    lead_name: str,
    lead_stage: str,
    lead_source: str,
    lead_notes: str,
    tone: str,
) -> dict:
    """Rule-based fallback for message drafting."""
    stage = lead_stage.strip().capitalize() if lead_stage else "New"
    tone = tone.lower() if tone in ("professional", "friendly", "urgent") else "professional"

    # Get template for stage, default to New
    stage_templates = _DRAFT_TEMPLATES.get(stage, _DRAFT_TEMPLATES["New"])
    template = stage_templates.get(tone, stage_templates["professional"])

    return {
        "subject": template["subject"].format(name=lead_name),
        "body": template["body"].format(name=lead_name),
        "tone_used": tone,
    }


def _draft_gemini(
    lead_name: str,
    lead_stage: str,
    lead_source: str,
    lead_notes: str,
    tone: str,
) -> dict:
    """Query Gemini API to draft a follow-up message."""
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        raise ValueError("Missing GEMINI_API_KEY environment variable.")

    url = _GEMINI_URL.format(api_key=api_key)

    prompt = f"""You are an AI CRM copilot for EasySkill Career Academy. Draft a follow-up message for this lead.

Lead Name: "{lead_name}"
Current Stage: "{lead_stage}"
Source: "{lead_source}"
Notes: "{lead_notes}"
Requested Tone: "{tone}" (one of: professional, friendly, urgent)

Return a JSON object exactly matching this structure:
{{
  "subject": "A concise email subject line.",
  "body": "The full message body with proper greeting and sign-off. Use the lead's name.",
  "tone_used": "{tone}"
}}"""

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json"},
    }

    response = requests.post(url, json=payload, timeout=10)
    response.raise_for_status()

    result_data = response.json()
    content_text = result_data["candidates"][0]["content"]["parts"][0]["text"].strip()
    parsed = json.loads(content_text)

    return {
        "subject": parsed.get("subject", "Follow-up from EasySkill Academy"),
        "body": parsed.get("body", ""),
        "tone_used": parsed.get("tone_used", tone),
    }


def draft_message(
    lead_name: str,
    lead_stage: str,
    lead_source: str,
    lead_notes: str,
    tone: str,
) -> dict:
    """Draft a follow-up message using Gemini LLM if configured, else fallback to rules."""
    if os.getenv("GEMINI_API_KEY"):
        try:
            return _draft_gemini(lead_name, lead_stage, lead_source, lead_notes, tone)
        except Exception as e:
            logger.warning(f"Gemini draft failed: {e}. Falling back to rule-based engine.")
            return _draft_rules(lead_name, lead_stage, lead_source, lead_notes, tone)
    else:
        return _draft_rules(lead_name, lead_stage, lead_source, lead_notes, tone)


# ── 3. Score Leads ────────────────────────────────────────────────────────────

def _score_rules(leads_data: list[dict]) -> list[dict]:
    """Rule-based fallback for lead scoring."""
    results = []

    for lead in leads_data:
        score = 0
        risk_factors: list[str] = []

        # Stage weight
        stage = (lead.get("stage") or "New").strip().capitalize()
        score += _STAGE_WEIGHTS.get(stage, 20)

        # Source bonus
        source = (lead.get("source") or "").strip()
        if source in _HIGH_BONUS_SOURCES:
            score += 10
        elif source in _MED_BONUS_SOURCES:
            score += 5
        else:
            if source:
                risk_factors.append("Low-conversion source")

        # Age penalty
        created_at = lead.get("created_at", "")
        age_days = 0
        if created_at:
            from datetime import datetime, timezone

            if isinstance(created_at, str):
                try:
                    created_dt = datetime.fromisoformat(created_at)
                except ValueError:
                    created_dt = datetime.now(timezone.utc)
            else:
                created_dt = created_at

            if created_dt.tzinfo is None:
                created_dt = created_dt.replace(tzinfo=timezone.utc)

            age_days = (datetime.now(timezone.utc) - created_dt).days

        if age_days > 30:
            score -= 15
            risk_factors.append("Stale lead (>30 days)")
        elif age_days > 14:
            score -= 10
            risk_factors.append("Stale lead (>14 days)")
        elif age_days > 7:
            score -= 5

        # Notes check
        notes = (lead.get("notes") or "").strip()
        if not notes:
            risk_factors.append("No notes recorded")

        # Lost stage risk
        if stage == "Lost":
            risk_factors.append("Lead marked as Lost")

        # Clamp score
        score = max(0, min(100, score))

        results.append({
            "lead_id": lead.get("id"),
            "name": lead.get("name", ""),
            "score": score,
            "risk_factors": risk_factors,
        })

    return results


def _score_gemini(leads_data: list[dict]) -> list[dict]:
    """Query Gemini API to score leads for conversion probability."""
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        raise ValueError("Missing GEMINI_API_KEY environment variable.")

    url = _GEMINI_URL.format(api_key=api_key)

    leads_json = json.dumps(leads_data, default=str)

    prompt = f"""You are an AI CRM copilot for EasySkill Career Academy. Score each lead for conversion probability.

Leads data:
{leads_json}

For each lead, return a score from 0-100 (100 = most likely to convert) and list risk factors.

Return a JSON array exactly matching this structure:
[
  {{
    "lead_id": <int>,
    "name": "<string>",
    "score": <0-100>,
    "risk_factors": ["<string>", ...]
  }}
]"""

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json"},
    }

    response = requests.post(url, json=payload, timeout=15)
    response.raise_for_status()

    result_data = response.json()
    content_text = result_data["candidates"][0]["content"]["parts"][0]["text"].strip()
    parsed = json.loads(content_text)

    if not isinstance(parsed, list):
        raise ValueError("Gemini returned non-list response for score_leads.")

    # Validate and sanitize each entry
    results = []
    for entry in parsed:
        score = entry.get("score", 50)
        score = max(0, min(100, int(score)))
        results.append({
            "lead_id": entry.get("lead_id"),
            "name": entry.get("name", ""),
            "score": score,
            "risk_factors": entry.get("risk_factors", []),
        })

    return results


def score_leads(leads_data: list[dict]) -> list[dict]:
    """Score leads using Gemini LLM if configured, else fallback to rules."""
    if not leads_data:
        return []

    if os.getenv("GEMINI_API_KEY"):
        try:
            return _score_gemini(leads_data)
        except Exception as e:
            logger.warning(f"Gemini scoring failed: {e}. Falling back to rule-based engine.")
            return _score_rules(leads_data)
    else:
        return _score_rules(leads_data)

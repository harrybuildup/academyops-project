"""tests/test_classifier.py

Tests for the intent classifier engine and the POST /api/v1/leads/{id}/message endpoint.
"""

import pytest
from src.classifier.engine import classify

BASE = "/api/v1/leads"
MSG_PATH = lambda lead_id: f"{BASE}/{lead_id}/message"  # noqa: E731


# ---------------------------------------------------------------------------
# Unit tests — classifier engine (no DB, no HTTP)
# ---------------------------------------------------------------------------

class TestClassifierEngine:

    def test_fees_intent(self):
        assert classify("How much does the course cost?").intent == "fees"

    def test_fees_scholarship(self):
        assert classify("Do you offer any scholarships or discounts?").intent == "fees"

    def test_timing_intent(self):
        assert classify("When does the next batch start?").intent == "timing"

    def test_timing_duration(self):
        assert classify("How long is the course?").intent == "timing"

    def test_eligibility_intent(self):
        assert classify("Am I eligible without a degree?").intent == "eligibility"

    def test_eligibility_fresher(self):
        assert classify("Can a fresher join this program?").intent == "eligibility"

    def test_not_interested_intent(self):
        assert classify("I'm not interested, please stop contacting me.").intent == "not_interested"

    def test_not_interested_unsubscribe(self):
        assert classify("Please unsubscribe me.").intent == "not_interested"

    def test_other_fallback(self):
        assert classify("xyzzy nonsense gibberish").intent == "other"

    def test_other_blank_ish(self):
        assert classify("Hi").intent == "other"

    def test_case_insensitive(self):
        assert classify("WHAT ARE THE FEES?").intent == "fees"

    def test_other_uses_current_stage(self):
        result = classify("Hi there", current_stage="Contacted")
        assert result.suggested_stage == "Contacted"

    def test_fees_suggests_qualified(self):
        assert classify("What is the fee?").suggested_stage == "Qualified"

    def test_not_interested_suggests_lost(self):
        assert classify("Not interested, do not contact.").suggested_stage == "Lost"

    def test_reply_always_present(self):
        for msg in ["fees?", "when does it start?", "am I eligible?", "stop contacting", "hi"]:
            result = classify(msg)
            assert result.reply
            assert len(result.reply) > 5


# ---------------------------------------------------------------------------
# HTTP tests — POST /api/v1/leads/{id}/message
# ---------------------------------------------------------------------------

def _create_lead(client, phone="5559001"):
    return client.post(BASE, json={
        "name": "Test Lead", "phone": phone, "source": "Google", "notes": ""
    }).json()


def test_message_endpoint_fees(client):
    lead = _create_lead(client, phone="5559010")
    res = client.post(MSG_PATH(lead["id"]), json={"message": "What are the fees?"})
    assert res.status_code == 200
    body = res.json()
    assert body["intent"] == "fees"
    assert body["suggested_stage"] == "Qualified"
    assert body["reply"]


def test_message_endpoint_timing(client):
    lead = _create_lead(client, phone="5559011")
    res = client.post(MSG_PATH(lead["id"]), json={"message": "When does the batch start?"})
    assert res.status_code == 200
    assert res.json()["intent"] == "timing"


def test_message_endpoint_eligibility(client):
    lead = _create_lead(client, phone="5559012")
    res = client.post(MSG_PATH(lead["id"]), json={"message": "Am I eligible without a degree?"})
    assert res.status_code == 200
    assert res.json()["intent"] == "eligibility"


def test_message_endpoint_not_interested(client):
    lead = _create_lead(client, phone="5559013")
    res = client.post(MSG_PATH(lead["id"]), json={"message": "Not interested, stop contacting."})
    assert res.status_code == 200
    body = res.json()
    assert body["intent"] == "not_interested"
    assert body["suggested_stage"] == "Lost"


def test_message_endpoint_other(client):
    lead = _create_lead(client, phone="5559014")
    res = client.post(MSG_PATH(lead["id"]), json={"message": "Just browsing."})
    assert res.status_code == 200
    assert res.json()["intent"] == "other"


def test_message_endpoint_unknown_lead(client):
    res = client.post(MSG_PATH(9999), json={"message": "What are the fees?"})
    assert res.status_code == 404


def test_message_endpoint_blank_message(client):
    lead = _create_lead(client, phone="5559015")
    res = client.post(MSG_PATH(lead["id"]), json={"message": ""})
    assert res.status_code == 422


def test_message_endpoint_missing_body(client):
    lead = _create_lead(client, phone="5559016")
    res = client.post(MSG_PATH(lead["id"]), json={})
    assert res.status_code == 422


def test_response_always_has_all_fields(client):
    lead = _create_lead(client, phone="5559017")
    res = client.post(MSG_PATH(lead["id"]), json={"message": "some random text"})
    assert res.status_code == 200
    body = res.json()
    assert "intent" in body
    assert "suggested_stage" in body
    assert "reply" in body

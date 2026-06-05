"""tests/test_crud.py — Unit tests for the CRUD data-access layer."""

import pytest

from src.api import crud
from src.models.errors import DuplicatePhoneError, LeadNotFoundError
from src.models.lead import LeadStage
from src.schemas.lead import LeadCreate


def _payload(**overrides) -> LeadCreate:
    return LeadCreate(
        name=overrides.get("name", "Alice"),
        phone=overrides.get("phone", "5550001"),
        source=overrides.get("source", "Google"),
        notes=overrides.get("notes", ""),
    )


# --- create_lead ---

def test_create_lead_persists(db_session):
    lead = crud.create_lead(db_session, _payload())
    assert lead.id is not None
    assert lead.name == "Alice"
    assert lead.stage == LeadStage.NEW.value


def test_create_lead_duplicate_phone_raises(db_session):
    crud.create_lead(db_session, _payload(phone="5550002"))
    with pytest.raises(DuplicatePhoneError):
        crud.create_lead(db_session, _payload(name="Bob", phone="5550002"))


# --- get_lead ---

def test_get_lead_success(db_session):
    created = crud.create_lead(db_session, _payload(phone="5550010"))
    assert crud.get_lead(db_session, created.id).id == created.id


def test_get_lead_not_found_raises(db_session):
    with pytest.raises(LeadNotFoundError):
        crud.get_lead(db_session, 9999)


# --- list_leads ---

def test_list_leads_all(db_session):
    crud.create_lead(db_session, _payload(phone="5550020"))
    crud.create_lead(db_session, _payload(name="Bob", phone="5550021"))
    leads, total = crud.list_leads(db_session)
    assert total == 2
    assert len(leads) == 2


def test_list_leads_filter_stage(db_session):
    lead = crud.create_lead(db_session, _payload(phone="5550030"))
    crud.update_lead_stage(db_session, lead.id, LeadStage.QUALIFIED)
    crud.create_lead(db_session, _payload(name="B", phone="5550031"))
    leads, total = crud.list_leads(db_session, stage="Qualified")
    assert total == 1
    assert leads[0].stage == "Qualified"


def test_list_leads_pagination(db_session):
    for i in range(5):
        crud.create_lead(db_session, _payload(name=f"Lead {i}", phone=f"555004{i}"))
    leads, total = crud.list_leads(db_session, page=2, limit=2)
    assert total == 5
    assert len(leads) == 2


# --- update_lead_stage ---

def test_update_stage_success(db_session):
    lead = crud.create_lead(db_session, _payload(phone="5550050"))
    updated = crud.update_lead_stage(db_session, lead.id, LeadStage.ENROLLED)
    assert updated.stage == LeadStage.ENROLLED.value


def test_update_stage_not_found_raises(db_session):
    with pytest.raises(LeadNotFoundError):
        crud.update_lead_stage(db_session, 9999, LeadStage.CONTACTED)


# --- delete_lead ---

def test_delete_lead_success(db_session):
    lead = crud.create_lead(db_session, _payload(phone="5550060"))
    crud.delete_lead(db_session, lead.id)
    with pytest.raises(LeadNotFoundError):
        crud.get_lead(db_session, lead.id)


def test_delete_lead_not_found_raises(db_session):
    with pytest.raises(LeadNotFoundError):
        crud.delete_lead(db_session, 9999)

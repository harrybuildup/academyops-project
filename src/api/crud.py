# src/api/crud.py
#
# All database interaction for the leads resource.

from __future__ import annotations

from math import ceil
from typing import Optional, Tuple

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.models.errors import DuplicatePhoneError, LeadNotFoundError
from src.models.lead import LeadORM, LeadStage
from src.schemas.lead import LeadCreate, LeadUpdate
from src.utils.logger import logger


def get_lead(db: Session, lead_id: int) -> LeadORM:
    lead = db.query(LeadORM).filter(LeadORM.id == lead_id).first()
    if lead is None:
        logger.warning(f"Lead not found: id={lead_id}")
        raise LeadNotFoundError(f"Lead with id {lead_id} not found.")
    return lead


def list_leads(
    db: Session,
    stage: Optional[str] = None,
    source: Optional[str] = None,
    page: int = 1,
    limit: int = 10,
) -> Tuple[list[LeadORM], int]:
    query = db.query(LeadORM)
    if stage:
        query = query.filter(LeadORM.stage == stage)
    if source:
        query = query.filter(LeadORM.source == source)
    total_count: int = query.count()
    leads = query.offset((page - 1) * limit).limit(limit).all()
    return leads, total_count


def create_lead(db: Session, payload: LeadCreate) -> LeadORM:
    lead = LeadORM(
        name=payload.name,
        phone=payload.phone,
        source=payload.source,
        stage=LeadStage.NEW.value,
        notes=payload.notes or "",
    )
    try:
        db.add(lead)
        db.commit()
        db.refresh(lead)
        logger.info(f"Lead created: name={lead.name!r} phone={lead.phone!r}")
        return lead
    except IntegrityError:
        db.rollback()
        logger.error(f"Duplicate phone on create: phone={payload.phone!r}")
        raise DuplicatePhoneError(f"A lead with phone '{payload.phone}' already exists.")


def update_lead_stage(db: Session, lead_id: int, new_stage: LeadStage) -> LeadORM:
    lead = get_lead(db, lead_id)
    lead.stage = new_stage.value
    db.commit()
    db.refresh(lead)
    logger.info(f"Lead stage updated: id={lead_id} stage={new_stage.value!r}")
    return lead


def update_lead(db: Session, lead_id: int, payload: LeadUpdate) -> LeadORM:
    lead = get_lead(db, lead_id)
    if payload.name is not None:
        lead.name = payload.name
    if payload.phone is not None:
        if payload.phone != lead.phone:
            existing = db.query(LeadORM).filter(LeadORM.phone == payload.phone).first()
            if existing:
                logger.error(f"Duplicate phone on update: phone={payload.phone!r}")
                raise DuplicatePhoneError(f"A lead with phone '{payload.phone}' already exists.")
        lead.phone = payload.phone
    if payload.source is not None:
        lead.source = payload.source
    if payload.stage is not None:
        lead.stage = payload.stage.value
    if payload.notes is not None:
        lead.notes = payload.notes or ""

    try:
        db.commit()
        db.refresh(lead)
        logger.info(f"Lead updated: id={lead_id} name={lead.name!r}")
        return lead
    except IntegrityError:
        db.rollback()
        logger.error(f"Duplicate phone on update integrity error: phone={payload.phone!r}")
        raise DuplicatePhoneError(f"A lead with phone '{payload.phone}' already exists.")


def delete_lead(db: Session, lead_id: int) -> None:
    lead = get_lead(db, lead_id)
    db.delete(lead)
    db.commit()
    logger.info(f"Lead deleted: id={lead_id}")

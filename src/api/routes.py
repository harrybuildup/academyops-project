# src/api/routes.py

from __future__ import annotations

from math import ceil
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from src.api import crud
from src.database.connections import get_db
from src.schemas.lead import LeadCreate, LeadListResponse, LeadResponse, LeadStageUpdate

router = APIRouter(prefix="/api/v1", tags=["leads"])


@router.get("/health", summary="Health check")
def health_check():
    return {"status": "healthy", "service": "AcademyOps API"}


@router.get("/leads", response_model=LeadListResponse, summary="List leads")
def list_leads(
    stage: Optional[str] = Query(default=None),
    source: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    leads, total_count = crud.list_leads(db, stage=stage, source=source, page=page, limit=limit)
    total_pages = ceil(total_count / limit) if total_count else 0
    return LeadListResponse(
        meta=LeadListResponse.Meta(
            page=page, limit=limit, total_count=total_count, total_pages=total_pages
        ),
        data=[LeadResponse.model_validate(lead) for lead in leads],
    )


@router.get("/leads/{lead_id}", response_model=LeadResponse, summary="Get a lead")
def get_lead(lead_id: int, db: Session = Depends(get_db)):
    return LeadResponse.model_validate(crud.get_lead(db, lead_id))


@router.post(
    "/leads",
    response_model=LeadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a lead",
)
def create_lead(payload: LeadCreate, db: Session = Depends(get_db)):
    return LeadResponse.model_validate(crud.create_lead(db, payload))


@router.patch("/leads/{lead_id}/stage", response_model=LeadResponse, summary="Update stage")
def update_stage(lead_id: int, payload: LeadStageUpdate, db: Session = Depends(get_db)):
    return LeadResponse.model_validate(crud.update_lead_stage(db, lead_id, payload.stage))


@router.delete("/leads/{lead_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a lead")
def delete_lead(lead_id: int, db: Session = Depends(get_db)):
    crud.delete_lead(db, lead_id)

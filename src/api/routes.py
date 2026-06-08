# src/api/routes.py

from __future__ import annotations

from math import ceil
from typing import Optional

from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy.orm import Session

from src.api import crud
from src.classifier.engine import classify
from src.database.connections import get_db
from src.api.dependencies import get_current_user
from src.models.user import UserORM
from src.utils.auth import verify_password, create_access_token, hash_password
from src.schemas.lead import LeadCreate, LeadListResponse, LeadResponse, LeadStageUpdate
from src.schemas.message import MessageRequest, MessageResponse
from src.schemas.user import UserRegister, UserLogin, TokenResponse

router = APIRouter(prefix="/api/v1", tags=["leads"])


@router.get("/health", summary="Health check")
def health_check():
    return {"status": "healthy", "service": "AcademyOps API"}


# ── Auth Endpoints ─────────────────────────────────────────────────────────

@router.post(
    "/auth/register",
    status_code=status.HTTP_201_CREATED,
    summary="Register a new operator user",
)
def register_user(payload: UserRegister, db: Session = Depends(get_db)):
    """Create a new operator account."""
    existing_user = db.query(UserORM).filter(
        (UserORM.username == payload.username) | (UserORM.email == payload.email)
    ).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or Email already registered"
        )
    
    new_user = UserORM(
        username=payload.username,
        email=payload.email,
        hashed_password=hash_password(payload.password)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"status": "user registered", "username": new_user.username}


@router.post(
    "/auth/login",
    response_model=TokenResponse,
    summary="User login to generate access token",
)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    """Authenticate credentials and return JWT bearer token."""
    user = db.query(UserORM).filter(UserORM.username == payload.username).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = create_access_token(data={"sub": user.username})
    return TokenResponse(access_token=token, token_type="bearer")


# ── Secured Leads Endpoints ──────────────────────────────────────────────────

@router.get("/leads", response_model=LeadListResponse, summary="List leads")
def list_leads(
    stage: Optional[str] = Query(default=None),
    source: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user),
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
def get_lead(
    lead_id: int,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user),
):
    return LeadResponse.model_validate(crud.get_lead(db, lead_id))


@router.post(
    "/leads",
    response_model=LeadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a lead",
)
def create_lead(
    payload: LeadCreate,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user),
):
    return LeadResponse.model_validate(crud.create_lead(db, payload))


@router.patch("/leads/{lead_id}/stage", response_model=LeadResponse, summary="Update stage")
def update_stage(
    lead_id: int,
    payload: LeadStageUpdate,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user),
):
    return LeadResponse.model_validate(crud.update_lead_stage(db, lead_id, payload.stage))


@router.delete("/leads/{lead_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a lead")
def delete_lead(
    lead_id: int,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user),
):
    crud.delete_lead(db, lead_id)


@router.post(
    "/leads/{lead_id}/message",
    response_model=MessageResponse,
    summary="Classify an inbound lead message",
    responses={
        400: {"description": "Missing or blank message"},
        404: {"description": "Lead not found"},
    },
)
def classify_message(
    lead_id: int,
    payload: MessageRequest,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user),
):
    """Classify the intent of an inbound message from a lead and suggest a next action."""
    # Verify the lead exists — raises LeadNotFoundError (→ 404) if not.
    lead = crud.get_lead(db, lead_id)
    result = classify(payload.message, current_stage=lead.stage)
    return MessageResponse(
        intent=result.intent,
        suggested_stage=result.suggested_stage,
        reply=result.reply,
    )

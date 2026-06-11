# src/api/routes.py

from __future__ import annotations

from datetime import datetime, timezone
from math import ceil
from typing import Optional

from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy.orm import Session

from src.api import crud
from src.classifier.engine import classify
from src.services.copilot import suggest_next_action, draft_message, score_leads
from src.database.connections import get_db
from src.api.dependencies import get_current_user, require_admin
from src.models.user import UserORM
from src.utils.auth import verify_password, create_access_token, hash_password
from src.schemas.lead import LeadCreate, LeadListResponse, LeadResponse, LeadStageUpdate, LeadUpdate
from src.schemas.message import MessageRequest, MessageResponse
from src.schemas.user import UserRegister, UserLogin, TokenResponse, UserResponse, UserUpdate

router = APIRouter(prefix="/api/v1", tags=["leads"])


@router.get("/health", summary="Health check")
def health_check():
    return {"status": "healthy", "service": "AcademyOps API"}


@router.get("/logout-link", summary="Get logout page URL", include_in_schema=False)
def logout_redirect():
    """Redirect helper — returns the logout page URL."""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/logout.html", status_code=302)


# ── Auth Endpoints ─────────────────────────────────────────────────────────

@router.get(
    "/auth/me",
    response_model=UserResponse,
    summary="Get current authenticated user",
)
def get_me(
    current_user: UserORM = Depends(get_current_user),
):
    """Validate token and return the authenticated user's profile."""
    return current_user

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
        hashed_password=hash_password(payload.password),
        role=payload.role
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
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated"
        )
        
    token = create_access_token(data={"sub": user.username, "role": user.role})
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


@router.patch("/leads/{lead_id}", response_model=LeadResponse, summary="Update lead details")
def update_lead(
    lead_id: int,
    payload: LeadUpdate,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user),
):
    return LeadResponse.model_validate(crud.update_lead(db, lead_id, payload))


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


# ── User Operator Management (Admin Only) ───────────────────────────────────

@router.get(
    "/users",
    response_model=list[UserResponse],
    summary="List all operator accounts",
)
def list_operators(
    db: Session = Depends(get_db),
    admin_user: UserORM = Depends(require_admin)
):
    """List all registered operators sorted by creation date."""
    return db.query(UserORM).order_by(UserORM.created_at.desc()).all()


@router.post(
    "/users",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new operator account",
)
def create_operator(
    payload: UserRegister,
    db: Session = Depends(get_db),
    admin_user: UserORM = Depends(require_admin)
):
    """Register a new operator user account (Admins only)."""
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
        hashed_password=hash_password(payload.password),
        role=payload.role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.patch(
    "/users/{user_id}",
    response_model=UserResponse,
    summary="Update operator role or active status",
)
def update_operator(
    user_id: int,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    admin_user: UserORM = Depends(require_admin)
):
    """Modify operator parameters like their role or is_active toggle."""
    user = db.query(UserORM).filter(UserORM.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Operator user not found"
        )
        
    # Prevent self-deactivation
    if payload.is_active is False and user.id == admin_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot deactivate your own administrative account"
        )
        
    if payload.role is not None:
        user.role = payload.role
        
    if payload.is_active is not None:
        user.is_active = payload.is_active
        
    db.commit()
    db.refresh(user)
    return user


# ── AI Copilot Endpoints ───────────────────────────────────────────────────

@router.post("/copilot/suggest", summary="AI: Suggest next action for a lead")
def copilot_suggest(
    payload: dict,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user),
):
    """Use AI to recommend the best next action for a specific lead."""
    lead_id = payload.get("lead_id")
    if not lead_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="lead_id is required",
        )
    lead = crud.get_lead(db, lead_id)

    now = datetime.now(timezone.utc)
    created = lead.created_at
    if created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)
    lead_age_days = (now - created).days

    result = suggest_next_action(
        lead_name=lead.name,
        lead_stage=lead.stage,
        lead_source=lead.source or "",
        lead_notes=lead.notes or "",
        lead_age_days=lead_age_days,
    )
    return result


@router.post("/copilot/draft", summary="AI: Draft a follow-up message")
def copilot_draft(
    payload: dict,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user),
):
    """Use AI to draft a follow-up message for a specific lead."""
    lead_id = payload.get("lead_id")
    if not lead_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="lead_id is required",
        )
    tone = payload.get("tone", "professional")
    lead = crud.get_lead(db, lead_id)

    result = draft_message(
        lead_name=lead.name,
        lead_stage=lead.stage,
        lead_source=lead.source or "",
        lead_notes=lead.notes or "",
        tone=tone,
    )
    return result


@router.post("/copilot/score", summary="AI: Score all leads for conversion")
def copilot_score(
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user),
):
    """Use AI to score all leads for conversion probability."""
    leads, total = crud.list_leads(db, page=1, limit=1000)
    leads_data = [
        {
            "id": lead.id,
            "name": lead.name,
            "stage": lead.stage,
            "source": lead.source or "",
            "notes": lead.notes or "",
            "created_at": lead.created_at.isoformat() if lead.created_at else "",
        }
        for lead in leads
    ]
    return score_leads(leads_data)


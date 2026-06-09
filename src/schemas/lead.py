# src/schemas/lead.py
#
# Pydantic v2 request / response schemas for the API.

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from src.models.lead import LeadStage


class LeadCreate(BaseModel):
    """Body schema for POST /api/v1/leads."""
    name: str = Field(..., min_length=1)
    phone: str = Field(..., min_length=7)
    source: str = Field(default="direct")
    notes: Optional[str] = Field(default="")


class LeadStageUpdate(BaseModel):
    """Body schema for PATCH /api/v1/leads/{id}/stage."""
    stage: LeadStage


class LeadResponse(BaseModel):
    """Response schema for a single lead."""
    id: int
    name: str
    phone: str
    source: Optional[str]
    stage: str
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class LeadListResponse(BaseModel):
    """Paginated list response for GET /api/v1/leads."""

    class Meta(BaseModel):
        page: int
        limit: int
        total_count: int
        total_pages: int

    meta: Meta
    data: list[LeadResponse]


class LeadUpdate(BaseModel):
    """Body schema for PATCH /api/v1/leads/{id}."""
    name: Optional[str] = Field(default=None, min_length=1)
    phone: Optional[str] = Field(default=None, min_length=7)
    source: Optional[str] = Field(default=None)
    stage: Optional[LeadStage] = Field(default=None)
    notes: Optional[str] = Field(default=None)

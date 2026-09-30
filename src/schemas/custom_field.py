# src/schemas/custom_field.py
#
# Pydantic v2 request / response schemas for Custom Fields.

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class CustomFieldCreate(BaseModel):
    """Body schema for POST /api/v1/custom-fields."""
    name: str
    field_type: str
    options: Optional[list[str]] = None
    is_required: bool = False
    display_order: int = 0


class CustomFieldUpdate(BaseModel):
    """Body schema for PATCH /api/v1/custom-fields/{field_id}."""
    name: Optional[str] = None
    field_type: Optional[str] = None
    options: Optional[list[str]] = None
    is_required: Optional[bool] = None
    display_order: Optional[int] = None
    is_active: Optional[bool] = None


class CustomFieldResponse(BaseModel):
    """Response schema for a single custom field definition."""
    id: int
    name: str
    field_key: str
    field_type: str
    options: Optional[list[str]]
    is_required: bool
    display_order: int
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}

# src/models/custom_field.py

from __future__ import annotations

from sqlalchemy import Boolean, Column, DateTime, Integer, JSON, String
from sqlalchemy.sql import func

from src.database.connections import Base


class CustomFieldDefinition(Base):
    """SQLAlchemy ORM model for the *custom_field_definitions* table."""

    __tablename__ = "custom_field_definitions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    field_key = Column(String(100), unique=True, nullable=False, index=True)
    field_type = Column(String(20), nullable=False)
    options = Column(JSON, nullable=True)
    is_required = Column(Boolean, nullable=False, default=False)
    display_order = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, server_default=func.now())

    def __repr__(self) -> str:  # pragma: no cover
        return f"<CustomFieldDefinition id={self.id} field_key={self.field_key!r}>"

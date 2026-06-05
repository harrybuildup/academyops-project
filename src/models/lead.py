# src/models/lead.py

from __future__ import annotations

from enum import Enum

from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from src.database.connections import Base


class LeadStage(str, Enum):
    NEW = "New"
    CONTACTED = "Contacted"
    QUALIFIED = "Qualified"
    DEMO = "Demo"
    ENROLLED = "Enrolled"
    LOST = "Lost"


class LeadORM(Base):
    """SQLAlchemy ORM model for the *leads* table."""

    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=False, unique=True, index=True)
    source = Column(String(100), nullable=True)
    stage = Column(String(50), nullable=False, default=LeadStage.NEW.value, index=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<LeadORM id={self.id} name={self.name!r} stage={self.stage!r}>"

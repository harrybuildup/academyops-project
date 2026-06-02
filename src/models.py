from dataclasses import dataclass
from enum import Enum


class LeadStage(str, Enum):
    NEW = "New"
    CONTACTED = "Contacted"
    QUALIFIED = "Qualified"
    DEMO = "Demo"
    ENROLLED = "Enrolled"
    LOST = "Lost"


@dataclass
class Lead:
    id: int | None
    name: str
    phone: str
    source: str
    stage: str
    notes: str
    created_at: str
    updated_at: str
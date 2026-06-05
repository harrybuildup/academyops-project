# src/schemas/message.py

from pydantic import BaseModel, Field


class MessageRequest(BaseModel):
    message: str = Field(..., min_length=1, description="Inbound message text from the lead.")


class MessageResponse(BaseModel):
    intent: str
    suggested_stage: str
    reply: str

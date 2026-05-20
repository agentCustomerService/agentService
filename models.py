from pydantic import BaseModel
from typing import List, Optional


class ChatRequest(BaseModel):
    message: str
    order_id: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    success: bool
    session_id: str
    actions: List[str]
    logs: List[str]
    response: str


class ActionResponse(BaseModel):
    actions: List[str]


class SessionInfo(BaseModel):
    session_id: str
    created_at: str
    updated_at: str
    metadata: dict


class InteractionRecord(BaseModel):
    timestamp: str
    user_message: str
    order_id: str
    actions: List[str]
    executed_actions: List[str]
    response: str
    logs: List[str]
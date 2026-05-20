from pydantic import BaseModel
from typing import List, Optional


class ChatRequest(BaseModel):
    message: str
    order_id: str
    session_id: Optional[str] = None


class ConfirmActionsRequest(BaseModel):
    session_id: str
    order_id: str
    confirmed: bool  # User confirmation: True to proceed, False to cancel


class ChatResponse(BaseModel):
    success: bool
    session_id: str
    pending_actions: List[str]  # Actions waiting for confirmation
    executed_actions: List[str]
    logs: List[str]
    response: str
    awaiting_confirmation: bool  # Whether waiting for user to confirm actions


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
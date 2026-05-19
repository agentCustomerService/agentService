from pydantic import BaseModel
from typing import List


class ChatRequest(BaseModel):
    message: str
    order_id: str


class ChatResponse(BaseModel):
    success: bool
    actions: List[str]
    logs: List[str]
    response: str


class ActionResponse(BaseModel):
    actions: List[str]
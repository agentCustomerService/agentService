from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from agent import app as agent_app

from models import (
    ChatRequest,
    ChatResponse,
    SessionInfo,
    InteractionRecord
)
from state_manager import state_manager
from db import get_session, get_session_history, list_sessions

api = FastAPI()
api = FastAPI()

api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # in production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@api.get("/")
async def root():

    return {
        "status": "running"
    }


@api.post(
    "/chat",
    response_model=ChatResponse
)
async def chat(request: ChatRequest):

    # Create or get session
    session_id = state_manager.create_or_get_session(request.session_id)

    result = await agent_app.ainvoke({

        "session_id": session_id,
        "message": request.message,
        "order_id": request.order_id,
        "actions": [],
        "executed_actions": [],
        "logs": [],
        "response": ""

    })

    # Save the result to state and memory
    state_manager.save_agent_result(session_id, {
        "message": request.message,
        "order_id": request.order_id
    }, result)

    return {

        "success": True,
        "session_id": session_id,
        "actions": result.get(
            "executed_actions",
            []
        ),

        "logs": result.get(
            "logs",
            []
        ),

        "response": result.get(
            "response",
            ""
        )
    }


@api.get("/sessions", response_model=list)
async def get_sessions():
    """List all sessions."""
    return list_sessions()


@api.get("/sessions/{session_id}", response_model=SessionInfo)
async def get_session_info(session_id: str):
    """Get session information."""
    session = get_session(session_id)
    if not session:
        return {"error": "Session not found"}
    return session


@api.get("/sessions/{session_id}/history")
async def get_session_interactions(session_id: str, limit: int = 10):
    """Get interaction history for a session."""
    return get_session_history(session_id, limit)
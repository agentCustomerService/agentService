from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from agent import app as agent_app

from models import (
    ChatRequest,
    ChatResponse,
    ConfirmActionsRequest,
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
        "pending_actions": [],
        "executed_actions": [],
        "user_confirmed": False,
        "logs": [],
        "response": ""

    })

    # Save the result to state and memory
    state_manager.save_agent_result(session_id, {
        "message": request.message,
        "order_id": request.order_id
    }, result)

    pending_actions = result.get("pending_actions", [])
    awaiting_confirmation = bool(pending_actions)

    return {

        "success": True,
        "session_id": session_id,
        "pending_actions": pending_actions,
        "executed_actions": result.get(
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
        ),
        
        "awaiting_confirmation": awaiting_confirmation
    }


@api.post("/actions/confirm")
async def confirm_actions(request: ConfirmActionsRequest):
    """
    User confirms or cancels pending actions.
    
    request.confirmed = True: Execute the pending actions
    request.confirmed = False: Cancel and discard the pending actions
    """
    
    session_id = request.session_id
    order_id = request.order_id
    
    # Get current state from session
    session_data = state_manager.get_session(session_id)
    
    if not session_data:
        return {
            "success": False,
            "error": "Session not found"
        }
    
    # If user confirmed, execute the actions
    if request.confirmed:
        result = await agent_app.ainvoke({
            "session_id": session_id,
            "message": "",
            "order_id": order_id,
            "actions": session_data.get("pending_actions", []),
            "pending_actions": [],
            "executed_actions": session_data.get("executed_actions", []),
            "user_confirmed": True,  # User confirmed - proceed with execution
            "logs": session_data.get("logs", []),
            "response": ""
        })
        
        executed_actions = result.get("executed_actions", [])
        logs = result.get("logs", [])
        response = result.get("response", "")
        
        return {
            "success": True,
            "session_id": session_id,
            "message": "Actions executed successfully",
            "executed_actions": executed_actions,
            "logs": logs,
            "response": response
        }
    
    else:
        # User cancelled - discard pending actions
        logs = session_data.get("logs", [])
        logs.append("User cancelled pending actions")
        
        return {
            "success": True,
            "session_id": session_id,
            "message": "Pending actions cancelled and discarded",
            "executed_actions": [],
            "logs": logs,
            "response": "No actions were performed. Pending actions were cancelled."
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
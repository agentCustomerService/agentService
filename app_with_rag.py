from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from agent_with_rag import app as agent_app

from models import (
    ChatRequest,
    ChatResponse,
    SessionInfo,
    InteractionRecord
)
from state_manager import state_manager
from db import get_session, get_session_history, list_sessions
from rag_policies import (
    load_policies_from_pdf,
    list_loaded_policies,
    get_policies_context,
    init_policies_dir
)
import os

api = FastAPI()

api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # in production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize policies directory on startup
init_policies_dir()

@api.get("/")
async def root():
    return {
        "status": "running"
    }


@api.post("/chat", response_model=ChatResponse)
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
        "response": "",
        "policies_shown": False

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


# ----------------------------
# POLICY MANAGEMENT ENDPOINTS
# ----------------------------

@api.post("/policies/upload")
async def upload_policy(file: UploadFile = File(...), policy_name: str = None):
    """Upload and process a policy PDF."""
    
    try:
        # Save uploaded file temporarily
        temp_path = f"/tmp/{file.filename}"
        with open(temp_path, "wb") as f:
            contents = await file.read()
            f.write(contents)
        
        # Load policy from PDF
        result = load_policies_from_pdf(temp_path, policy_name)
        
        # Clean up temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)
        
        return {
            "success": result["success"],
            "message": result.get("message", ""),
            "policy_name": result.get("policy_name", ""),
            "chunks_count": result.get("chunks_count", 0)
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to upload policy: {str(e)}"
        }


@api.get("/policies/list")
async def list_policies():
    """List all loaded policies."""
    policies = list_loaded_policies()
    return {
        "policies": policies,
        "count": len(policies)
    }


@api.get("/policies/cancellation")
async def get_cancellation_policies():
    """Get cancellation policies."""
    policies = get_policies_context("cancellation")
    return {
        "policies": policies
    }


@api.get("/policies/refund")
async def get_refund_policies():
    """Get refund policies."""
    policies = get_policies_context("refund")
    return {
        "policies": policies
    }


@api.get("/policies/all")
async def get_all_policies():
    """Get all loaded policies."""
    policies = get_policies_context("both")
    return {
        "policies": policies
    }


# ----------------------------
# SESSION MANAGEMENT
# ----------------------------

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

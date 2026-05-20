from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from agent_with_rag import app as agent_app

from models import (
    ChatRequest,
    ChatResponse,
    ConfirmActionsRequest,
    SessionInfo
)

from state_manager import state_manager
from db import get_session, get_session_history, list_sessions

from rag_policies import (
    load_policies_from_pdf,
    list_loaded_policies,
    get_policies_context,
    init_policies_dir
)

from pathlib import Path

# ----------------------------
# HARD-CODED PDF PATH
# ----------------------------
PDF_PATH = Path(r"C:\Users\DELL\Desktop\Policy.pdf")

# Store loaded policy globally
POLICY_RESULT = None


# ----------------------------
# LIFESPAN (REPLACES on_event)
# ----------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    global POLICY_RESULT

    init_policies_dir()

    if PDF_PATH.exists():
        POLICY_RESULT = load_policies_from_pdf(
            str(PDF_PATH),
            policy_name="default_policy"
        )
        print("[INIT] Policy loaded successfully")
    else:
        POLICY_RESULT = {
            "success": False,
            "message": f"PDF not found at {PDF_PATH}"
        }
        print("[ERROR] PDF not found")

    yield  # app runs here

    print("[SHUTDOWN] App stopped")


# ----------------------------
# FASTAPI APP
# ----------------------------
api = FastAPI(lifespan=lifespan)

api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ----------------------------
# ROOT
# ----------------------------
@api.get("/")
async def root():
    return {
        "status": "running"
    }


# ----------------------------
# CHAT ENDPOINT
# ----------------------------
@api.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):

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
        "response": "",
        "policies_shown": False,

        # preloaded policy context
        "policy_context": POLICY_RESULT
    })

    state_manager.save_agent_result(
        session_id,
        {
            "message": request.message,
            "order_id": request.order_id
        },
        result
    )

    pending_actions = result.get("pending_actions", [])
    awaiting_confirmation = bool(pending_actions)

    return {
        "success": True,
        "session_id": session_id,
        "pending_actions": pending_actions,
        "executed_actions": result.get("executed_actions", []),
        "logs": result.get("logs", []),
        "response": result.get("response", ""),
        "awaiting_confirmation": awaiting_confirmation
    }


# ----------------------------
# POLICIES (READ ONLY)
# ----------------------------
@api.get("/policies")
async def get_policies():
    return POLICY_RESULT or {
        "success": False,
        "message": "No policy loaded"
    }


@api.get("/policies/list")
async def list_policies():
    policies = list_loaded_policies()
    return {
        "policies": policies,
        "count": len(policies)
    }


@api.get("/policies/cancellation")
async def get_cancellation_policies():
    return {
        "policies": get_policies_context("cancellation")
    }


@api.get("/policies/refund")
async def get_refund_policies():
    return {
        "policies": get_policies_context("refund")
    }


@api.get("/policies/all")
async def get_all_policies():
    return {
        "policies": get_policies_context("both")
    }


# ----------------------------
# ACTION CONFIRMATION
# ----------------------------
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
            "response": "",
            "policies_shown": False,
            "policy_context": POLICY_RESULT
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


# ----------------------------
# SESSION MANAGEMENT
# ----------------------------
@api.get("/sessions", response_model=list)
async def get_sessions():
    return list_sessions()


@api.get("/sessions/{session_id}", response_model=SessionInfo)
async def get_session_info(session_id: str):
    session = get_session(session_id)

    if not session:
        return {"error": "Session not found"}

    return session


@api.get("/sessions/{session_id}/history")
async def get_session_interactions(session_id: str, limit: int = 10):
    return get_session_history(session_id, limit)
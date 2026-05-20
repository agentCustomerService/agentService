from typing import TypedDict, List
from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END
import os

from models import ActionResponse
from services.orders import cancel_order, refund_order
from state_manager import state_manager
from rag_policies import get_policies_context, list_loaded_policies

load_dotenv()

# ----------------------------
# LLM SETUP
# ----------------------------
try:
    from langchain_ollama import ChatOllama
    llm = ChatOllama(
        model="llama3.1:8b",
        temperature=0
    )
except ImportError:
    from langchain_google_genai import ChatGoogleGenerativeAI
    if not os.getenv("GOOGLE_API_KEY"):
        raise ValueError("GOOGLE_API_KEY is required when langchain-ollama is not available")
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0
    )

SYSTEM_PROMPT = """
You are an order management assistant with access to company policies.

Available actions:
- cancel
- refund
- none

IMPORTANT: Before suggesting cancel or refund actions, you MUST:
1. First inform the customer of relevant policies
2. Ask for their consent given the policies
3. Only proceed with the action if they agree

Return ONLY valid JSON in this format:

{
  "actions": ["cancel", "refund"],
  "show_policies": true,
  "message": "Here are our policies... do you agree?"
}

Rules:
- output JSON only
- no explanation
- Always show policies before actions
- Be respectful about policies
"""


class AgentState(TypedDict):
    session_id: str
    message: str
    order_id: str
    actions: List[str]
    pending_actions: List[str]  # Actions to show user for confirmation
    executed_actions: List[str]
    user_confirmed: bool  # User confirmation flag
    logs: List[str]
    response: str
    policies_shown: bool


# ----------------------------
# POLICY RETRIEVAL
# ----------------------------
def retrieve_policies(state: AgentState) -> str:
    """Retrieve relevant policies for the order action."""
    message = state.get("message", "").lower()
    
    # Determine what kind of policies to show
    if "refund" in message and "cancel" in message:
        return get_policies_context("both")
    elif "refund" in message:
        return get_policies_context("refund")
    elif "cancel" in message:
        return get_policies_context("cancellation")
    
    return ""


# ----------------------------
# ANALYZE (WITH POLICY CONTEXT)
# ----------------------------
async def analyze(state: AgentState):

    # Get memory context from past interactions
    memory_context = state_manager.get_memory_context(state.get("session_id", ""))
    
    memory_section = f"\n{memory_context}\n" if memory_context else ""
    
    # Get relevant policies
    policies = retrieve_policies(state)
    policies_section = f"\n{policies}\n" if policies else ""

    prompt = f"""
{SYSTEM_PROMPT}

{memory_section}

{policies_section}

User message:
{state["message"]}

Return the JSON with action decision and whether to show policies.
"""

    result = llm.invoke(prompt)

    content = result.content.strip()

    # fallback-safe parsing
    import json

    try:
        data = json.loads(content)
        actions = data.get("actions", [])
        show_policies = data.get("show_policies", False)
        message = data.get("message", "")
    except Exception:
        actions = []
        show_policies = False
        message = ""

    return {
        "actions": actions,
        "pending_actions": actions,  # Show actions for user confirmation
        "user_confirmed": False,  # Require user confirmation
        "policies_shown": show_policies,
        "response": message
    }


# ----------------------------
# DISPLAY ACTIONS NODE
# ----------------------------
async def display_actions(state: AgentState):
    """Display pending actions for user confirmation"""
    
    pending_actions = state.get("pending_actions", [])
    
    if not pending_actions:
        return {
            "user_confirmed": True  # No actions to confirm
        }
    
    # Log the actions for user review
    action_list = ", ".join(pending_actions)
    logs = state.get("logs", [])
    logs.append(f"Pending actions to execute: {action_list}")
    
    return {
        "logs": logs,
        "pending_actions": pending_actions
    }


# ----------------------------
# EXECUTE
# ----------------------------
async def execute(state: AgentState):

    actions = state.get("actions", [])
    pending = state.get("pending_actions", [])
    
    # Only execute if user confirmed or no pending actions
    if not pending or not state.get("user_confirmed", False):
        return {
            "actions": actions,
            "pending_actions": pending
        }

    if not actions:
        return {}

    action = actions.pop(0)

    order_id = state["order_id"]
    logs = state.get("logs", [])
    executed = state.get("executed_actions", [])

    try:

        if action == "cancel":
            await cancel_order(order_id)
            logs.append(f"Order {order_id} canceled")
            executed.append("cancel")

        elif action == "refund":
            await refund_order(order_id)
            logs.append(f"Order {order_id} refunded")
            executed.append("refund")

        else:
            logs.append(f"Unknown action: {action}")

    except Exception as e:
        logs.append(str(e))

    return {
        "actions": actions,
        "logs": logs,
        "executed_actions": executed
    }


# ----------------------------
# RESPONSE NODE
# ----------------------------
async def generate_response(state: AgentState):

    executed = state.get("executed_actions", [])
    response = state.get("response", "")

    if not executed:
        if not response:
            response = "No actions were performed."
    else:
        action_text = ", ".join(executed)
        if response:
            response = f"{response}\n\nCompleted actions: {action_text}"
        else:
            response = f"Completed actions: {action_text}"

    return {
        "response": response
    }


# ----------------------------
# ROUTER - Should Display Actions
# ----------------------------
def should_display_actions(state: AgentState):
    """Check if there are actions to display"""
    
    if state.get("pending_actions"):
        return "display_actions"
    
    return "generate_response"


# ----------------------------
# ROUTER - Should Continue Execution
# ----------------------------
def should_continue(state: AgentState):
    """Check if we should continue executing actions"""
    
    if state.get("actions") and state.get("user_confirmed", False):
        return "execute"

    return "generate_response"


# ----------------------------
# GRAPH
# ----------------------------
graph = StateGraph(AgentState)

graph.add_node("analyze", analyze)
graph.add_node("display_actions", display_actions)
graph.add_node("execute", execute)
graph.add_node("generate_response", generate_response)

graph.add_edge(START, "analyze")
graph.add_conditional_edges("analyze", should_display_actions)
graph.add_edge("display_actions", "execute")
graph.add_conditional_edges("execute", should_continue)

graph.add_edge("generate_response", END)

app = graph.compile()

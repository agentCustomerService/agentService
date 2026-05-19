from typing import TypedDict, List
from fastapi.middleware.cors import CORSMiddleware
from langgraph.graph import StateGraph, START, END
from langchain_ollama import ChatOllama

from models import ActionResponse
from services.orders import cancel_order, refund_order


# ----------------------------
# LOCAL LLM (FIXED MODEL NAME)
# ----------------------------
llm = ChatOllama(
    model="llama3.1:8b",  # IMPORTANT FIX
    temperature=0
)

SYSTEM_PROMPT = """
You are an order management assistant.

Available actions:
- cancel
- refund
- none

Return ONLY valid JSON in this format:

{
  "actions": ["cancel", "refund"]
}

Rules:
- output JSON only
- no explanation
"""


class AgentState(TypedDict):
    message: str
    order_id: str
    actions: List[str]
    executed_actions: List[str]
    logs: List[str]
    response: str


# ----------------------------
# ANALYZE (FIXED: NO structured_output)
# Ollama structured output is unreliable here
# ----------------------------
async def analyze(state: AgentState):

    prompt = f"""
{SYSTEM_PROMPT}

User message:
{state["message"]}
"""

    result = llm.invoke(prompt)

    content = result.content.strip()

    # fallback-safe parsing
    import json

    try:
        data = json.loads(content)
        actions = data.get("actions", [])
    except Exception:
        actions = []

    return {
        "actions": actions
    }


# ----------------------------
# EXECUTE
# ----------------------------
async def execute(state: AgentState):

    actions = state.get("actions", [])

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

    if not executed:
        response = "No actions were performed."
    else:
        response = "Completed actions: " + ", ".join(executed)

    return {
        "response": response
    }


# ----------------------------
# ROUTER
# ----------------------------
def should_continue(state: AgentState):

    if state.get("actions"):
        return "execute"

    return "generate_response"


# ----------------------------
# GRAPH
# ----------------------------
graph = StateGraph(AgentState)

graph.add_node("analyze", analyze)
graph.add_node("execute", execute)
graph.add_node("generate_response", generate_response)

graph.add_edge(START, "analyze")
graph.add_edge("analyze", "execute")

graph.add_conditional_edges("execute", should_continue)

graph.add_edge("generate_response", END)

app = graph.compile()
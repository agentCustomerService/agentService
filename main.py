from dotenv import load_dotenv
import os
import sys
import time
import traceback

from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END, START
from typing import TypedDict, List


load_dotenv()

if not os.getenv("GOOGLE_API_KEY"):
    print("ERROR: GOOGLE_API_KEY is not set in .env")
    sys.exit(1)


llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0
)


SYSTEM_PROMPT = """
You are a customer support assistant for order management only.

Return ALL required actions from this list:
- cancel
- refund
- none

If multiple actions are needed, return them comma-separated.
Example:
cancel, refund
"""


class AgentState(TypedDict):
    message: str
    actions: List[str]
    response: str


def cancel_order(order_id: str):
    print(f"[ACTION] Order {order_id} has been CANCELED")


def refund_order(order_id: str):
    print(f"[ACTION] Order {order_id} has been REFUNDED")


# ----------------------------
# ANALYZE NODE (build action queue)
# ----------------------------
def analyze(state: AgentState):
    print("\n[NODE] analyze")

    prompt = f"""
{SYSTEM_PROMPT}

User message:
{state["message"]}

Return actions:
"""

    try:
        result = llm.invoke(prompt)
        content = result.content.strip().lower()

        print("[DEBUG] raw LLM:", content)

        actions = [a.strip() for a in content.split(",") if a.strip()]

        return {"actions": actions}

    except Exception:
        print(traceback.format_exc())
        return {"actions": []}


# ----------------------------
# EXECUTE ONE ACTION PER STEP
# ----------------------------
def execute(state: AgentState):
    print("\n[NODE] execute")
    print("[STATE]", state)

    actions = state.get("actions", [])
    order_id = "1234"

    if not actions:
        return {"response": "No actions to perform."}

    action = actions.pop(0)

    print("[DEBUG] executing:", action)

    if action == "cancel":
        cancel_order(order_id)

    elif action == "refund":
        refund_order(order_id)

    return {"actions": actions}


# ----------------------------
# ROUTER (controls loop)
# ----------------------------
def should_continue(state: AgentState):
    if state.get("actions"):
        return "execute"
    return END


# ----------------------------
# GRAPH
# ----------------------------
print("[INIT] building graph...")

graph = StateGraph(AgentState)

graph.add_node("analyze", analyze)
graph.add_node("execute", execute)

graph.add_edge(START, "analyze")
graph.add_edge("analyze", "execute")

graph.add_conditional_edges("execute", should_continue)

app = graph.compile()

print("[INIT] graph ready")


# ----------------------------
# RUN
# ----------------------------
if __name__ == "__main__":
    print("\n[MAIN] start")

    result = app.invoke({
        "message": "cancel my order then refund me",
        "actions": [],
        "response": ""
    })

    print("\n[FINAL RESULT]", result)
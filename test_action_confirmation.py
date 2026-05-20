"""
Test script to demonstrate the action confirmation workflow.
This shows how actions are displayed and can be confirmed or cancelled.
"""

import json
from agent import app as agent_app


async def test_action_confirmation_flow():
    """Test the complete action confirmation flow"""
    
    print("\n" + "="*80)
    print("TEST 1: User requests cancel and refund")
    print("="*80)
    
    # Step 1: User sends a message requesting actions
    result1 = await agent_app.ainvoke({
        "session_id": "test-session-1",
        "message": "I want to cancel my order and get a refund",
        "order_id": "ORDER-12345",
        "actions": [],
        "pending_actions": [],
        "executed_actions": [],
        "user_confirmed": False,
        "logs": [],
        "response": ""
    })
    
    print("\n[STEP 1] Chat endpoint response:")
    print(f"  Pending Actions: {result1.get('pending_actions', [])}")
    print(f"  Executed Actions: {result1.get('executed_actions', [])}")
    print(f"  Awaiting Confirmation: {bool(result1.get('pending_actions', []))}")
    print(f"  Response: {result1.get('response', '')}")
    print(f"  Logs: {result1.get('logs', [])}")
    
    pending_actions = result1.get('pending_actions', [])
    
    if not pending_actions:
        print("\n  ⚠️ No actions identified by LLM")
        return
    
    print("\n" + "="*80)
    print("TEST 2: User confirms the pending actions")
    print("="*80)
    
    # Step 2: User confirms the actions (simulating /actions/confirm endpoint)
    result2 = await agent_app.ainvoke({
        "session_id": "test-session-1",
        "message": "",
        "order_id": "ORDER-12345",
        "actions": pending_actions.copy(),
        "pending_actions": [],
        "executed_actions": [],
        "user_confirmed": True,  # User confirmed!
        "logs": result1.get('logs', []),
        "response": ""
    })
    
    print("\n[STEP 2] After user confirmation:")
    print(f"  Executed Actions: {result2.get('executed_actions', [])}")
    print(f"  Response: {result2.get('response', '')}")
    print(f"  Logs:")
    for log in result2.get('logs', []):
        print(f"    - {log}")
    
    print("\n" + "="*80)
    print("TEST 3: User cancels the actions")
    print("="*80)
    
    # Step 3: Another flow where user cancels
    result3 = await agent_app.ainvoke({
        "session_id": "test-session-2",
        "message": "Cancel my order",
        "order_id": "ORDER-67890",
        "actions": [],
        "pending_actions": [],
        "executed_actions": [],
        "user_confirmed": False,
        "logs": [],
        "response": ""
    })
    
    print("\n[STEP 3a] Chat endpoint response:")
    print(f"  Pending Actions: {result3.get('pending_actions', [])}")
    
    # User cancels (user_confirmed stays False)
    result4 = await agent_app.ainvoke({
        "session_id": "test-session-2",
        "message": "",
        "order_id": "ORDER-67890",
        "actions": [],  # Empty actions list means no execution
        "pending_actions": result3.get('pending_actions', []),
        "executed_actions": [],
        "user_confirmed": False,  # User did NOT confirm
        "logs": result3.get('logs', []),
        "response": ""
    })
    
    print("\n[STEP 3b] After user cancellation (user_confirmed=False):")
    print(f"  Executed Actions: {result4.get('executed_actions', [])}")
    print(f"  Response: {result4.get('response', '')}")
    print(f"  Logs:")
    for log in result4.get('logs', []):
        print(f"    - {log}")
    
    print("\n" + "="*80)
    print("WORKFLOW SUMMARY")
    print("="*80)
    print("""
1. User sends message → LLM identifies pending actions
2. Pending actions shown in response with awaiting_confirmation=true
3. User has two options:
   a) Confirm: Call /actions/confirm with confirmed=true
      → Actions are executed and saved
   b) Cancel: Call /actions/confirm with confirmed=false
      → Pending actions are discarded, no execution
4. Session state persists across API calls
5. All actions and confirmations are logged
    """)


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_action_confirmation_flow())

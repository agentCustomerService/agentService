#!/usr/bin/env python3
"""
Simple test to verify the state and memory implementation works correctly.
"""

import json
import asyncio
from db import init_db, get_session, get_session_history, list_sessions
from state_manager import state_manager

async def test_state_and_memory():
    """Test the state and memory functionality."""
    
    print("=" * 60)
    print("Testing Agent State & Memory Implementation")
    print("=" * 60)
    
    # Initialize database
    print("\n1. Initializing database...")
    init_db()
    print("✓ Database initialized")
    
    # Create a session
    print("\n2. Creating a session...")
    session_id = state_manager.create_or_get_session()
    print(f"✓ Session created: {session_id}")
    
    # Verify session exists
    print("\n3. Verifying session...")
    session = get_session(session_id)
    print(f"✓ Session found: {json.dumps(session, indent=2)}")
    
    # Simulate agent execution and save result
    print("\n4. Simulating agent execution and saving state...")
    agent_input = {
        "message": "Cancel order 12345",
        "order_id": "12345"
    }
    agent_output = {
        "actions": [],
        "executed_actions": ["cancel"],
        "response": "Completed actions: cancel",
        "logs": ["Order 12345 canceled"]
    }
    state_manager.save_agent_result(session_id, agent_input, agent_output)
    print("✓ Agent result saved")
    
    # Simulate another interaction
    print("\n5. Simulating second interaction...")
    agent_input2 = {
        "message": "Refund order 12345",
        "order_id": "12345"
    }
    agent_output2 = {
        "actions": [],
        "executed_actions": ["refund"],
        "response": "Completed actions: refund",
        "logs": ["Order 12345 refunded"]
    }
    state_manager.save_agent_result(session_id, agent_input2, agent_output2)
    print("✓ Second interaction saved")
    
    # Retrieve session history
    print("\n6. Retrieving session history...")
    history = get_session_history(session_id)
    print(f"✓ Retrieved {len(history)} interactions:")
    for i, interaction in enumerate(history, 1):
        print(f"  {i}. Order {interaction['order_id']}: {interaction['user_message']}")
        print(f"     Actions: {interaction['executed_actions']}")
    
    # Get memory context (used by agent)
    print("\n7. Getting memory context for agent...")
    memory = state_manager.get_memory_context(session_id)
    print("✓ Memory context:")
    print(memory)
    
    # Test session reuse
    print("\n8. Testing session reuse...")
    session_id_reuse = state_manager.create_or_get_session(session_id)
    print(f"✓ Reused session: {session_id_reuse}")
    assert session_id_reuse == session_id, "Session ID mismatch!"
    
    # List all sessions
    print("\n9. Listing all sessions...")
    all_sessions = list_sessions()
    print(f"✓ Found {len(all_sessions)} session(s):")
    for s in all_sessions:
        print(f"  - {s['session_id']} (updated: {s['updated_at']})")
    
    print("\n" + "=" * 60)
    print("All tests passed! ✓")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_state_and_memory())

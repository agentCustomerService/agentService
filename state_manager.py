import uuid
from typing import Optional
from db import (
    create_session, get_session, save_state_snapshot, 
    save_interaction, get_session_memory_context, 
    update_session_timestamp, init_db
)


class StateManager:
    """Manages agent state persistence and memory."""
    
    def __init__(self):
        init_db()
    
    def create_or_get_session(self, session_id: Optional[str] = None) -> str:
        """Create a new session or return existing one."""
        if session_id:
            session = get_session(session_id)
            if session:
                update_session_timestamp(session_id)
                return session_id
        
        # Generate new session
        new_id = str(uuid.uuid4())
        create_session(new_id)
        return new_id
    
    def save_agent_result(self, session_id: str, agent_input: dict, agent_output: dict) -> None:
        """Save the agent's execution result."""
        save_interaction(
            session_id=session_id,
            user_message=agent_input.get("message", ""),
            order_id=agent_input.get("order_id", ""),
            actions=agent_output.get("actions", []),
            executed_actions=agent_output.get("executed_actions", []),
            response=agent_output.get("response", ""),
            logs=agent_output.get("logs", [])
        )
        save_state_snapshot(session_id, agent_output)
        update_session_timestamp(session_id)
    
    def get_memory_context(self, session_id: str) -> str:
        """Get memory context from past interactions."""
        return get_session_memory_context(session_id)


# Global state manager instance
state_manager = StateManager()

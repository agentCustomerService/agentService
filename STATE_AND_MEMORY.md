# Agent State & Memory Implementation

This document describes the state and memory system added to the agent service.

## Overview

The agent now supports:

- **Session Management** - Track conversations across multiple requests
- **Persistent State** - Store agent state snapshots for debugging and recovery
- **Memory/History** - Keep track of past interactions to inform future decisions
- **Session Querying** - APIs to retrieve session info and interaction history

## Architecture

### Components

#### 1. **db.py** - Database Layer

Handles all database operations for persistence:

- `sessions` table - Tracks active sessions with metadata
- `state_history` table - Stores snapshots of agent state after each execution
- `interactions` table - Tracks conversation history with orders and actions

Key functions:

- `init_db()` - Initialize database schema
- `create_session(session_id)` - Create a new session
- `get_session(session_id)` - Retrieve session info
- `save_state_snapshot(session_id, state)` - Save state snapshot
- `save_interaction(...)` - Record an interaction
- `get_session_history(session_id, limit)` - Retrieve recent interactions
- `get_session_memory_context(session_id, limit)` - Get formatted memory for agent

#### 2. **state_manager.py** - State Management

High-level API for state operations:

- `StateManager.create_or_get_session()` - Create new or retrieve existing session
- `StateManager.save_agent_result()` - Save execution result
- `StateManager.get_memory_context()` - Get memory context for agent reasoning

#### 3. **agent.py** - Updated Agent

Enhanced with session and memory support:

- `AgentState` now includes `session_id`
- `analyze()` function includes memory context in prompt
- Agent uses past interactions when making decisions

#### 4. **models.py** - Updated Data Models

New models for session management:

- `ChatRequest` - Optional `session_id` parameter
- `ChatResponse` - Now includes `session_id`
- `SessionInfo` - Session metadata
- `InteractionRecord` - Single interaction record

#### 5. **app.py** - Enhanced API

New endpoints for session management:

- `POST /chat` - Execute agent (with session support)
- `GET /sessions` - List all sessions
- `GET /sessions/{session_id}` - Get session info
- `GET /sessions/{session_id}/history` - Get interaction history

## Usage

### Creating a New Session

```python
import requests

# First request - will create a new session automatically
response = requests.post("http://localhost:8000/chat", json={
    "message": "Cancel order 12345",
    "order_id": "12345"
})

result = response.json()
session_id = result["session_id"]
# {
#   "success": true,
#   "session_id": "uuid-here",
#   "actions": ["cancel"],
#   "logs": ["Order 12345 canceled"],
#   "response": "Completed actions: cancel"
# }
```

### Continuing a Session

```python
# Second request - reuse the same session
response = requests.post("http://localhost:8000/chat", json={
    "message": "Refund order 12345",
    "order_id": "12345",
    "session_id": "uuid-here"  # Provide session_id to continue
})

# The agent will have access to past interactions with this order
```

### Querying Sessions

```python
# List all sessions
sessions = requests.get("http://localhost:8000/sessions").json()

# Get session info
session = requests.get("http://localhost:8000/sessions/uuid-here").json()
# {
#   "session_id": "uuid-here",
#   "created_at": "2024-01-01T10:00:00",
#   "updated_at": "2024-01-01T10:05:00",
#   "metadata": {}
# }

# Get interaction history
history = requests.get("http://localhost:8000/sessions/uuid-here/history?limit=10").json()
# [
#   {
#     "id": 1,
#     "timestamp": "2024-01-01T10:00:00",
#     "user_message": "Cancel order 12345",
#     "order_id": "12345",
#     "actions": ["cancel"],
#     "executed_actions": ["cancel"],
#     "response": "Completed actions: cancel",
#     "logs": ["Order 12345 canceled"]
#   }
# ]
```

## Memory in Action

The agent now uses past interactions to inform decisions. For example:

**Interaction 1:**

```
User: "Cancel order 12345"
Agent: "Canceled order 12345"
```

**Interaction 2 (same session):**

```
User: "What happened to my order?"
Agent: (has access to memory: "Order 12345 was recently canceled")
```

The memory context is injected into the agent's prompt, so it can refer back to previous actions.

## Database Schema

### sessions

```sql
CREATE TABLE sessions (
    session_id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    metadata TEXT  -- JSON
)
```

### state_history

```sql
CREATE TABLE state_history (
    id INTEGER PRIMARY KEY,
    session_id TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    state TEXT NOT NULL,  -- Full JSON state snapshot
    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
)
```

### interactions

```sql
CREATE TABLE interactions (
    id INTEGER PRIMARY KEY,
    session_id TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    user_message TEXT,
    order_id TEXT,
    actions TEXT,  -- JSON list
    executed_actions TEXT,  -- JSON list
    response TEXT,
    logs TEXT,  -- JSON list
    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
)
```

## Testing

Run the test suite:

```bash
python test_state_memory.py
```

This will:

1. Initialize the database
2. Create a session
3. Simulate agent executions
4. Verify state is persisted
5. Test memory retrieval
6. Confirm session history works

## Configuration

The database is stored as `agent_state.db` in the project root directory.

To use a different database location, modify the `DB_PATH` in `db.py`:

```python
DB_PATH = Path(__file__).parent / "agent_state.db"
```

## Future Enhancements

- Session TTL (automatic cleanup of old sessions)
- Session search/filtering API
- Export session history to CSV/JSON
- Conversation summaries
- Automatic session naming
- Session annotations/tags

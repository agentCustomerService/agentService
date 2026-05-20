# Architecture Overview: Agent State & Memory System

## System Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                         API Request                              │
│  POST /chat {message, order_id, session_id (optional)}           │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
         ┌─────────────────────────────────────┐
         │  StateManager (state_manager.py)    │
         │  - create_or_get_session()          │
         │  - get_memory_context()             │
         └──────────┬────────────────┬─────────┘
                    │                │
        ┌───────────▼──┐    ┌────────▼──────────┐
        │   Database   │    │  Agent Processor  │
        │   (db.py)    │    │   (agent.py)      │
        │              │    │                   │
        │ • sessions   │    │ AgentState now    │
        │ • history    │    │ includes:         │
        │ • state      │    │ - session_id      │
        └──────────────┘    │ - memory context  │
                            │                   │
                            │ analyze() node    │
                            │ includes memory   │
                            │ in prompt         │
                            └────────┬──────────┘
                                     │
                                     ▼
         ┌─────────────────────────────────────┐
         │   LLM (llama3.1:8b)                 │
         │   Makes decision with context       │
         │   of past actions                   │
         └────────────────┬────────────────────┘
                          │
                          ▼
         ┌─────────────────────────────────────┐
         │   Save Result                       │
         │   - Store interaction               │
         │   - Save state snapshot             │
         │   - Update timestamp                │
         └────────────────┬────────────────────┘
                          │
                          ▼
         ┌─────────────────────────────────────┐
         │   Return Response                   │
         │   {session_id, actions, response}   │
         └─────────────────────────────────────┘
```

## Component Interactions

### 1. Session Management

```
ChatRequest (with optional session_id)
    ↓
StateManager.create_or_get_session()
    ├→ If session_id provided: retrieve from DB
    ├→ Else: generate new UUID
    └→ Return session_id

Database stores:
- session_id (unique)
- created_at timestamp
- updated_at timestamp (refreshed on each request)
- metadata (JSON)
```

### 2. Memory Injection

```
Agent execution with session_id:
    ↓
analyze() node runs:
    ├→ Get memory_context from StateManager
    ├→ Memory contains last 5 interactions
    ├→ Format as "Recent interaction history:"
    └→ Include in LLM prompt

LLM now sees:
- System prompt (available actions)
- Memory context (what happened before)
- Current user message
    ↓
More informed decision
```

### 3. Persistence

```
After agent execution:
    ↓
StateManager.save_agent_result():
    ├→ Save interaction record
    │  (message, order_id, actions, response, logs)
    │
    ├→ Save state snapshot
    │  (full AgentState as JSON)
    │
    └→ Update session timestamp
       (tracks last activity)
```

## Data Flow Example

### First Request

```
POST /chat
{
  "message": "Cancel order 12345",
  "order_id": "12345"
}
      ↓
StateManager generates session_id: "abc-123-def"
      ↓
Agent processes: decide action is "cancel"
      ↓
Save to DB:
- interactions table: interaction record
- state_history table: full state snapshot
- sessions table: update timestamp
      ↓
Return:
{
  "session_id": "abc-123-def",
  "actions": ["cancel"],
  "response": "Completed actions: cancel",
  "logs": ["Order 12345 canceled"]
}
```

### Second Request (Same Session)

```
POST /chat
{
  "message": "Refund the order",
  "order_id": "12345",
  "session_id": "abc-123-def"
}
      ↓
StateManager reuses session: "abc-123-def"
      ↓
Agent.analyze() gets memory context:
"Recent interaction history:
- Order 12345: Cancel order 12345
  Actions taken: cancel"
      ↓
LLM reads memory and knows order was just canceled
Decides action is "refund"
      ↓
Save to DB (new interaction record + state snapshot)
      ↓
Return response with refund confirmation
```

## Query APIs

```
GET /sessions
└→ Returns list of all sessions sorted by last update

GET /sessions/{session_id}
└→ Returns session metadata and timestamps

GET /sessions/{session_id}/history?limit=10
└→ Returns recent interactions in reverse chronological order
   Each interaction shows:
   - timestamp
   - user message
   - order_id
   - actions taken
   - response from agent
   - logs
```

## Files Overview

```
agent.py (modified)
├─ Added: session_id to AgentState
├─ Updated: analyze() to include memory context
└─ Imports: state_manager for memory retrieval

app.py (modified)
├─ Added: StateManager integration in /chat endpoint
├─ New: /sessions endpoints for querying
└─ Imports: state_manager, db functions

models.py (modified)
├─ Updated: ChatRequest with optional session_id
├─ Updated: ChatResponse with session_id
└─ New: SessionInfo, InteractionRecord models

state_manager.py (new)
├─ Class: StateManager
├─ Method: create_or_get_session()
├─ Method: save_agent_result()
├─ Method: get_memory_context()
└─ Exports: state_manager (global instance)

db.py (new)
├─ Function: init_db() - creates tables
├─ Function: create_session() - new session
├─ Function: get_session() - retrieve session
├─ Function: save_interaction() - record interaction
├─ Function: get_session_history() - retrieve history
├─ Function: get_session_memory_context() - format memory
└─ Tables: sessions, state_history, interactions
```

## Key Design Decisions

✅ **Stateless Agent** - Agent itself remains stateless; state is managed externally
✅ **Memory in Prompt** - Rather than fine-tuning, memory is injected into context
✅ **SQLite** - Lightweight, serverless, no external dependencies
✅ **Session ID Optional** - Clients can auto-generate new sessions or reuse existing
✅ **Full Snapshots** - Store complete state for debugging and recovery
✅ **Interaction Records** - Human-readable summary for queries

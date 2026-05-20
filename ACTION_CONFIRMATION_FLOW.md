# Action Confirmation Flow

## Overview

The agent system now displays pending actions to the user before execution and allows them to confirm or cancel these actions.

## Updated LangGraph Flow

```
START
  │
  ▼
┌──────────────────┐
│   analyze()      │  ─ LLM analyzes user message
│  node            │  ─ Returns list of actions
└────────┬─────────┘
         │
    ┌────▼────────────────────────────┐
    │ should_display_actions()         │
    │ (conditional router)             │
    └────┬────────────────┬────────────┘
         │ (has actions)  │ (no actions)
         ▼                │
    ┌──────────────────┐  │
    │ display_actions()│  │
    │  node            │  │
    │  ─ Show pending  │  │
    │    actions to    │  │
    │    user          │  │
    │  ─ Wait for      │  │
    │    confirmation  │  │
    └────────┬─────────┘  │
             │            │
             ▼            │
    ┌──────────────────┐  │
    │ execute()        │  │
    │  node (only if   │  │
    │  confirmed)      │  │
    │  ─ Execute       │  │
    │    actions       │  │
    │  ─ Log results   │  │
    └────────┬─────────┘  │
             │            │
    ┌────────▼────────────▼────────────┐
    │ should_continue()                │
    │ (conditional router)             │
    └────┬────────────────┬────────────┘
         │ (more actions) │ (no more)
         │                │
         └────────┬───────┘
                  │
                  ▼
         ┌──────────────────┐
         │generate_response()│
         │  node            │
         │  ─ Summarize     │
         │    executed      │
         │    actions       │
         └────────┬─────────┘
                  │
                  ▼
                 END
```

## State Structure

```python
class AgentState(TypedDict):
    session_id: str                    # Session identifier
    message: str                       # User message
    order_id: str                      # Order to act on
    actions: List[str]                # Actions still to execute
    pending_actions: List[str]        # Actions waiting for user confirmation
    executed_actions: List[str]       # Actions already executed
    user_confirmed: bool              # Whether user confirmed pending actions
    logs: List[str]                   # Log messages
    response: str                      # Final response to user
```

## API Endpoints

### 1. POST /chat

**Purpose**: Analyze user message and return pending actions

**Request**:

```json
{
  "message": "cancel my order and refund me",
  "order_id": "12345",
  "session_id": "optional-session-id"
}
```

**Response**:

```json
{
  "success": true,
  "session_id": "generated-or-provided-session-id",
  "pending_actions": ["cancel", "refund"],
  "executed_actions": [],
  "logs": ["Pending actions to execute: cancel, refund"],
  "response": "No actions were performed.",
  "awaiting_confirmation": true
}
```

### 2. POST /actions/confirm

**Purpose**: User confirms or cancels pending actions

**Request - Confirm Actions**:

```json
{
  "session_id": "session-id",
  "order_id": "12345",
  "confirmed": true
}
```

**Request - Cancel Actions**:

```json
{
  "session_id": "session-id",
  "order_id": "12345",
  "confirmed": false
}
```

**Response (confirmed=true)**:

```json
{
  "success": true,
  "session_id": "session-id",
  "message": "Actions executed successfully",
  "executed_actions": ["cancel", "refund"],
  "logs": [
    "Pending actions to execute: cancel, refund",
    "Order 12345 canceled",
    "Order 12345 refunded"
  ],
  "response": "Completed actions: cancel, refund"
}
```

**Response (confirmed=false)**:

```json
{
  "success": true,
  "session_id": "session-id",
  "message": "Pending actions cancelled and discarded",
  "executed_actions": [],
  "logs": [
    "Pending actions to execute: cancel, refund",
    "User cancelled pending actions"
  ],
  "response": "No actions were performed. Pending actions were cancelled."
}
```

## Usage Example

### Step 1: User sends message requesting actions

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "cancel and refund my order",
    "order_id": "12345"
  }'
```

**Response** shows `pending_actions: ["cancel", "refund"]` and `awaiting_confirmation: true`

### Step 2a: User confirms the actions

```bash
curl -X POST http://localhost:8000/actions/confirm \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "the-session-id",
    "order_id": "12345",
    "confirmed": true
  }'
```

**Result**: Actions are executed

### Step 2b: User cancels the actions

```bash
curl -X POST http://localhost:8000/actions/confirm \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "the-session-id",
    "order_id": "12345",
    "confirmed": false
  }'
```

**Result**: Pending actions are discarded

## Key Features

1. **Action Display**: Pending actions are shown in the response after `/chat` endpoint
2. **User Confirmation**: Required before any actions are executed
3. **Cancellation**: Users can cancel pending actions at any time
4. **Refund Support**: Both `cancel` and `refund` actions are available
5. **State Persistence**: All actions and confirmations are saved in the database
6. **Logging**: All operations are logged for audit trail

## Implementation Details

### analyze() Node

- Receives user message
- Calls LLM with system prompt and memory context
- Parses JSON response to extract actions
- Returns `pending_actions` list and sets `user_confirmed: false`

### display_actions() Node

- Logs pending actions for user review
- Displays action list in the response
- Waits for user confirmation before proceeding

### execute() Node

- Only executes if `user_confirmed: true`
- Executes actions one by one
- Logs each action result
- Updates `executed_actions` list

### generate_response() Node

- Creates summary of executed actions
- Returns final response to user

## Database Schema

**Sessions Table**:

- `session_id`: Unique session identifier
- `created_at`: Session creation time
- `updated_at`: Last activity time
- `metadata`: Additional session data

**State History Table**:

- Stores snapshots of agent state after each step
- Includes `pending_actions`, `actions`, and `executed_actions`

**Interactions Table**:

- Records of all user-agent interactions
- Includes user message, order_id, and all actions taken

## Notes

- LLM is configurable: Falls back from langchain-ollama to ChatGoogleGenerativeAI
- Actions are stored in pending state until confirmed
- Session data persists across API calls
- All operations are logged for audit and debugging

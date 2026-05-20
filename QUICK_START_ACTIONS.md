# Quick Start: Action Confirmation System

## What Changed?

The agent now **requires user confirmation before executing actions**. Instead of immediately canceling or refunding orders, the agent shows the user what it will do and waits for confirmation.

## How to Use

### 1. User Requests Actions (API Call)

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "cancel my order",
    "order_id": "ORDER-12345"
  }'
```

### 2. Check the Response

The API returns:

```json
{
  "success": true,
  "session_id": "abc123...",
  "pending_actions": ["cancel"],
  "executed_actions": [],
  "awaiting_confirmation": true,
  "logs": ["Pending actions to execute: cancel"],
  "response": "No actions were performed."
}
```

**Key Fields**:

- `pending_actions`: Actions that will be executed (if confirmed)
- `awaiting_confirmation`: true = waiting for user to confirm
- `executed_actions`: Empty (actions haven't run yet!)
- `response`: "No actions were performed" (because nothing executed yet)

### 3. User Confirms or Cancels

**To Confirm (Execute the Actions)**:

```bash
curl -X POST http://localhost:8000/actions/confirm \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "abc123...",
    "order_id": "ORDER-12345",
    "confirmed": true
  }'
```

Response:

```json
{
  "success": true,
  "message": "Actions executed successfully",
  "executed_actions": ["cancel"],
  "logs": ["Pending actions to execute: cancel", "Order ORDER-12345 canceled"],
  "response": "Completed actions: cancel"
}
```

**To Cancel (Don't Execute)**:

```bash
curl -X POST http://localhost:8000/actions/confirm \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "abc123...",
    "order_id": "ORDER-12345",
    "confirmed": false
  }'
```

Response:

```json
{
  "success": true,
  "message": "Pending actions cancelled and discarded",
  "executed_actions": [],
  "logs": [
    "Pending actions to execute: cancel",
    "User cancelled pending actions"
  ],
  "response": "No actions were performed. Pending actions were cancelled."
}
```

## Key Points

✅ **Actions shown before execution** - Users see what will happen  
✅ **User can cancel** - No unwanted actions  
✅ **Refund and cancel both available** - Full order management  
✅ **All logged** - Audit trail of all confirmations  
✅ **Session persists** - State saved between calls

## Available Actions

The agent can identify and execute:

- `cancel` - Cancel an order
- `refund` - Refund an order
- `none` - No actions needed

## Flow Diagram

```
User Message
    ↓
Agent Analyzes
    ↓
Shows Pending Actions ← STOP HERE - WAITING FOR USER
    ↓
User Confirms/Cancels
    ↓
If Confirmed: Execute Actions
If Cancelled: Discard Actions
    ↓
Return Result
```

## Example Scenarios

### Scenario 1: Cancel Order

```
User: "I want to cancel order ORDER-12345"
      ↓
Agent: "I found the action: cancel"
       Response shows pending_actions: ["cancel"]
       ← WAITING FOR CONFIRMATION ←
User: Calls /actions/confirm with confirmed=true
      ↓
Agent: Executes cancel action
       Returns: executed_actions: ["cancel"]
```

### Scenario 2: Cancel and Refund

```
User: "Cancel and refund my order"
      ↓
Agent: "I found actions: cancel, refund"
       Response shows pending_actions: ["cancel", "refund"]
       ← WAITING FOR CONFIRMATION ←
User: Calls /actions/confirm with confirmed=true
      ↓
Agent: Executes cancel, then refund
       Returns: executed_actions: ["cancel", "refund"]
```

### Scenario 3: User Changes Mind

```
User: "Cancel my order"
      ↓
Agent: "I found action: cancel"
       Response shows pending_actions: ["cancel"]
       ← WAITING FOR CONFIRMATION ←
User: Changes mind, calls /actions/confirm with confirmed=false
      ↓
Agent: Discards the cancel action
       Returns: executed_actions: []
       Message: "Pending actions cancelled and discarded"
```

## Implementation Details

### LangGraph Flow

```
analyze (identify actions)
   ↓
display_actions (show to user, wait for confirmation)
   ↓
execute (only if user confirmed)
   ↓
generate_response (return result)
   ↓
END
```

### State Fields

- `pending_actions`: Actions waiting for confirmation
- `user_confirmed`: Whether user confirmed (true/false)
- `executed_actions`: Actions that actually ran
- `actions`: Working list of actions
- `logs`: All operation logs

## Database

All sessions, confirmations, and actions are saved to `agent_state.db`:

- **sessions table**: Session metadata
- **state_history**: Snapshots of state
- **interactions**: User interactions and results

## Troubleshooting

### "Session not found"

- The session_id from `/chat` response is required for `/actions/confirm`
- Copy it exactly from the `/chat` response

### "No actions identified"

- Check if the LLM (Ollama or Google Genai) is properly configured
- Ensure the message clearly indicates what action is needed

### Actions not executing

- Verify `confirmed: true` in the `/actions/confirm` request
- Check logs for error messages
- Ensure order_id is correct

## Configuration

The system supports two LLMs:

1. **Local Ollama** (preferred):
   - Requires `langchain-ollama` installed
   - Uses `llama3.1:8b` model
   - No API key needed

2. **Google Genai** (fallback):
   - Requires `GOOGLE_API_KEY` in .env
   - Uses `gemini-2.5-flash` model
   - Cloud-based

Switch between them by:

1. Having `langchain-ollama` installed → Uses Ollama
2. Removing it or having error → Falls back to Google Genai

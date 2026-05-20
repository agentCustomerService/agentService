# Agent Service with Action Confirmation System

## 🎯 Overview

A FastAPI-based order management agent that uses LangGraph and LLM to identify and execute actions like canceling or refunding orders. The system requires **user confirmation before executing any action**, providing full control and transparency.

**Features:**

- ✅ Actions displayed to users **before execution**
- ✅ User **confirmation required** for all operations
- ✅ Users can **cancel** pending actions anytime
- ✅ Support for both **cancel** and **refund** operations
- ✅ Optional **RAG-based policy system** (with agent_with_rag.py)
- ✅ Complete **audit trail** of all operations
- ✅ **Session persistence** across API calls

---

## 🚀 Quick Start (5 Minutes)

### Installation

```bash
pip install -r requirements.txt
```

### Start Server

```bash
uvicorn app:api --reload
```

### Test the Workflow

**Step 1: Send message to /chat**

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I want to cancel my order",
    "order_id": "ORD-12345"
  }'
```

**Response:**

```json
{
  "success": true,
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "pending_actions": ["cancel"],
  "executed_actions": [],
  "awaiting_confirmation": true,
  "logs": ["Pending actions to execute: cancel"],
  "response": "No actions were performed."
}
```

**Step 2a: User confirms the action**

```bash
curl -X POST http://localhost:8000/actions/confirm \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "order_id": "ORD-12345",
    "confirmed": true
  }'
```

**Result:** Action executed and returned

**Step 2b: Or user cancels the action**

```bash
curl -X POST http://localhost:8000/actions/confirm \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "order_id": "ORD-12345",
    "confirmed": false
  }'
```

**Result:** Action discarded, nothing executed

---

## 📁 Project Structure

```
agent/
├── agent.py                    # Main agent with LangGraph
├── app.py                      # FastAPI application
├── agent_with_rag.py          # Agent with RAG/policy support
├── app_with_rag.py            # FastAPI with RAG support
├── models.py                  # Pydantic models
├── state_manager.py           # Session and state management
├── db.py                      # Database operations
├── rag_policies.py            # RAG policy system
├── services/
│   └── orders.py              # Order service client
├── policies/                  # Policy directory for RAG
├── agent_state.db             # SQLite database
├── requirements.txt           # Python dependencies
└── README_FINAL.md           # This file
```

---

## 🔄 How It Works

### Workflow

```
1. User sends message
        ↓
2. LLM identifies actions (cancel, refund, none)
        ↓
3. Actions displayed to user
   (awaiting_confirmation = true)
        ↓
4. User must confirm or cancel
   POST /actions/confirm
        ↓
5a. If confirmed=true:
    → Execute actions
    → Return results

5b. If confirmed=false:
    → Discard pending actions
    → Return cancellation message
```

### State Flow

**Initial State (after analyze):**

```python
{
    "pending_actions": ["cancel", "refund"],
    "user_confirmed": false,
    "executed_actions": [],
    "logs": ["Pending actions to execute: cancel, refund"]
}
```

**After User Confirmation (after execute):**

```python
{
    "pending_actions": [],
    "user_confirmed": true,
    "executed_actions": ["cancel", "refund"],
    "logs": [
        "Pending actions to execute: cancel, refund",
        "Order ORD-12345 canceled",
        "Order ORD-12345 refunded"
    ]
}
```

---

## 📊 LangGraph Flow

```
START
  │
  ├─→ analyze (LLM identifies actions)
  │
  ├─→ should_display_actions (Router)
  │   If pending_actions: → display_actions
  │   Else: → generate_response
  │
  ├─→ display_actions (Show to user, wait for confirmation)
  │
  ├─→ execute (Only if user_confirmed=true)
  │   Executes actions one by one
  │
  ├─→ should_continue (Router)
  │   If more actions: → execute (loop)
  │   Else: → generate_response
  │
  ├─→ generate_response (Create summary)
  │
  └─→ END
```

---

## 🌐 API Endpoints

### Chat Endpoint

**POST /chat**

- **Input:** `message`, `order_id`, (optional) `session_id`
- **Output:** `pending_actions`, `executed_actions`, `awaiting_confirmation`, `logs`
- **Purpose:** Analyze user message and identify pending actions

### Action Confirmation Endpoint

**POST /actions/confirm**

- **Input:** `session_id`, `order_id`, `confirmed` (true/false)
- **Output:** `executed_actions`, `logs`, `response`
- **Purpose:** Execute or cancel pending actions

### Session Management

- `GET /sessions` - List all sessions
- `GET /sessions/{session_id}` - Get session info
- `GET /sessions/{session_id}/history` - Get interaction history

### RAG Policy Endpoints (RAG version only)

- `GET /policies` - Get loaded policies
- `GET /policies/list` - List all loaded policies
- `GET /policies/cancellation` - Get cancellation policies
- `GET /policies/refund` - Get refund policies
- `GET /policies/all` - Get all policies

---

## 🛠️ Configuration

### Environment Variables

```bash
# Required for Google Genai fallback
GOOGLE_API_KEY=your-api-key-here

# Optional (defaults below)
# OLLAMA_BASE_URL=http://localhost:11434
# OLLAMA_MODEL=llama3.1:8b
```

### LLM Support

The system automatically selects the best available LLM:

1. **Local Ollama** (preferred)
   - No API key required
   - Model: llama3.1:8b
   - Fast and private

2. **Google Genai** (fallback)
   - Requires GOOGLE_API_KEY
   - Model: gemini-2.5-flash
   - Cloud-based

---

## 📚 Implementation Details

### Modified Files

1. **agent.py** - Core agent logic
   - Added `display_actions` node
   - Added `pending_actions` and `user_confirmed` to state
   - Added confirmation flow

2. **app.py** - FastAPI application
   - Updated `/chat` endpoint
   - Added `/actions/confirm` endpoint
   - Full request/response handling

3. **models.py** - Data models
   - Added `ConfirmActionsRequest` model
   - Updated `ChatResponse` with confirmation fields

4. **state_manager.py** - State management
   - Added `get_session()` method

5. **db.py** - Database operations
   - Enhanced `get_session()` to include latest state

6. **agent_with_rag.py** - RAG version of agent
   - Same changes as agent.py
   - Plus policy integration

7. **app_with_rag.py** - RAG version of FastAPI
   - Same changes as app.py
   - Plus policy endpoints and RAG management

8. **requirements.txt**
   - Added `langchain-ollama==0.2.0`

---

## 🎯 Available Actions

The LLM can identify these actions from user messages:

- **`cancel`** - Cancel the order
- **`refund`** - Refund the order
- **`none`** - No action needed

Multiple actions can be combined:

- "Cancel and refund" → `["cancel", "refund"]`
- "Just cancel" → `["cancel"]`
- "Give me my money back" → `["refund"]`

---

## 💾 Database

### SQLite Database (`agent_state.db`)

**Sessions Table**

- `session_id` - Unique identifier
- `created_at` - Creation timestamp
- `updated_at` - Last activity
- `metadata` - Additional data

**State History Table**

- Stores snapshots of agent state
- Tracks `pending_actions`, `executed_actions`, logs
- Full state reconstruction possible

**Interactions Table**

- Records of all user-agent interactions
- Complete audit trail
- Can retrieve history by session

---

## 🧪 Testing

### Run Example Tests

```bash
python test_action_confirmation.py
```

### Manual Testing with cURL

**1. Test identify actions:**

```bash
curl -X POST http://localhost:8000/chat \
  -d '{"message":"cancel order","order_id":"123"}'
```

**2. Test confirm:**

```bash
curl -X POST http://localhost:8000/actions/confirm \
  -d '{"session_id":"...","order_id":"123","confirmed":true}'
```

**3. Test cancel:**

```bash
curl -X POST http://localhost:8000/actions/confirm \
  -d '{"session_id":"...","order_id":"123","confirmed":false}'
```

### Python Testing

```python
import requests

# Send message
response = requests.post(
    "http://localhost:8000/chat",
    json={
        "message": "cancel my order",
        "order_id": "ORD-123"
    }
)

session_id = response.json()["session_id"]

# Confirm actions
confirm = requests.post(
    "http://localhost:8000/actions/confirm",
    json={
        "session_id": session_id,
        "order_id": "ORD-123",
        "confirmed": True
    }
)

print(confirm.json())
```

---

## 🚢 Deployment

### Development

```bash
uvicorn app:api --reload
```

### Production

```bash
uvicorn app:api --host 0.0.0.0 --port 8000 --workers 4
```

### Docker (Optional)

```dockerfile
FROM python:3.11
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "app:api", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 🔍 Troubleshooting

### ImportError: langchain_ollama not found

**Solution:** Install it

```bash
pip install langchain-ollama==0.2.0
```

### GOOGLE_API_KEY required error

**Solution:** Set environment variable

```bash
export GOOGLE_API_KEY=your-key
# or in .env file
echo "GOOGLE_API_KEY=your-key" >> .env
```

### Session not found in /actions/confirm

**Solution:** Use exact `session_id` from `/chat` response

```bash
# Get from response:
RESPONSE=$(curl ... /chat)
SESSION=$(echo $RESPONSE | jq -r '.session_id')

# Use in confirm:
curl ... -d "{\"session_id\": \"$SESSION\", ...}"
```

### No actions identified by LLM

**Solution:** Use clearer message

- Good: "I want to cancel my order"
- Good: "Please refund my order"
- Better: "Cancel and refund my order ORD-123"

---

## 📖 Examples

### Example 1: Cancel Order

```json
Request: {"message": "cancel my order", "order_id": "ORD-001"}
Response: {
  "pending_actions": ["cancel"],
  "awaiting_confirmation": true
}
Confirm: {"confirmed": true}
Result: "Completed actions: cancel"
```

### Example 2: Multiple Actions

```json
Request: {"message": "cancel and refund", "order_id": "ORD-002"}
Response: {
  "pending_actions": ["cancel", "refund"],
  "awaiting_confirmation": true
}
Confirm: {"confirmed": true}
Result: "Completed actions: cancel, refund"
```

### Example 3: User Cancels

```json
Request: {"message": "refund me", "order_id": "ORD-003"}
Response: {
  "pending_actions": ["refund"],
  "awaiting_confirmation": true
}
Confirm: {"confirmed": false}
Result: "No actions were performed"
```

---

## 🔐 Security Notes

- ✅ All confirmations logged
- ✅ Session IDs tracked
- ✅ Audit trail in database
- ✅ No automatic actions
- ✅ User consent required
- ✅ CORS restricted in production
- ⚠️ Set HTTPS in production
- ⚠️ Validate order_id origin
- ⚠️ Restrict API access

---

## 📈 Performance

- **Response Time:** ~500ms (LLM dependent)
- **Database:** SQLite (fine for < 10k sessions)
- **Concurrent Users:** ~50 (single worker)
- **Scale:** Add more workers with load balancer

---

## 🤝 Integration

### With Existing Systems

1. Replace `/orders/cancel` calls with agent API
2. Always check `awaiting_confirmation` flag
3. Implement user confirmation UI
4. Store `session_id` for tracking
5. Poll `/sessions/{id}/history` for updates

### Example Integration

```python
# Old way (risky)
cancel_order(order_id)

# New way (safe)
chat_response = send_chat(message, order_id)
if chat_response["awaiting_confirmation"]:
    # Show UI for user to confirm
    confirmed = get_user_confirmation()
    if confirmed:
        confirm_actions(session_id, order_id, True)
    else:
        confirm_actions(session_id, order_id, False)
```

---

## ✨ Key Features Comparison

| Feature           | Before     | After       |
| ----------------- | ---------- | ----------- |
| Action visibility | ❌ Hidden  | ✅ Shown    |
| User control      | ❌ None    | ✅ Full     |
| Confirmation      | ❌ Auto    | ✅ Manual   |
| Cancellation      | ❌ No      | ✅ Yes      |
| Audit trail       | ⚠️ Basic   | ✅ Complete |
| Session state     | ✅ Yes     | ✅ Enhanced |
| Multiple actions  | ⚠️ Limited | ✅ Full     |

---

## 📞 Support

### Need Help?

1. **Check examples** - See "Examples" section above
2. **Run tests** - `python test_action_confirmation.py`
3. **Check logs** - Server output shows detailed logs
4. **Review database** - `sqlite3 agent_state.db .tables`

### Common Issues

| Issue             | Solution                               |
| ----------------- | -------------------------------------- |
| Actions not shown | Check message clarity                  |
| Session not found | Use exact session_id from response     |
| LLM errors        | Check GOOGLE_API_KEY or Ollama running |
| DB errors         | Delete agent_state.db to reset         |

---

## 📋 Version History

- **v1.0.0** (2026-05-20) - Initial release with action confirmation
  - Both regular and RAG versions
  - Full API endpoints
  - Database persistence
  - Complete documentation

---

## 📄 License

This project is part of the Agent Service system.

---

## 🎉 Summary

The Agent Service provides a **safe, user-controlled** way to manage order operations:

1. **Transparency** - Users see what will happen
2. **Control** - Users confirm before execution
3. **Safety** - No accidental operations
4. **Auditability** - Complete operation history
5. **Flexibility** - Works with or without RAG policies

**Start using it now:**

```bash
pip install -r requirements.txt
uvicorn app:api --reload
curl http://localhost:8000/
```

Happy ordering! 🚀

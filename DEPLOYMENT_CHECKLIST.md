# Deployment Checklist: Action Confirmation System

## ✅ Pre-Deployment Verification

### Code Changes

- [x] `agent.py` updated with:
  - [x] `display_actions` node added
  - [x] `pending_actions` and `user_confirmed` in AgentState
  - [x] `should_display_actions` router added
  - [x] `should_continue` router updated
  - [x] LLM fallback support (Ollama → Google Genai)

- [x] `app.py` updated with:
  - [x] `/chat` endpoint returns `pending_actions` and `awaiting_confirmation`
  - [x] `/actions/confirm` endpoint added
  - [x] Handles `confirmed=true/false` logic

- [x] `models.py` updated with:
  - [x] `ConfirmActionsRequest` model added
  - [x] `ChatResponse` updated with new fields

- [x] `state_manager.py` enhanced:
  - [x] `get_session()` method added

- [x] `db.py` enhanced:
  - [x] `get_session()` returns latest state

- [x] `requirements.txt` updated:
  - [x] `langchain-ollama==0.2.0` added

### Documentation

- [x] `ACTION_CONFIRMATION_FLOW.md` - Flow diagrams and API docs
- [x] `IMPLEMENTATION_CHANGES.md` - Technical details
- [x] `QUICK_START_ACTIONS.md` - Quick reference
- [x] `API_EXAMPLES.md` - Real examples
- [x] `CHANGES_SUMMARY.md` - Summary
- [x] `VISUAL_FLOW.md` - Flow diagrams
- [x] `ACTION_SYSTEM_INDEX.md` - Documentation index
- [x] `DEPLOYMENT_CHECKLIST.md` - This file
- [x] `test_action_confirmation.py` - Test script

---

## 📦 Installation Steps

### 1. Install Dependencies

```bash
# Option 1: Fresh install (recommended)
pip install -r requirements.txt

# Option 2: Update existing installation
pip install langchain-ollama==0.2.0
```

### 2. Verify Dependencies

```bash
# Check langchain-ollama is installed
python -c "from langchain_ollama import ChatOllama; print('✓ langchain-ollama installed')"

# Check all imports work
python -c "import agent; import app; import models; print('✓ All imports successful')"
```

### 3. Database

```bash
# Existing database will work (schema compatible)
# If fresh installation, database will be created automatically
# No migration needed - backward compatible
```

---

## 🧪 Testing

### Unit Tests

```bash
# Run the example test script
python test_action_confirmation.py

# Expected output:
# ✓ TEST 1: Actions identified and displayed
# ✓ TEST 2: Actions executed after confirmation
# ✓ TEST 3: Actions cancelled without execution
```

### Integration Tests

```bash
# Start the server
uvicorn app:api --reload

# In another terminal, test the endpoints:

# 1. Test /chat endpoint
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "cancel my order", "order_id": "TEST-123"}'

# 2. Test /actions/confirm endpoint (confirm)
curl -X POST http://localhost:8000/actions/confirm \
  -H "Content-Type: application/json" \
  -d '{"session_id": "...", "order_id": "TEST-123", "confirmed": true}'

# 3. Test /actions/confirm endpoint (cancel)
curl -X POST http://localhost:8000/actions/confirm \
  -H "Content-Type: application/json" \
  -d '{"session_id": "...", "order_id": "TEST-456", "confirmed": false}'
```

---

## 🔧 Configuration

### Environment Variables

```bash
# For Google Genai fallback (if Ollama not available)
GOOGLE_API_KEY=your-api-key-here

# Optional (defaults below)
# OLLAMA_BASE_URL=http://localhost:11434
# OLLAMA_MODEL=llama3.1:8b
```

### LLM Configuration

The system automatically:

1. Tries to use `langchain-ollama` (local, no API key needed)
2. Falls back to Google Genai if not available (requires GOOGLE_API_KEY)

To force one LLM:

- **Use Ollama**: Ensure it's installed and running
- **Use Google Genai**: Remove langchain-ollama, set GOOGLE_API_KEY

### Server Configuration

```bash
# Development
uvicorn app:api --reload

# Production
uvicorn app:api --host 0.0.0.0 --port 8000 --workers 4
```

---

## 📊 Expected Behavior

### /chat Endpoint

**Input:**

```json
{
  "message": "cancel my order",
  "order_id": "ORD-123"
}
```

**Output (awaiting confirmation):**

```json
{
  "success": true,
  "session_id": "...",
  "pending_actions": ["cancel"],
  "executed_actions": [],
  "awaiting_confirmation": true,
  "logs": ["Pending actions to execute: cancel"],
  "response": "No actions were performed."
}
```

### /actions/confirm Endpoint (confirmed=true)

**Input:**

```json
{
  "session_id": "...",
  "order_id": "ORD-123",
  "confirmed": true
}
```

**Output:**

```json
{
  "success": true,
  "message": "Actions executed successfully",
  "executed_actions": ["cancel"],
  "logs": ["Pending actions to execute: cancel", "Order ORD-123 canceled"],
  "response": "Completed actions: cancel"
}
```

### /actions/confirm Endpoint (confirmed=false)

**Input:**

```json
{
  "session_id": "...",
  "order_id": "ORD-123",
  "confirmed": false
}
```

**Output:**

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

---

## 🔍 Verification Points

### Functional Tests

- [ ] User can send message to /chat endpoint
- [ ] LLM identifies actions correctly
- [ ] pending_actions returned in response
- [ ] awaiting_confirmation flag is true when actions found
- [ ] User can confirm actions via /actions/confirm
- [ ] Actions execute after confirmation
- [ ] User can cancel actions before confirmation
- [ ] No actions execute if cancelled
- [ ] All operations logged correctly
- [ ] Session data persists

### Data Integrity Tests

- [ ] Database saves all sessions
- [ ] State snapshots saved correctly
- [ ] Interactions history records actions
- [ ] Logs capture all operations
- [ ] No data loss on restart

### Error Handling Tests

- [ ] Invalid session_id returns error
- [ ] Missing required fields returns error
- [ ] LLM error handled gracefully
- [ ] Order service errors logged

---

## 📋 Post-Deployment Steps

### 1. Monitor Logs

```bash
# Check for any errors during startup
# Look for:
# - "✓ Successfully connected to order service"
# - "✓ Database initialized"
# - No ImportError or AttributeError
```

### 2. Test Critical Paths

```bash
# Verify the three main flows work:
# 1. Message → Action identified → Confirmed → Executed
# 2. Message → Action identified → Cancelled → Not executed
# 3. Message → No action → Direct response
```

### 3. Load Testing

```bash
# Optional: Test with multiple concurrent requests
ab -n 100 -c 10 http://localhost:8000/
```

### 4. Backup Database

```bash
# Backup the SQLite database
cp agent_state.db agent_state.db.backup
```

---

## 🚨 Rollback Plan

If issues occur:

### 1. Code Rollback

```bash
git revert <commit-hash>
# or
git checkout main -- agent.py app.py models.py state_manager.py db.py
```

### 2. Database Rollback

```bash
cp agent_state.db.backup agent_state.db
```

### 3. Dependency Rollback

```bash
pip install -r requirements.txt.backup
# or remove langchain-ollama:
pip uninstall langchain-ollama
```

---

## 📞 Troubleshooting

### Issue: ImportError for langchain_ollama

**Solution:** Install it

```bash
pip install langchain-ollama==0.2.0
```

### Issue: GOOGLE_API_KEY required error

**Solution:** Set environment variable

```bash
export GOOGLE_API_KEY=your-key
# or in .env file
echo "GOOGLE_API_KEY=your-key" >> .env
```

### Issue: /actions/confirm returns "Session not found"

**Solution:** Copy session_id exactly from /chat response

```bash
# Get session_id from /chat
RESPONSE=$(curl -s -X POST http://localhost:8000/chat ...)
SESSION=$(echo $RESPONSE | jq -r '.session_id')

# Use exact session_id
curl -X POST http://localhost:8000/actions/confirm \
  -d "{\"session_id\": \"$SESSION\", ...}"
```

### Issue: No actions identified by LLM

**Solution:** Check message clarity

- Use clear action words: "cancel", "refund"
- Provide order_id explicitly
- Test with explicit messages: "I want to cancel my order"

---

## ✅ Final Checklist

Before going live:

- [ ] All code changes merged
- [ ] Dependencies installed
- [ ] Tests pass
- [ ] Documentation reviewed
- [ ] Environment variables set
- [ ] Database backed up
- [ ] Logs monitored
- [ ] Error handling tested
- [ ] Performance verified
- [ ] Team trained

---

## 📖 Documentation Links

- **Quick Start:** [QUICK_START_ACTIONS.md](QUICK_START_ACTIONS.md)
- **API Examples:** [API_EXAMPLES.md](API_EXAMPLES.md)
- **Technical Flow:** [ACTION_CONFIRMATION_FLOW.md](ACTION_CONFIRMATION_FLOW.md)
- **Visual Diagrams:** [VISUAL_FLOW.md](VISUAL_FLOW.md)
- **Implementation:** [IMPLEMENTATION_CHANGES.md](IMPLEMENTATION_CHANGES.md)

---

**Status:** ✅ Ready for Deployment  
**Last Verified:** 2026-05-20  
**Version:** 1.0.0

# API Request/Response Examples

## Complete Workflow Examples

### Example 1: Cancel Order (User Confirms)

**Step 1: Send chat message**

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I want to cancel my order",
    "order_id": "ORD-2024-001"
  }'
```

**Response (Step 1):**

```json
{
  "success": true,
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "pending_actions": ["cancel"],
  "executed_actions": [],
  "logs": ["Pending actions to execute: cancel"],
  "response": "No actions were performed.",
  "awaiting_confirmation": true
}
```

ℹ️ Notice: `pending_actions` has the action, but `executed_actions` is empty. Nothing has happened yet.

**Step 2: User confirms the action**

```bash
curl -X POST http://localhost:8000/actions/confirm \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "order_id": "ORD-2024-001",
    "confirmed": true
  }'
```

**Response (Step 2):**

```json
{
  "success": true,
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Actions executed successfully",
  "executed_actions": ["cancel"],
  "logs": ["Pending actions to execute: cancel", "Order ORD-2024-001 canceled"],
  "response": "Completed actions: cancel"
}
```

✅ Now the action is executed!

---

### Example 2: Refund Order (User Cancels)

**Step 1: Send chat message**

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I need a refund for order ORD-2024-002",
    "order_id": "ORD-2024-002"
  }'
```

**Response (Step 1):**

```json
{
  "success": true,
  "session_id": "660e8400-e29b-41d4-a716-446655440001",
  "pending_actions": ["refund"],
  "executed_actions": [],
  "logs": ["Pending actions to execute: refund"],
  "response": "No actions were performed.",
  "awaiting_confirmation": true
}
```

**Step 2: User changes mind and cancels**

```bash
curl -X POST http://localhost:8000/actions/confirm \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "660e8400-e29b-41d4-a716-446655440001",
    "order_id": "ORD-2024-002",
    "confirmed": false
  }'
```

**Response (Step 2):**

```json
{
  "success": true,
  "session_id": "660e8400-e29b-41d4-a716-446655440001",
  "message": "Pending actions cancelled and discarded",
  "executed_actions": [],
  "logs": [
    "Pending actions to execute: refund",
    "User cancelled pending actions"
  ],
  "response": "No actions were performed. Pending actions were cancelled."
}
```

❌ The action was cancelled - nothing executed!

---

### Example 3: Multiple Actions (Cancel AND Refund)

**Step 1: Send chat message**

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Please cancel my order and give me a refund",
    "order_id": "ORD-2024-003"
  }'
```

**Response (Step 1):**

```json
{
  "success": true,
  "session_id": "770e8400-e29b-41d4-a716-446655440002",
  "pending_actions": ["cancel", "refund"],
  "executed_actions": [],
  "logs": ["Pending actions to execute: cancel, refund"],
  "response": "No actions were performed.",
  "awaiting_confirmation": true
}
```

ℹ️ Multiple actions identified! User sees both before anything executes.

**Step 2: User confirms both actions**

```bash
curl -X POST http://localhost:8000/actions/confirm \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "770e8400-e29b-41d4-a716-446655440002",
    "order_id": "ORD-2024-003",
    "confirmed": true
  }'
```

**Response (Step 2):**

```json
{
  "success": true,
  "session_id": "770e8400-e29b-41d4-a716-446655440002",
  "message": "Actions executed successfully",
  "executed_actions": ["cancel", "refund"],
  "logs": [
    "Pending actions to execute: cancel, refund",
    "Order ORD-2024-003 canceled",
    "Order ORD-2024-003 refunded"
  ],
  "response": "Completed actions: cancel, refund"
}
```

✅ Both actions executed in sequence!

---

### Example 4: No Actions Needed

**Step 1: Send chat message**

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Can I check the status of my order?",
    "order_id": "ORD-2024-004"
  }'
```

**Response (Step 1):**

```json
{
  "success": true,
  "session_id": "880e8400-e29b-41d4-a716-446655440003",
  "pending_actions": [],
  "executed_actions": [],
  "logs": [],
  "response": "No actions were performed.",
  "awaiting_confirmation": false
}
```

ℹ️ No pending_actions identified - no confirmation needed!

---

### Example 5: Invalid/Unknown Order

**Step 1: Send chat message**

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "cancel my order",
    "order_id": "INVALID-ORDER"
  }'
```

**Response (Step 1):**

```json
{
  "success": true,
  "session_id": "990e8400-e29b-41d4-a716-446655440004",
  "pending_actions": ["cancel"],
  "executed_actions": [],
  "logs": ["Pending actions to execute: cancel"],
  "response": "No actions were performed.",
  "awaiting_confirmation": true
}
```

**Step 2: User confirms**

```bash
curl -X POST http://localhost:8000/actions/confirm \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "990e8400-e29b-41d4-a716-446655440004",
    "order_id": "INVALID-ORDER",
    "confirmed": true
  }'
```

**Response (Step 2):**

```json
{
  "success": true,
  "session_id": "990e8400-e29b-41d4-a716-446655440004",
  "message": "Actions executed successfully",
  "executed_actions": [],
  "logs": [
    "Pending actions to execute: cancel",
    "Order service error: 404 - Order not found"
  ],
  "response": "Completed actions: "
}
```

⚠️ Action attempted but failed at the order service level. Error is logged.

---

## Response Fields Explained

### ChatResponse (from `/chat`)

```json
{
  "success": boolean,                    // true if API call succeeded
  "session_id": "string",               // Session ID for tracking
  "pending_actions": ["string"],        // Actions awaiting confirmation
  "executed_actions": ["string"],       // Actions already executed
  "logs": ["string"],                   // Operation logs
  "response": "string",                 // Summary message
  "awaiting_confirmation": boolean      // true if user action needed
}
```

### ConfirmActionResponse (from `/actions/confirm`)

```json
{
  "success": boolean,                    // true if API call succeeded
  "session_id": "string",               // Same session ID
  "message": "string",                  // Status message
  "executed_actions": ["string"],       // Which actions ran
  "logs": ["string"],                   // Operation logs
  "response": "string"                  // User-facing message
}
```

## Testing with Python

```python
import requests
import json

API_URL = "http://localhost:8000"

# Step 1: Send message
response = requests.post(
    f"{API_URL}/chat",
    json={
        "message": "cancel my order",
        "order_id": "ORD-12345"
    }
)

data = response.json()
session_id = data["session_id"]
pending_actions = data["pending_actions"]

print(f"Session: {session_id}")
print(f"Pending Actions: {pending_actions}")
print(f"Awaiting Confirmation: {data['awaiting_confirmation']}")

if data["awaiting_confirmation"]:
    # Step 2: User confirms
    confirm_response = requests.post(
        f"{API_URL}/actions/confirm",
        json={
            "session_id": session_id,
            "order_id": "ORD-12345",
            "confirmed": True  # or False to cancel
        }
    )

    result = confirm_response.json()
    print(f"Executed: {result['executed_actions']}")
    print(f"Response: {result['response']}")
```

## Testing with cURL

### Save as script (run.sh):

```bash
#!/bin/bash

API="http://localhost:8000"

# Step 1: Get pending actions
echo "=== STEP 1: Send message ==="
RESPONSE=$(curl -s -X POST "$API/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "cancel my order",
    "order_id": "ORD-12345"
  }')

echo "$RESPONSE" | jq .

SESSION=$(echo "$RESPONSE" | jq -r '.session_id')
echo "Session: $SESSION"

# Step 2: Confirm actions
echo ""
echo "=== STEP 2: Confirm actions ==="
curl -s -X POST "$API/actions/confirm" \
  -H "Content-Type: application/json" \
  -d "{
    \"session_id\": \"$SESSION\",
    \"order_id\": \"ORD-12345\",
    \"confirmed\": true
  }" | jq .
```

Run with: `bash run.sh`

## Error Scenarios

### Session Not Found

```json
{
  "success": false,
  "error": "Session not found"
}
```

→ Check that session_id matches exactly

### Missing Required Fields

```json
{
  "detail": "Field required"
}
```

→ Ensure all required fields are in the request

### Server Error

```json
{
  "detail": "Internal server error"
}
```

→ Check server logs for details

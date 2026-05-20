# Quick Reference: Agent State & Memory

## New Files

- `db.py` - Database layer with SQLite operations
- `state_manager.py` - State management API
- `test_state_memory.py` - Test suite
- `STATE_AND_MEMORY.md` - Full documentation
- `IMPLEMENTATION_SUMMARY.md` - Implementation overview

## Modified Files

- `agent.py` - Added session_id and memory context
- `models.py` - Added session-related models
- `app.py` - Added session management endpoints

## API Endpoints

| Method | Endpoint                 | Purpose                                     |
| ------ | ------------------------ | ------------------------------------------- |
| POST   | `/chat`                  | Execute agent (auto-creates/reuses session) |
| GET    | `/sessions`              | List all sessions                           |
| GET    | `/sessions/{id}`         | Get session info                            |
| GET    | `/sessions/{id}/history` | Get interaction history                     |

## Usage Examples

### Start a new session (auto-generated):

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Cancel order 123", "order_id": "123"}'
```

### Continue a session:

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Refund order 123",
    "order_id": "123",
    "session_id": "uuid-from-first-request"
  }'
```

### View all sessions:

```bash
curl http://localhost:8000/sessions
```

### View session history:

```bash
curl http://localhost:8000/sessions/uuid-here/history
```

## Database Schema

**sessions**: session_id, created_at, updated_at, metadata
**state_history**: id, session_id, timestamp, state
**interactions**: id, session_id, timestamp, user_message, order_id, actions, executed_actions, response, logs

## How Memory Works

1. Agent makes a decision
2. Decision is saved to database
3. On next request in same session:
   - Database retrieves past interactions
   - Memory is formatted as text context
   - Context is added to agent's prompt
   - Agent can reference past decisions

## Testing

```bash
python test_state_memory.py
```

All tests pass ✓

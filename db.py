import sqlite3
import json
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent / "agent_state.db"


def init_db():
    """Initialize the database with required tables."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Sessions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            metadata TEXT
        )
    """)

    # State history table - stores snapshots of agent state
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS state_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            state TEXT NOT NULL,
            FOREIGN KEY (session_id) REFERENCES sessions(session_id)
        )
    """)

    # Memory/interactions table - stores conversation history
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS interactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            user_message TEXT,
            order_id TEXT,
            actions TEXT,
            executed_actions TEXT,
            response TEXT,
            logs TEXT,
            FOREIGN KEY (session_id) REFERENCES sessions(session_id)
        )
    """)

    conn.commit()
    conn.close()


def create_session(session_id: str, metadata: dict = None) -> bool:
    """Create a new session."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    now = datetime.utcnow().isoformat()
    
    try:
        cursor.execute("""
            INSERT INTO sessions (session_id, created_at, updated_at, metadata)
            VALUES (?, ?, ?, ?)
        """, (session_id, now, now, json.dumps(metadata or {})))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def get_session(session_id: str) -> dict:
    """Get session info."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT session_id, created_at, updated_at, metadata
        FROM sessions WHERE session_id = ?
    """, (session_id,))
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            "session_id": row[0],
            "created_at": row[1],
            "updated_at": row[2],
            "metadata": json.loads(row[3])
        }
    return None


def save_state_snapshot(session_id: str, state: dict) -> None:
    """Save a snapshot of the agent state."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    now = datetime.utcnow().isoformat()
    
    cursor.execute("""
        INSERT INTO state_history (session_id, timestamp, state)
        VALUES (?, ?, ?)
    """, (session_id, now, json.dumps(state)))
    
    conn.commit()
    conn.close()


def save_interaction(session_id: str, user_message: str, order_id: str, 
                     actions: list, executed_actions: list, response: str, 
                     logs: list) -> None:
    """Save an interaction to the memory."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    now = datetime.utcnow().isoformat()
    
    cursor.execute("""
        INSERT INTO interactions 
        (session_id, timestamp, user_message, order_id, actions, executed_actions, response, logs)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        session_id, now, user_message, order_id,
        json.dumps(actions), json.dumps(executed_actions),
        response, json.dumps(logs)
    ))
    
    conn.commit()
    conn.close()


def get_session_history(session_id: str, limit: int = 10) -> list:
    """Get recent interactions for a session."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, timestamp, user_message, order_id, actions, executed_actions, response, logs
        FROM interactions
        WHERE session_id = ?
        ORDER BY timestamp DESC
        LIMIT ?
    """, (session_id, limit))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [
        {
            "id": row[0],
            "timestamp": row[1],
            "user_message": row[2],
            "order_id": row[3],
            "actions": json.loads(row[4]),
            "executed_actions": json.loads(row[5]),
            "response": row[6],
            "logs": json.loads(row[7])
        }
        for row in rows
    ]


def get_session_memory_context(session_id: str, limit: int = 5) -> str:
    """Get memory context from recent interactions for the agent."""
    history = get_session_history(session_id, limit)
    
    if not history:
        return ""
    
    memory_lines = ["Recent interaction history:"]
    for item in reversed(history):
        memory_lines.append(f"- Order {item['order_id']}: {item['user_message']}")
        if item['executed_actions']:
            memory_lines.append(f"  Actions taken: {', '.join(item['executed_actions'])}")
    
    return "\n".join(memory_lines)


def update_session_timestamp(session_id: str) -> None:
    """Update the session's last updated timestamp."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    now = datetime.utcnow().isoformat()
    
    cursor.execute("""
        UPDATE sessions SET updated_at = ? WHERE session_id = ?
    """, (now, session_id))
    
    conn.commit()
    conn.close()


def list_sessions(limit: int = 20) -> list:
    """List all sessions."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT session_id, created_at, updated_at, metadata
        FROM sessions
        ORDER BY updated_at DESC
        LIMIT ?
    """, (limit,))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [
        {
            "session_id": row[0],
            "created_at": row[1],
            "updated_at": row[2],
            "metadata": json.loads(row[3])
        }
        for row in rows
    ]

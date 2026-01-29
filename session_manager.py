import sqlite3
import json
import uuid
import datetime
from typing import Dict, Optional, List, Any
from loguru import logger

DB_PATH = "sessions.db"

def init_db():
    """Initialize the SQLite database and create the table if it doesn't exist."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # New table for multi-session support
    c.execute('''
        CREATE TABLE IF NOT EXISTS chat_sessions (
            session_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            user_name TEXT,
            session_name TEXT,
            chat_history TEXT,
            last_interaction TIMESTAMP,
            metadata TEXT
        )
    ''')
    conn.commit()
    conn.close()
    logger.info("Database initialized (multi-session).")

def get_user_sessions(user_id: str) -> List[Dict[str, Any]]:
    """Retrieve all sessions for a user, sorted by last interaction (newest first)."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute(
        "SELECT session_id, user_name, session_name, last_interaction FROM chat_sessions WHERE user_id = ? ORDER BY last_interaction DESC", 
        (user_id,)
    )
    rows = c.fetchall()
    conn.close()
    
    sessions = []
    for row in rows:
        sessions.append({
            "session_id": row["session_id"],
            "user_name": row["user_name"],
            "session_name": row["session_name"] or row["session_id"][:8],
            "last_interaction": row["last_interaction"]
        })
    return sessions

def get_session(session_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve a specific session by session_id."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM chat_sessions WHERE session_id = ?", (session_id,))
    row = c.fetchone()
    conn.close()
    
    if row:
        return {
            "session_id": row["session_id"],
            "user_id": row["user_id"],
            "user_name": row["user_name"],
            "session_name": row["session_name"],
            "chat_history": json.loads(row["chat_history"]) if row["chat_history"] else [],
            "last_interaction": row["last_interaction"],
            "metadata": json.loads(row["metadata"]) if row["metadata"] else {}
        }
    return None

def create_session(user_id: str, user_name: str, session_name: str = None) -> Dict[str, Any]:
    """Create a new session for a user."""
    session_id = str(uuid.uuid4())
    now = datetime.datetime.now()
    initial_history = []
    initial_metadata = {}
    
    # Default name if none provided
    if not session_name:
        session_name = f"Session {now.strftime('%Y-%m-%d %H:%M')}"

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute(
            "INSERT INTO chat_sessions (session_id, user_id, user_name, session_name, chat_history, last_interaction, metadata) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (session_id, user_id, user_name, session_name, json.dumps(initial_history), now, json.dumps(initial_metadata))
        )
        conn.commit()
        logger.info(f"Created new session {session_id} for user {user_id}")
        return {
            "session_id": session_id,
            "user_id": user_id,
            "user_name": user_name,
            "session_name": session_name,
            "chat_history": initial_history,
            "last_interaction": now,
            "metadata": initial_metadata
        }
    except Exception as e:
        logger.error(f"Error creating session: {e}")
        return None
    finally:
        conn.close()

def update_chat_history(session_id: str, history: List[Dict[str, str]]):
    """Update the chat history for a session."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    now = datetime.datetime.now()
    c.execute(
        "UPDATE chat_sessions SET chat_history = ?, last_interaction = ? WHERE session_id = ?",
        (json.dumps(history), now, session_id)
    )
    conn.commit()
    conn.close()

def update_metadata(session_id: str, metadata: Dict[str, Any]):
    """Update metadata for a session."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    now = datetime.datetime.now()
    c.execute(
        "UPDATE chat_sessions SET metadata = ?, last_interaction = ? WHERE session_id = ?",
        (json.dumps(metadata), now, session_id)
    )
    conn.commit()
    conn.close()

"""Persistent conversation history, backed by a local SQLite database.

Uses langchain_community's SQLChatMessageHistory rather than LangGraph's
own checkpointer (create_agent does support one natively via its
`checkpointer` param) — that's the more modern approach for LangGraph
specifically, but it requires the separate langgraph-checkpoint-sqlite
package, which isn't installed or requested. SQLChatMessageHistory reuses
what's already in requirements.txt (langchain-community).
"""
from pathlib import Path

from langchain_community.chat_message_histories import SQLChatMessageHistory

from backend.config import settings

DB_PATH = Path(settings.cache_path) / "conversations.sqlite3"


def _connection_string() -> str:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{DB_PATH}"


def get_session_history(session_id: str) -> SQLChatMessageHistory:
    """Returns the persistent chat history for a session.

    Callers (backend/agents/chain.py) are responsible for supplying a
    session_id — either one the user provided to resume a prior
    conversation, or a freshly generated UUID for a new one.
    """
    return SQLChatMessageHistory(session_id=session_id, connection=_connection_string())

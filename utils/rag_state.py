from typing import Any, Dict, List, Optional

import streamlit as st

from config import MAX_CHAT_SESSIONS_PER_DOCUMENT
from utils.pdf_cache import remove_batch_cache


def _default_session_values() -> Dict[str, Any]:
    """Central place to define all session keys and their defaults."""
    return {
        # One active batch of documents per session
        "batch_id": None,
        "num_files_uploaded": 0,
        # Per-file metadata for the current batch:
        # documents: List[{"name", "size_bytes"}]
        "documents": [],
        "document_ready": False,
        # In-memory vector store for current batch (not persisted)
        "vectorstore": None,
        # Single active chat's messages (mirrors currently selected session)
        "messages": [],
        "chat_started": False,
        # Multi-chat management for a given document
        # chat_sessions: {chat_id: {"name": str, "messages": List[dict]}}
        "chat_sessions": {},
        "current_chat_id": None,
        "error": None,
    }


def init_session_state() -> None:
    """Ensure all expected keys exist in st.session_state with sensible defaults."""
    defaults = _default_session_values()
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def has_document() -> bool:
    """Return True if a document has been successfully set and is ready for chat."""
    return bool(st.session_state.get("document_ready")) and bool(
        st.session_state.get("num_files_uploaded", 0)
    )


def set_uploaded_batch(documents: List[Dict[str, Any]], batch_id: Optional[str] = None) -> None:
    """
    Register the currently uploaded batch in session state.
    """
    st.session_state.batch_id = batch_id
    st.session_state.documents = documents
    st.session_state.num_files_uploaded = len(documents)

    # Reset all chat sessions for a fresh batch
    st.session_state.messages = []
    st.session_state.chat_started = False
    st.session_state.chat_sessions = {}
    st.session_state.current_chat_id = None

    st.session_state.document_ready = True


def reset_all_chats() -> None:
    """Clear all chat sessions for the current batch."""
    remove_batch_cache(st.session_state.get("batch_id"))
    st.session_state.messages = []
    st.session_state.chat_started = False
    st.session_state.chat_sessions = {}
    st.session_state.current_chat_id = None
    st.session_state.error = None


def persist_current_chat_messages() -> None:
    """Store current messages into the active chat session, if any."""
    chat_id = st.session_state.get("current_chat_id")
    chat_sessions: Dict[str, Any] = st.session_state.get("chat_sessions", {})
    if chat_id and chat_id in chat_sessions:
        chat_sessions[chat_id]["messages"] = list(st.session_state.get("messages", []))
        st.session_state.chat_sessions = chat_sessions


def start_new_chat_session(name: Optional[str] = None) -> Optional[str]:
    """
    Create a new chat session for the current document and switch to it.
    Existing sessions are preserved so the user can switch between them.
    """
    # Enforce an upper bound on number of chat sessions per batch
    chat_sessions: Dict[str, Any] = st.session_state.get("chat_sessions", {})
    if len(chat_sessions) >= MAX_CHAT_SESSIONS_PER_DOCUMENT:
        st.session_state.error = (
            f"Maximum of {MAX_CHAT_SESSIONS_PER_DOCUMENT} chat sessions per document reached."
        )
        return None

    # Persist messages of the current session before switching
    persist_current_chat_messages()

    chat_index = len(chat_sessions) + 1
    chat_id = f"chat_{chat_index}"
    chat_name = name or f"Chat {chat_index}"

    chat_sessions[chat_id] = {"name": chat_name, "messages": []}
    st.session_state.chat_sessions = chat_sessions

    st.session_state.current_chat_id = chat_id
    st.session_state.messages = []
    st.session_state.chat_started = False

    return chat_id


def switch_chat_session(chat_id: str) -> None:
    """Switch to an existing chat session."""
    chat_sessions: Dict[str, Any] = st.session_state.get("chat_sessions", {})
    if chat_id not in chat_sessions:
        return

    # Persist current messages before switching
    persist_current_chat_messages()

    st.session_state.current_chat_id = chat_id
    st.session_state.messages = list(chat_sessions[chat_id].get("messages", []))
    st.session_state.chat_started = bool(st.session_state.messages)

def ensure_default_chat_session() -> None:
    """Guarantee that at least one chat session exists for the current batch."""
    chat_sessions: Dict[str, Any] = st.session_state.get("chat_sessions", {})
    if chat_sessions:
       
        current_id = st.session_state.get("current_chat_id")
        if not current_id:
            # Default to first available chat if none is selected yet
            first_id = next(iter(chat_sessions.keys()))
            st.session_state.current_chat_id = first_id
            st.session_state.messages = list(chat_sessions[first_id].get("messages", []))
            st.session_state.chat_started = bool(st.session_state.messages)
        return

    # No sessions yet: create the first one
    start_new_chat_session(name="Chat 1")



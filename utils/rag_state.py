import hashlib
import time
from typing import Any, Dict, List, Optional

import streamlit as st

from config import MAX_CHAT_SESSIONS_PER_DOCUMENT


def _default_session_values() -> Dict[str, Any]:
    """Central place to define all session keys and their defaults."""
    return {
        "document_id": None,
        "document_name": None,
        "document_metadata": {},
        "document": None,  # raw UploadedFile or path; kept for now for compatibility
        "document_ready": False,
        "retriever": None,
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
    return bool(st.session_state.get("document_ready"))


def set_current_document(uploaded_file: Any, num_pages: Optional[int] = None) -> None:
    """
    Register a newly uploaded document in session state.

    This assigns a stable document_id based on file content, stores basic metadata,
    and marks the document as ready. It also resets any prior chat history so the
    new document starts with a clean conversation.
    """
    # Generate a simple hash-based id from the file bytes for reproducibility
    file_bytes = uploaded_file.getvalue()
    document_id = hashlib.md5(file_bytes).hexdigest()

    st.session_state.document_id = document_id
    st.session_state.document_name = getattr(uploaded_file, "name", "uploaded.pdf")
    st.session_state.document = uploaded_file

    metadata: Dict[str, Any] = {
        "num_pages": num_pages,
        "uploaded_at": time.time(),
    }
    st.session_state.document_metadata = metadata

    # Reset all chat sessions and retriever for this new document
    st.session_state.messages = []
    st.session_state.chat_started = False
    st.session_state.chat_sessions = {}
    st.session_state.current_chat_id = None
    st.session_state.retriever = None

    st.session_state.document_ready = True


def reset_all_chats() -> None:
    """Clear all chat sessions for the current document."""
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
    # Enforce an upper bound on number of chat sessions per document
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
    """Guarantee that at least one chat session exists for the current document."""
    chat_sessions: Dict[str, Any] = st.session_state.get("chat_sessions", {})
    if chat_sessions:
        # If we already have a current chat selected, do not overwrite its in-memory
        # messages on rerun. This prevents losing messages that have not yet been
        # explicitly persisted by a session switch.
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



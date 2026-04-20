from typing import Any, Dict, List, Optional

import streamlit as st

from config import MAX_CHAT_SESSIONS_PER_DOCUMENT
from utils.pdf_cache import remove_all_cache


def _default_session_values() -> Dict[str, Any]:
    """Default keys for st.session_state."""
    return {
        "batch_id": None,
        "num_files_uploaded": 0,
        "documents": [],
        "document_ready": False,
        "vectorstore": None,
        "messages": [],
        "chat_started": False,
        "chat_sessions": {},
        "current_chat_id": None,
        "error": None,
        "preview_cache_file": None,
    }


def init_session_state() -> None:
    """Fill missing session_state keys from defaults."""
    defaults = _default_session_values()
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def has_document() -> bool:
    """True when upload batch is marked ready and has files."""
    return bool(st.session_state.get("document_ready")) and bool(
        st.session_state.get("num_files_uploaded", 0)
    )


def set_uploaded_batch(documents: List[Dict[str, Any]], batch_id: Optional[str] = None) -> None:
    """Store a new upload batch and clear chats for that batch."""
    st.session_state.batch_id = batch_id
    st.session_state.documents = documents
    st.session_state.num_files_uploaded = len(documents)
    st.session_state.messages = []
    st.session_state.chat_started = False
    st.session_state.chat_sessions = {}
    st.session_state.current_chat_id = None

    st.session_state.document_ready = True


def reset_all_chats() -> None:
    """Clear chats, errors, and all disk PDF preview cache."""
    remove_all_cache()
    st.session_state.messages = []
    st.session_state.chat_started = False
    st.session_state.chat_sessions = {}
    st.session_state.current_chat_id = None
    st.session_state.error = None


def persist_current_chat_messages() -> None:
    """Copy messages into the active chat_sessions entry."""
    chat_id = st.session_state.get("current_chat_id")
    chat_sessions: Dict[str, Any] = st.session_state.get("chat_sessions", {})
    if chat_id and chat_id in chat_sessions:
        chat_sessions[chat_id]["messages"] = list(st.session_state.get("messages", []))
        st.session_state.chat_sessions = chat_sessions


def start_new_chat_session(name: Optional[str] = None) -> Optional[str]:
    """Add a new tab session and switch to it (respects max session count)."""
    chat_sessions: Dict[str, Any] = st.session_state.get("chat_sessions", {})
    if len(chat_sessions) >= MAX_CHAT_SESSIONS_PER_DOCUMENT:
        st.session_state.error = (
            f"Maximum of {MAX_CHAT_SESSIONS_PER_DOCUMENT} chat sessions per document reached."
        )
        return None

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
    """Load another session's messages into the main message list."""
    chat_sessions: Dict[str, Any] = st.session_state.get("chat_sessions", {})
    if chat_id not in chat_sessions:
        return

    persist_current_chat_messages()

    st.session_state.current_chat_id = chat_id
    st.session_state.messages = list(chat_sessions[chat_id].get("messages", []))
    st.session_state.chat_started = bool(st.session_state.messages)

def ensure_default_chat_session() -> None:
    """Ensure there is at least one chat session and a selected current_chat_id."""
    chat_sessions: Dict[str, Any] = st.session_state.get("chat_sessions", {})
    if chat_sessions:
        current_id = st.session_state.get("current_chat_id")
        if not current_id:
            first_id = next(iter(chat_sessions.keys()))
            st.session_state.current_chat_id = first_id
            st.session_state.messages = list(chat_sessions[first_id].get("messages", []))
            st.session_state.chat_started = bool(st.session_state.messages)
        return

    start_new_chat_session(name="Chat 1")



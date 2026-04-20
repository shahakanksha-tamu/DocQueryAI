import html
import re

import streamlit as st

st.set_page_config(layout="wide", page_title="DocQueryAI - Chat")

from utils.rag_state import (
    has_document,
    init_session_state,
    ensure_default_chat_session,
    start_new_chat_session,
    switch_chat_session,
    persist_current_chat_messages,
)

from rag.qa import answer_question

# Two-step rerun: show user message first, then run the LLM on the next run.
CHAT_PHASE_KEY = "_dq_chat_phase"

_WELCOME_ASSISTANT_MSG = (
    "Hi — I'm your PDF assistant. Ask me anything about the document(s) you uploaded "
    "and I'll answer from its contents and show **Sources** when I use them."
)


def _format_chat_body(text: str) -> str:
    """HTML-escape chat text; newlines and **bold** to safe HTML."""
    if not text:
        return ""
    safe = html.escape(str(text))
    safe = safe.replace("\n", "<br/>")
    safe = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", safe)
    return safe


def _chat_bubble_html(role: str, inner_html: str) -> str:
    """One chat row (user or assistant) as HTML."""
    if role in ("user", "human"):
        return (
            f'<div class="dq-chat-row dq-row-user">'
            f'<div class="dq-bubble dq-bubble-user" dir="auto">{inner_html}</div>'
            f'<div class="dq-avatar dq-avatar-user" aria-hidden="true">'
            f'<span class="material-icons dq-avatar-material">tag_faces</span>'
            f"</div></div>"
        )
    return (
        f'<div class="dq-chat-row dq-row-assistant">'
        f'<div class="dq-avatar dq-avatar-assistant" aria-hidden="true">'
        f'<span class="material-icons dq-avatar-material">smart_toy</span>'
        f"</div>"
        f'<div class="dq-bubble dq-bubble-assistant" dir="auto">{inner_html}</div>'
        f"</div>"
    )


def render_chat_bubble(role: str, content: str) -> None:
    st.markdown(_chat_bubble_html(role, _format_chat_body(content)), unsafe_allow_html=True)


def _render_sources_expander(sources: list) -> None:
    """Show cited pages grouped by document."""
    with st.expander("Sources"):
        pages_by_doc: dict = {}
        for s in sources:
            name = s.get("document_name") or "document"
            doc_id = s.get("document_id")
            page = s.get("page_number")
            if page is None:
                continue
            pages_by_doc.setdefault((name, doc_id), set()).add(page)

        if pages_by_doc:
            for (name, doc_id), pages in pages_by_doc.items():
                sorted_pages = sorted(pages)
                pages_str = ", ".join(str(p) for p in sorted_pages)
                short_id = (doc_id or "")[:8]
                suffix = f" ({short_id})" if short_id else ""
                st.write(f"{name}{suffix}: pages {pages_str}")
        else:
            unique_docs = sorted(
                {
                    (
                        s.get("document_name") or "document",
                        (s.get("document_id") or "")[:8],
                    )
                    for s in sources
                }
            )
            st.write(
                ", ".join([f"{name} ({sid})" if sid else name for name, sid in unique_docs])
            )


init_session_state()

st.markdown(
    """
<link href="https://fonts.googleapis.com/css2?family=Sora:wght@400;600;700&display=swap" rel="stylesheet">
<link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">

<style>
html, body, [data-testid="stAppViewContainer"] {
    font-family: 'Sora', sans-serif;
}

/* Push content below Streamlit top bar */
[data-testid="stMainBlockContainer"] {
    padding-top: calc(3.75rem + env(safe-area-inset-top, 0px)) !important;
    padding-bottom: 6rem !important;
}

[data-testid="stSidebar"] {
    padding-left: 16px;
    padding-right: 16px;
    border-right: 1px solid rgba(148, 163, 184, 0.18);
}

.brand {
    display: flex;
    align-items: center;
    gap: 10px;
    font-weight: 700;
    font-size: 1.5rem;
    margin-bottom: 30px;
    font-family: 'Sora', sans-serif;
    color: #7c3aed;
}

.brand-icon {
    font-size: 26px;
    color: #7c3aed;
}

.dq-chat-header {
    background: transparent;
    padding: 8px 0 12px 0;
    margin-top: 4px;
    margin-bottom: 1.25rem;
}
.dq-chat-title {
    font-size: 2rem;
    font-weight: 700;
    line-height: 1.1;
    color: #e5e7eb;
}
.dq-chat-subtitle {
    margin-top: 6px;
    color: #94a3b8;
}

/* Chat bubbles: assistant left, user right */
.dq-chat-row {
    display: flex;
    width: 100%;
    margin-bottom: 0.65rem;
}
.dq-row-assistant {
    justify-content: flex-start;
    align-items: flex-end;
    gap: 0.45rem;
}
.dq-row-user {
    justify-content: flex-end;
    align-items: flex-end;
    gap: 0.45rem;
}
/* Square avatars */
.dq-avatar {
    width: 2.5rem;
    height: 2.5rem;
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    margin-bottom: 2px;
}
.dq-avatar-assistant {
    background: #ea580c;
    border: none;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
}
.dq-avatar-user {
    background: #dc2626;
    border: none;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
}
.dq-avatar .dq-avatar-material {
    font-size: 1.35rem !important;
    line-height: 1 !important;
}
.dq-avatar-assistant .dq-avatar-material,
.dq-avatar-user .dq-avatar-material {
    color: #ffffff !important;
}
.dq-bubble {
    max-width: min(88%, 34rem);
    padding: 0.55rem 0.85rem 0.65rem;
    border-radius: 1rem;
    line-height: 1.45;
    font-size: 0.95rem;
    word-wrap: break-word;
}
.dq-bubble-assistant {
    background: rgba(148, 163, 184, 0.16);
    border: 1px solid rgba(148, 163, 184, 0.22);
    border-bottom-left-radius: 0.25rem;
    color: #e5e7eb;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.12);
}
.dq-bubble-user {
    background: rgba(148, 163, 184, 0.16);
    border: 1px solid rgba(148, 163, 184, 0.22);
    border-bottom-right-radius: 0.25rem;
    color: #e5e7eb;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.12);
}
.dq-bubble-user strong,
.dq-bubble-assistant strong {
    font-weight: 600;
}
.dq-doc-hint {
    margin-top: 0.2rem;
    margin-bottom: 0.5rem;
    color: #94a3b8;
    font-size: 0.78rem;
    line-height: 1.2;
}
.dq-doc-row {
    display: flex;
    align-items: center;
    gap: 0.3rem;
    margin: 0.2rem 0 0.42rem;
    color: #94a3b8;
    font-size: 0.8rem;
    line-height: 1.25;
}
.dq-doc-icon {
    font-size: 0.85rem !important;
    opacity: 0.85;
}
.dq-doc-link {
    color: #94a3b8;
    text-decoration: underline;
    text-underline-offset: 0.1rem;
}
.dq-doc-size {
    opacity: 0.9;
}
</style>
""",
    unsafe_allow_html=True,
)

if not has_document():
    st.warning("Please upload a PDF document before starting a chat.")
    if st.button("Go to Upload Page"):
        st.switch_page("pages/upload.py")
    st.stop()

ensure_default_chat_session()

with st.sidebar:
    st.markdown(
        """
    <div class="brand">
        <span class="material-icons brand-icon">psychology</span>
        DocQueryAI
    </div>
    """,
        unsafe_allow_html=True,
    )

    nav_col_home, nav_col_upload, nav_col_new_chat = st.columns([1, 1, 1])
    with nav_col_home:
        if st.button("Home", key="nav_home"):
            st.switch_page("app.py")
    with nav_col_upload:
        if st.button("Upload", key="nav_upload"):
            st.switch_page("pages/upload.py")
    with nav_col_new_chat:
        if st.button("New Chat", key="nav_new_chat"):
            new_id = start_new_chat_session()
            if new_id is not None:
                st.rerun()

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    st.subheader("Uploaded Documents")
    documents = st.session_state.get("documents", [])
    if documents:
        label = (
            documents[0].get("name", "document")
            if len(documents) == 1
            else f"{len(documents)} documents"
        )
        st.markdown(f"`{label}`")
        st.markdown(
            '<div class="dq-doc-hint">Use Preview to view the PDF</div>',
            unsafe_allow_html=True,
        )
        batch_id = st.session_state.get("batch_id")
        for i, doc in enumerate(documents):
            name = doc.get("name", "unknown")
            size_bytes = doc.get("size_bytes")
            cache_file = doc.get("cache_file")
            size_mb = (
                size_bytes / (1024 * 1024) if isinstance(size_bytes, int) else None
            )
            if cache_file and batch_id:
                label = name if len(name) <= 44 else name[:41] + "…"
                if st.button(
                    f"Preview: {label}",
                    key=f"sidebar_doc_preview_{i}",
                    use_container_width=True,
                ):
                    st.session_state["preview_cache_file"] = cache_file
                    st.switch_page("pages/preview.py")
                if size_mb is not None:
                    st.caption(f"{size_mb:.2f} MB")
            elif size_mb is not None:
                st.caption(f"{name} • {size_mb:.2f} MB")
            else:
                st.caption(name)
    else:
        st.markdown("No documents in session.")

    st.markdown("<hr style='margin: 16px 0;'/>", unsafe_allow_html=True)
    st.subheader("Chat Sessions")
    st.caption("Use sessions to keep separate conversations for the same uploaded document(s).")

    chat_sessions = list(st.session_state.get("chat_sessions", {}).items())
    current_chat_id = st.session_state.get("current_chat_id")

    if st.session_state.get("error"):
        st.warning(st.session_state.error)
        st.session_state.error = None

    for idx, (chat_id, info) in enumerate(chat_sessions):
        if idx % 3 == 0:
            cols = st.columns(3)
        col = cols[idx % 3]
        label = info.get("name", chat_id)
        is_current = chat_id == current_chat_id
        with col:
            if st.button(
                label,
                key=f"chat_select_{chat_id}",
                type="primary" if is_current else "secondary",
            ):
                if not is_current:
                    switch_chat_session(chat_id)
                    st.rerun()

    st.markdown("---")


docs_count = st.session_state.get("num_files_uploaded", 0)
st.markdown(
    f"""
<div class="dq-chat-header">
  <div class="dq-chat-title">PDF Chat</div>
  <div class="dq-chat-subtitle">Chatting with: <b>{docs_count} document(s)</b></div>
</div>
""",
    unsafe_allow_html=True,
)

if st.session_state.get("vectorstore") is None:
    st.info("Index not loaded in memory yet. Please re-upload documents to build the index.")

if not st.session_state.messages and not st.session_state.chat_started:
    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": _WELCOME_ASSISTANT_MSG,
        }
    )
    st.session_state.chat_started = True


for msg in st.session_state.messages:
    role = msg.get("role", "assistant")
    content = msg.get("content", "")
    if role == "user":
        render_chat_bubble("user", content)
    else:
        _a1, _a2 = st.columns([3, 1])
        with _a1:
            render_chat_bubble("assistant", content)
            if msg.get("sources"):
                _render_sources_expander(msg["sources"])


_phase = st.session_state.get(CHAT_PHASE_KEY)
if _phase == "paint_user":
    st.session_state[CHAT_PHASE_KEY] = "generate"
    st.rerun()
elif _phase == "generate":
    st.session_state[CHAT_PHASE_KEY] = None
    msgs = st.session_state.messages
    if msgs and msgs[-1].get("role") == "user":
        prompt = (msgs[-1].get("content") or "").strip()
        if prompt:
            with st.spinner("Generating answer..."):
                if st.session_state.get("vectorstore") is None:
                    answer = "Index not loaded. Please upload documents again."
                    sources = []
                else:
                    try:
                        answer, sources = answer_question(
                            vectorstore=st.session_state.vectorstore,
                            question=prompt,
                        )
                    except Exception as e:
                        answer = f"Error during retrieval/QA: {e}"
                        sources = []

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": answer,
                    "sources": sources if sources else None,
                }
            )
            persist_current_chat_messages()
            st.rerun()


if prompt := st.chat_input("Ask a question about the document"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.session_state[CHAT_PHASE_KEY] = "paint_user"
    persist_current_chat_messages()
    st.rerun()

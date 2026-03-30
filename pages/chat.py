import streamlit as st

from utils.rag_state import (
    has_document,
    init_session_state,
    ensure_default_chat_session,
    start_new_chat_session,
    switch_chat_session,
    persist_current_chat_messages,
)

from rag.qa import answer_question


st.set_page_config(layout="wide", page_title="DocQueryAI - Chat")

# Ensure expected session keys are present
init_session_state()

# Shared fonts and basic styling so sidebar branding matches upload page
st.markdown(
    """
<link href="https://fonts.googleapis.com/css2?family=Sora:wght@400;600;700&display=swap" rel="stylesheet">
<link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">

<style>
html, body, [data-testid="stAppViewContainer"] {
    font-family: 'Sora', sans-serif;
}

[data-testid="stMainBlockContainer"]{
    padding-top: 20px !important;
    padding-bottom: 10px !important;
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
    color: var(--primary-color);
}

.brand-icon {
    font-size: 26px;
    color: var(--primary-color);
}

/* Sticky chat header (keeps "PDF Chat" visible while scrolling). */
.dq-chat-header {
    background: var(--background-color);
    padding: 10px 0 8px 0;
    margin-top: 10px;
}
.dq-chat-title {
    font-size: 2rem;
    font-weight: 700;
    line-height: 1.1;
}
.dq-chat-subtitle {
    margin-top: 6px;
    opacity: 0.85;
}

</style>
""",
    unsafe_allow_html=True,
)

# Route protection: do not allow access to chat without a document
if not has_document():
    st.warning("Please upload a PDF document before starting a chat.")
    if st.button("Go to Upload Page"):
        st.switch_page("pages/upload.py")
    st.stop()

# Ensure we have at least one chat session for this document
ensure_default_chat_session()


with st.sidebar:
    # Branding (consistent with upload page)
    st.markdown(
        """
    <div class="brand">
        <span class="material-icons brand-icon">psychology</span>
        DocQueryAI
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Simple navigation row (kept compact)
    nav_col_home, nav_col_upload, nav_col_new_chat = st.columns([1, 1, 1])
    with nav_col_home:
        if st.button("Home", key="nav_home"):
            st.switch_page("app.py")
    with nav_col_upload:
        if st.button("Upload", key="nav_upload"):
            st.switch_page("pages/upload.py")
    with nav_col_new_chat:
        if st.button("+ New Chat", key="nav_new_chat"):
            new_id = start_new_chat_session()
            if new_id is not None:
                st.rerun()

    # Small vertical gap between navbar and sections
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
        for doc in documents:
            name = doc.get("name", "unknown")
            size_bytes = doc.get("size_bytes")
            if isinstance(size_bytes, int):
                size_mb = size_bytes / (1024 * 1024)
                st.caption(f"{name} • {size_mb:.2f} MB")
            else:
                st.caption(name)
    else:
        st.markdown("No documents in session.")

    st.markdown("<hr style='margin: 16px 0;'/>", unsafe_allow_html=True)
    st.subheader("Chat Sessions")

    chat_sessions = list(st.session_state.get("chat_sessions", {}).items())
    current_chat_id = st.session_state.get("current_chat_id")

    # Show any error from session management (e.g., max sessions reached)
    if st.session_state.get("error"):
        st.warning(st.session_state.error)
        st.session_state.error = None

    # Render chat sessions in rows of 3 using Streamlit columns
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

# Initialize a welcome message once per chat session
if not st.session_state.messages and not st.session_state.chat_started:
    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": "Ask me questions about your uploaded PDF.",
        }
    )
    st.session_state.chat_started = True


# Render existing messages for the current chat session
for msg in st.session_state.messages:
    role = msg.get("role", "assistant")
    content = msg.get("content", "")
    with st.chat_message(role):
        st.markdown(content)


# Handle new user input for the current chat session
if prompt := st.chat_input("Ask a question about the document"):

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        placeholder.markdown("Generating answer...")

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

        placeholder.markdown(answer)
        if sources:
            with st.expander("Sources"):
                # Group pages by document so we don't repeat the same doc/page pairs
                pages_by_doc = {}
                for s in sources:
                    name = s.get("document_name") or "document"
                    doc_id = s.get("document_id")
                    page = s.get("page_number")
                    if page is None:
                        continue
                    # Key by both name and id so sources can't "mix" when filenames repeat.
                    pages_by_doc.setdefault((name, doc_id), set()).add(page)

                if pages_by_doc:
                    for (name, doc_id), pages in pages_by_doc.items():
                        sorted_pages = sorted(pages)
                        pages_str = ", ".join(str(p) for p in sorted_pages)
                        short_id = (doc_id or "")[:8]
                        suffix = f" ({short_id})" if short_id else ""
                        st.write(f"{name}{suffix}: pages {pages_str}")
                else:
                    # Fallback: if page metadata is missing
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
                        ", ".join(
                            [f"{name} ({sid})" if sid else name for name, sid in unique_docs]
                        )
                    )

    st.session_state.messages.append({"role": "assistant", "content": answer})

    # Persist updated messages into the active chat session so they survive
    # session switches and reruns.
    persist_current_chat_messages()


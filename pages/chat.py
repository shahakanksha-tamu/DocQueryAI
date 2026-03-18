import streamlit as st

from utils.rag_state import (
    has_document,
    init_session_state,
    ensure_default_chat_session,
    start_new_chat_session,
    switch_chat_session,
    persist_current_chat_messages,
)


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
    background-color: #020617 !important;
    color: #e5e7eb !important;
    font-family: 'Sora', sans-serif;
}

[data-testid="stMainBlockContainer"]{
    padding-top: 20px !important;
    padding-bottom: 10px !important;
}

[data-testid="stSidebar"] {
    padding-left: 16px;
    padding-right: 16px;
    background-color: #0f172a !important;  /* slightly lighter than main background */
    border-right: 1px solid #1e293b;
    min-width: 300px !important;
}

.brand {
    display: flex;
    align-items: center;
    gap: 10px;
    font-weight: 700;
    font-size: 1.5rem;
    margin-bottom: 30px;
    font-family: 'Sora', sans-serif;
}

.brand-icon {
    font-size: 26px;
    color: #7C3AED;
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
    nav_col_home, nav_col_upload, _ = st.columns([1, 1, 1])
    with nav_col_home:
        if st.button("Home", key="nav_home"):
            st.switch_page("app.py")
    with nav_col_upload:
        if st.button("Upload", key="nav_upload"):
            st.switch_page("pages/upload.py")

    # Small vertical gap between navbar and sections
    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    st.subheader("Uploaded Documents")
    st.markdown(f"`{st.session_state.document_name}`")

    # List all documents in this active batch, if available
    documents = st.session_state.get("documents", [])
    if documents:
        for doc in documents:
            st.markdown(f"- `{doc.get('name', 'unknown')}`")

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
    if st.button("+ New Chat", key="sidebar_new_chat"):
        new_id = start_new_chat_session()
        if new_id is not None:
            st.rerun()


st.title("PDF Chat")
st.caption(f"Chatting with: **{st.session_state.document_name}**")

# Initialize a welcome message once per chat session
if not st.session_state.messages and not st.session_state.chat_started:
    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": "Ask me questions about your uploaded PDF. (RAG answers coming soon.)",
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
    # Show user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Placeholder assistant response (RAG/LLM integration will replace this)
    placeholder_answer = (
        "Thanks for your question! The retrieval and LLM backend "
        "are not wired up yet, but this chat flow and session handling "
        "form the foundation for the full DocQueryAI experience."
    )
    st.session_state.messages.append(
        {"role": "assistant", "content": placeholder_answer}
    )
    with st.chat_message("assistant"):
        st.markdown(placeholder_answer)

    # Persist updated messages into the active chat session so they survive
    # session switches and reruns.
    persist_current_chat_messages()

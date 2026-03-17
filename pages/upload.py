import streamlit as st
import time

from utils.rag_state import (
    init_session_state,
    reset_all_chats,
    set_current_document,
    has_document,
)
from utils.spinner import show_loading_overlay

st.set_page_config(layout="wide", page_title="DocQueryAI - Upload")

# Initialize a consistent session schema
init_session_state()

st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Sora:wght@400;600;700&display=swap" rel="stylesheet">
<link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">

<style>
html, body, [data-testid="stAppViewContainer"] {
    background-color: #020617 !important;
    color: #e5e7eb !important;
    font-family: 'Sora', sans-serif;
}

[data-testid="stMainBlockContainer"] {
    padding-top: 0 !important;
    padding-bottom: 0 !important;
}

[data-testid="stSidebar"] {
    padding: 16px;
    background-color: #0f172a !important;  /* slightly lighter than main background */
    border-right: 1px solid #1e293b;
}


.brand {
    display: flex;
    align-items: center;
    gap: 10px;
    font-weight: 700;
    font-size: 1.5rem;
    margin-bottom: 30px;
}

.brand-icon {
    font-size: 26px;
    color: #2563eb;
}


.sidebar-btn {
    background: #2563eb;
    color: white;
    border-radius: 8px;
    padding: 10px 14px;
    text-align: center;
    font-weight: 600;
    margin-bottom: 20px;
}


.main-container {
    max-width: 800px;
    margin-top: 4rem;
    margin-left: auto;
    margin-right: auto;
    text-align: center;
}


.upload-icon-wrapper {
    width: 100px;
    height: 100px;
    background: rgba(148, 163, 184, 0.15);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 0 auto 20px auto;
    animation: bounce 2s infinite ease-in-out;
}

.upload-icon {
    font-size: 64px;
    color: #22c55e;
}

@keyframes bounce {
    0%, 100% { transform: translateY(0px); }
    50% { transform: translateY(-10px); }
}

[data-testid="stFileUploader"] {
    width: 80%;
    margin: auto;
    border: 2px dashed #334155;
    border-radius: 14px;
    text-align: center;
    transition: all 0.2s ease;
    cursor: pointer;
}

[data-testid="stFileUploader"] section {
    height: 250px;
    text-align: center; 
}

[data-testid="stFileUploaderDropzoneInstructions"]{
    display: flex;
    flex-direction: column;
}

[data-testid="stFileUploader"]:hover {
    border-color: #7C3AED;
    background: #020617;
}

[data-testid="stFileUploader"] button {
    display: none;

}

.upload-wrapper {
    position: relative;
    max-width: 600px;
}

</style>
""", unsafe_allow_html=True)

# Sidebar
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

    if st.button("Home"):
        st.switch_page("app.py")

    if st.button("Go to Chat"):
        if has_document():
            st.switch_page("pages/chat.py")
        else:
            # Set a flag so the warning is rendered in the main content area
            st.session_state["upload_chat_warning"] = (
                "Upload a PDF first to start chatting."
            )

# Main Content
st.markdown(
    """
<div class="main-container">
    <div class="upload-icon-wrapper">
        <span class="material-icons upload-icon">description</span>
    </div>
    <div style="font-size:2rem;font-weight:700;margin-bottom:10px;">
        PDF Chat
    </div>
    <div style="color:#6b7280;margin-bottom:40px;">
        Upload PDF documents to analyze content, get summaries,
        and ask specific questions.
    </div>
</div>
""",
    unsafe_allow_html=True,
)

# Show any warning about missing document when trying to go to chat
warning_msg = st.session_state.get("upload_chat_warning")
if warning_msg:
    st.warning(warning_msg)
    # Clear it after displaying once
    st.session_state["upload_chat_warning"] = None


if st.session_state.document_ready:
    st.info(f"You are currently working with: **{st.session_state.document_name}**")

    if st.button("Continue Chat"):
        st.switch_page("pages/chat.py")

    if st.button("Upload New Document"):
        # Clear all chats and the current document, then restart flow
        reset_all_chats()
        for key in [
            "document_id",
            "document_name",
            "document_metadata",
            "document",
            "retriever",
            "document_ready",
        ]:
            st.session_state.pop(key, None)
        st.rerun()
else:
    # Upload Section
    st.markdown('<div class="upload-wrapper">', unsafe_allow_html=True)

    uploaded_file = st.file_uploader(
        "",
        type=["pdf"],
        label_visibility="collapsed",
    )

    st.markdown("</div>", unsafe_allow_html=True)

    if uploaded_file and not has_document():
        st.success(f"File '{uploaded_file.name}' uploaded successfully!")
        time.sleep(1)
        show_loading_overlay("Processing your document")

        # Simulate ingestion
        time.sleep(3)

        # Here you will:
        # 1. Extract text
        # 2. Chunk
        # 3. Embed
        # 4. Store vector DB

        # For now, just register the document in session state
        set_current_document(uploaded_file=uploaded_file, num_pages=None)

        # Redirect to chat page
        st.switch_page("pages/chat.py")

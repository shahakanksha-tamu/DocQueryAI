import os

import sys
from pathlib import Path
import streamlit as st
import time
import uuid

from utils.rag_state import (
    init_session_state,
    reset_all_chats,
    has_document,
    set_uploaded_batch,
)
from utils.spinner import show_loading_overlay
from rag.rag_pipeline import rag_processing

st.set_page_config(layout="wide", page_title="DocQueryAI - Upload")

init_session_state()

if "upload_widget_key" not in st.session_state:
    st.session_state["upload_widget_key"] = str(uuid.uuid4())

st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Sora:wght@400;600;700&display=swap" rel="stylesheet">
<link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">

<style>
html, body, [data-testid="stAppViewContainer"] {
    font-family: 'Sora', sans-serif;
}

[data-testid="stMainBlockContainer"] {
    padding-top: 0 !important;
    padding-bottom: 0 !important;
}

[data-testid="stSidebar"] {
    display: none;
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
    border: 2px dashed rgba(148, 163, 184, 0.35);
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
    border-color: var(--primary-color);
    background: var(--background-color);
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

# Main Content
_, top_right = st.columns([12, 2])
with top_right:
    st.markdown(
        '<div style="height: 2.25rem;" aria-hidden="true"></div>',
        unsafe_allow_html=True,
    )
    if st.button("Home", key="upload_top_home"):
        st.switch_page("app.py")

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

if has_document():
    names = [d.get("name", "unknown") for d in st.session_state.get("documents", [])]
    label = names[0] if len(names) == 1 else f"{len(names)} documents"
    st.info(f"You are currently working with: **{label}**")

    _pad_l, col_continue, col_new, _pad_r = st.columns([2, 2, 2, 2])
    with col_continue:
        if st.button("Continue Chat", use_container_width=True, key="upload_continue_chat"):
            st.switch_page("pages/chat.py")
    with col_new:
        if st.button(
            "Upload New Document(s)",
            use_container_width=True,
            key="upload_new_documents",
        ):
            reset_all_chats()

            st.session_state["upload_widget_key"] = str(uuid.uuid4())

            for key in [
                "batch_id",
                "num_files_uploaded",
                "documents",
                "vectorstore",
                "document_ready",
            ]:
                st.session_state.pop(key, None)
            st.rerun()
else:
    # Upload Section
    st.markdown('<div class="upload-wrapper">', unsafe_allow_html=True)

    uploaded_files = st.file_uploader(
        "Upload PDF document(s)",
        type=["pdf"],
        label_visibility="collapsed",
        accept_multiple_files=True,
        key=f"uploader_{st.session_state.get('upload_widget_key')}",
    )

    st.markdown("</div>", unsafe_allow_html=True)

    if uploaded_files and not has_document():
        st.success(f"{len(uploaded_files)} file(s) uploaded successfully!")
        time.sleep(1)
        show_loading_overlay("Processing your documents")

        # lightweight UI metadata (no content stored)
        documents_meta = []
        for f in uploaded_files:
            file_bytes = f.getvalue()
            documents_meta.append({"name": f.name, "size_bytes": len(file_bytes)})

        batch_id = str(uuid.uuid4())

        # PDFs -> pages -> chunks -> in-memory Chroma vectorstore
        _, _, vectorstore = rag_processing(uploaded_files=uploaded_files, batch_id=batch_id)
        st.session_state.vectorstore = vectorstore

        # Mark batch as ready for chat (store only lightweight metadata)
        set_uploaded_batch(documents=documents_meta, batch_id=batch_id)

        # Redirect to chat page
        st.switch_page("pages/chat.py")

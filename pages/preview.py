import streamlit as st
from streamlit.errors import StreamlitAPIException

from utils.pdf_cache import cache_root, is_valid_cache_filename


def _get_query_param(name: str) -> str | None:
    """Read one query param (st.query_params or legacy API)."""
    try:
        params = st.query_params  # type: ignore[attr-defined]
        val = params.get(name)
        if isinstance(val, list):
            return val[0] if val else None
        return val
    except Exception:
        qp = st.experimental_get_query_params()
        val = qp.get(name)
        if isinstance(val, list):
            return val[0] if val else None
        return val


def _resolve_doc_id() -> tuple[str | None, str | None]:
    """batch_id + cache filename from session, else from URL (legacy links)."""
    batch_id = st.session_state.get("batch_id")
    doc_id = st.session_state.get("preview_cache_file")

    if batch_id and doc_id and is_valid_cache_filename(str(doc_id)):
        return str(batch_id), str(doc_id)

    q_batch = _get_query_param("batch_id")
    q_doc = _get_query_param("doc_id")
    if q_batch and q_doc and is_valid_cache_filename(str(q_doc)):
        return str(q_batch), str(q_doc)

    return None, None


st.set_page_config(layout="wide", page_title="PDF Preview")

st.markdown(
    """
<style>
html, body { margin: 0; padding: 0; }
/* Clear Streamlit header overlap */
[data-testid="stMainBlockContainer"] {
    padding-top: calc(3.75rem + env(safe-area-inset-top, 0px)) !important;
    padding-bottom: 1.5rem !important;
}
</style>
""",
    unsafe_allow_html=True,
)

nav_col_back, _ = st.columns([1, 3])
with nav_col_back:
    if st.button("← Back to chat", use_container_width=True, key="preview_back_chat"):
        st.switch_page("pages/chat.py")

batch_id, doc_id = _resolve_doc_id()

if not batch_id or not doc_id:
    st.info("No document selected for preview. Open a document from the chat sidebar.")
    st.stop()

pdf_path = cache_root() / str(batch_id) / str(doc_id)
if not pdf_path.is_file():
    st.error("Preview not found. Please return to chat and open the document again.")
    st.stop()

if pdf_path.stat().st_size == 0:
    st.error("Cached preview file is empty.")
    st.stop()

try:
    st.pdf(str(pdf_path), height=900)
except StreamlitAPIException as e:
    st.warning(str(e))
    pdf_bytes = pdf_path.read_bytes()
    st.download_button(
        label="Download PDF",
        data=pdf_bytes,
        file_name=pdf_path.name,
        mime="application/pdf",
        use_container_width=True,
    )
    st.caption(
        'Install the PDF extra: pip install "streamlit[pdf]" '
        "and redeploy. You can open the file locally with the button above."
    )

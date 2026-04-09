import streamlit as st
from streamlit.errors import StreamlitAPIException

from utils.pdf_cache import cache_root


def _get_query_param(name: str) -> str | None:
    # Streamlit supports both `st.query_params` and legacy `experimental_get_query_params`.
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


st.set_page_config(layout="wide", page_title="PDF Preview")

st.markdown(
    """
<style>
html, body { margin: 0; padding: 0; }
[data-testid="stMainBlockContainer"] { padding-top: 0 !important; }
</style>
""",
    unsafe_allow_html=True,
)

batch_id = _get_query_param("batch_id")
doc_id = _get_query_param("doc_id")

if not batch_id or not doc_id:
    st.info("Missing preview parameters.")
elif not (pdf_path := (cache_root() / str(batch_id) / str(doc_id))):
    st.error("Invalid preview path.")
elif not pdf_path.is_file():
    st.error("Preview not found. Please re-upload your PDF.")
else:
    pdf_bytes = pdf_path.read_bytes()
    if not pdf_bytes:
        st.error("Cached preview file is empty.")
    else:
        # Primary renderer: Streamlit PDF element.
        try:
            st.pdf(pdf_bytes, height=900)
        except StreamlitAPIException:
            # Deployed environments can block iframe/data: URL fallbacks via browser CSP.
            st.warning("Inline preview is unavailable in this browser/deployment.")
            st.download_button(
                label="Download PDF",
                data=pdf_bytes,
                file_name=pdf_path.name,
                mime="application/pdf",
                use_container_width=True,
            )
            st.caption("Download the file to open it locally.")


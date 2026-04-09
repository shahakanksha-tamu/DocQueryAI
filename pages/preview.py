import base64

import streamlit as st
import streamlit.components.v1 as components
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
        # Primary renderer: Streamlit PDF element (more reliable than data: URLs for large files).
        try:
            st.pdf(pdf_bytes, height=900)
        except StreamlitAPIException:
            # Fallback for environments missing streamlit-pdf support.
            b64 = base64.b64encode(pdf_bytes).decode("ascii")
            iframe_html = f"""
<iframe
  title="PDF preview"
  src="data:application/pdf;base64,{b64}"
  style="width: 100%; height: 90vh; border: 0; background: #0f172a;"
>
</iframe>
"""
            components.html(iframe_html, height=950, scrolling=True)
            st.caption(
                "Using fallback preview renderer. If blank, install streamlit PDF support:"
                " pip install streamlit[pdf]"
            )


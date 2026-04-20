import os
import streamlit as st


def get_huggingface_api_token() -> str:
    """HF token from env or Streamlit secrets; empty string if missing."""
    token = os.environ.get("HUGGINGFACE_API_TOKEN", "").strip()
    if token:
        return token
    try:

        if hasattr(st, "secrets") and "HUGGINGFACE_API_TOKEN" in st.secrets:
            return str(st.secrets["HUGGINGFACE_API_TOKEN"]).strip()
    except Exception:
        pass
    return ""

def require_huggingface_api_token() -> str:
    """Same as get_huggingface_api_token but raises if unset."""
    token = get_huggingface_api_token()
    if not token:
        raise ValueError(
            "Hugging Face chat requires HUGGINGFACE_API_TOKEN in the environment "
            "or in .streamlit/secrets.toml (see Streamlit secrets docs)."
        )
    return token

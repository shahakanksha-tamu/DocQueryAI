from typing import List, Optional

from langchain_core.documents import Document
from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores import Chroma

from config import OLLAMA_BASE_URL, OLLAMA_EMBED_MODEL
import streamlit as st

@st.cache_resource
def get_embeddings() -> OllamaEmbeddings:
    """Return an OllamaEmbeddings instance configured from config.py."""
    return OllamaEmbeddings(model=OLLAMA_EMBED_MODEL, base_url=OLLAMA_BASE_URL)


def build_chroma_index(chunks: List[Document], collection_name: Optional[str] = None) -> Chroma:
    """
    Build an in-memory Chroma vector store from chunk Documents.

    This step computes embeddings (via Ollama) and stores them with associated
    metadata in an in-memory Chroma store for the current Streamlit session.
    """
    embeddings = get_embeddings()
    kwargs = {
        "documents": chunks,
        "embedding": embeddings,
    }
    if collection_name:
        kwargs["collection_name"] = collection_name

    return Chroma.from_documents(
        **kwargs,
    )


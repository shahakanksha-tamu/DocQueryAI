import os
from typing import List, Optional

import streamlit as st
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

from config import HF_EMBEDDING_DEVICE, HF_EMBEDDING_MODEL
from utils.hf_token import get_huggingface_api_token


@st.cache_resource
def get_embeddings() -> Embeddings:
    """Singleton sentence-transformers embedder (optional HF token)."""
    token = get_huggingface_api_token()
    model_kwargs: dict = {"device": HF_EMBEDDING_DEVICE}
    if token:
        model_kwargs["token"] = token
    
    return HuggingFaceEmbeddings(
        model_name=HF_EMBEDDING_MODEL,
        model_kwargs=model_kwargs,
        encode_kwargs={"normalize_embeddings": True},
    )


def build_chroma_index(chunks: List[Document], collection_name: Optional[str] = None) -> Chroma:
    """Build in-memory Chroma from chunked documents."""
    embeddings = get_embeddings()
    kwargs: dict = {"documents": chunks, "embedding": embeddings}
    if collection_name:
        kwargs["collection_name"] = collection_name
    return Chroma.from_documents(**kwargs)

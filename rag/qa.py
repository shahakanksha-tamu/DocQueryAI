from __future__ import annotations

from typing import Any, Dict, List, Tuple

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.vectorstores import VectorStore
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint

from config import (
    HF_CHAT_MAX_NEW_TOKENS,
    HF_CHAT_MODEL,
    HF_CHAT_PROVIDER,
    HF_CHAT_TEMPERATURE,
    TOP_K_RETRIEVAL,
)
from utils.hf_token import require_huggingface_api_token


def _format_sources(docs: List[Any]) -> List[Dict[str, Any]]:
    """Extract source metadata from retrieved chunk Documents."""
    sources: List[Dict[str, Any]] = []
    for d in docs:
        meta = dict(getattr(d, "metadata", {}) or {})
        sources.append(
            {
                "document_name": meta.get("document_name"),
                "document_id": meta.get("document_id"),
                "page_number": meta.get("page_number"),
            }
        )
    return sources


def _build_context(docs: List[Any]) -> str:
    """Create a single context string for the LLM from retrieved chunks."""
    parts: List[str] = []
    for d in docs:
        meta = dict(getattr(d, "metadata", {}) or {})
        doc_name = meta.get("document_name") or meta.get("document_id") or "document"
        page = meta.get("page_number")

        header = f"[{doc_name}]"
        if page is not None:
            header += f" (page {page})"

        parts.append(f"{header}\n{d.page_content}")

    return "\n\n---\n\n".join(parts)


def _make_chat_model() -> ChatHuggingFace:

    token = require_huggingface_api_token()
    endpoint_kwargs: Dict[str, Any] = {
        "repo_id": HF_CHAT_MODEL,
        "huggingfacehub_api_token": token,
        "return_full_text": False,
        # "max_new_tokens": HF_CHAT_MAX_NEW_TOKENS,
        "do_sample": HF_CHAT_TEMPERATURE > 0,
        "temperature": HF_CHAT_TEMPERATURE,
    }

    if HF_CHAT_PROVIDER:
        endpoint_kwargs["provider"] = HF_CHAT_PROVIDER

    endpoint = HuggingFaceEndpoint(**endpoint_kwargs)
    return ChatHuggingFace(
        llm=endpoint,
        temperature=HF_CHAT_TEMPERATURE,
        max_tokens=HF_CHAT_MAX_NEW_TOKENS,
    )


def answer_question(
    vectorstore: VectorStore,
    question: str,
    top_k: int = TOP_K_RETRIEVAL,
) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Retrieve top-k chunks and answer

    Returns:
      (answer_text, sources_metadata)
    """
    retriever = vectorstore.as_retriever(search_kwargs={"k": top_k})

    try:
        docs = retriever.get_relevant_documents(question)
    except Exception:
        docs = retriever.invoke(question)

    if isinstance(docs, dict) and "documents" in docs:
        docs = docs["documents"]

    context = _build_context(docs)
    sources = _format_sources(docs)

    system = (
        "You are DocQueryAI, a PDF question answering assistant. "
        "Answer the user's question using ONLY the provided CONTEXT. "
        "If the answer cannot be found in the context, say: "
        "\"I don't know based on the uploaded documents.\" "
        "Keep the answer concise and grounded."
    )

    user_block = (
        f"CONTEXT:\n{context}\n\n"
        f"QUESTION:\n{question}\n\n"
        "Answer using only the context above."
    )

    chat = _make_chat_model()
    ai_msg = chat.invoke(
        [
            SystemMessage(content=system),
            HumanMessage(content=user_block),
        ]
    )
    answer = (getattr(ai_msg, "content", None) or str(ai_msg)).strip()

    return answer, sources

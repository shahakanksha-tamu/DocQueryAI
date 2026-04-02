from __future__ import annotations

from typing import Any, Dict, List, Tuple

from langchain_ollama import ChatOllama
from langchain_core.vectorstores import VectorStore

from config import (
    OLLAMA_BASE_URL,
    OLLAMA_CHAT_MODEL,
    TOP_K_RETRIEVAL,
    OLLAMA_TEMPERATURE,
)


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


def answer_question(
    vectorstore: VectorStore,
    question: str,
    top_k: int = TOP_K_RETRIEVAL,
) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Retrieve top-k chunks from `vectorstore` and answer using local Ollama LLM.

    Returns:
      (answer_text, sources_metadata)
    """
    retriever = vectorstore.as_retriever(search_kwargs={"k": top_k})

    try:
        docs = retriever.get_relevant_documents(question)  # type: ignore[attr-defined]
    except Exception:
        docs = retriever.invoke(question)

    # Some retriever implementations may return a dict-like payload.
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

    prompt = (
        f"{system}\n\n"
        f"CONTEXT:\n{context}\n\n"
        f"QUESTION:\n{question}\n\n"
        f"ANSWER:"
    )

    llm = ChatOllama(model=OLLAMA_CHAT_MODEL, base_url=OLLAMA_BASE_URL, temperature=OLLAMA_TEMPERATURE)
    resp = llm.invoke(prompt)

    answer = getattr(resp, "content", None)
    if not answer:
        answer = str(resp)

    return answer, sources


from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Set, Tuple

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
    """Build {document_name, document_id, page_number} rows from chunks."""
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


def _retrieved_page_pairs(docs: List[Any]) -> Set[Tuple[str, int]]:
    """Unique (document_id, page) from retrieval."""
    pairs: Set[Tuple[str, int]] = set()
    for d in docs:
        meta = dict(getattr(d, "metadata", {}) or {})
        did = str(meta.get("document_id") or "")
        try:
            page = int(meta.get("page_number"))
        except (TypeError, ValueError):
            continue
        if did:
            pairs.add((did, page))
    return pairs


def _doc_name_for_pair(docs: List[Any], document_id: str, page_number: int) -> str | None:
    for d in docs:
        meta = dict(getattr(d, "metadata", {}) or {})
        if str(meta.get("document_id") or "") != document_id:
            continue
        try:
            if int(meta.get("page_number")) != page_number:
                continue
        except (TypeError, ValueError):
            continue
        name = meta.get("document_name")
        if name:
            return str(name)
    return None


def _sources_from_llm_page_citations(
    docs: List[Any],
    citations: List[Dict[str, Any]],
    valid_pairs: Set[Tuple[str, int]],
) -> List[Dict[str, Any]]:
    """Turn LLM cited pages into source rows; drop unknown pairs and dedupe."""
    out: List[Dict[str, Any]] = []
    seen: Set[Tuple[str, int]] = set()
    for c in citations:
        if not isinstance(c, dict):
            continue
        did = str(c.get("document_id") or "").strip()
        if not did:
            continue
        try:
            page = int(c.get("page_number"))
        except (TypeError, ValueError):
            continue
        key = (did, page)
        if key not in valid_pairs or key in seen:
            continue
        seen.add(key)
        name = _doc_name_for_pair(docs, did, page)
        out.append(
            {
                "document_name": name or None,
                "document_id": did,
                "page_number": page,
            }
        )
    return out


def _build_context(docs: List[Any]) -> str:
    """RAG context string with DOCUMENT_ID and PAGE lines per chunk."""
    parts: List[str] = []
    for d in docs:
        meta = dict(getattr(d, "metadata", {}) or {})
        doc_name = meta.get("document_name") or meta.get("document_id") or "document"
        page = meta.get("page_number")
        did = str(meta.get("document_id") or "")

        header = f"DOCUMENT_ID: {did}\nPAGE: {page}\n[{doc_name}]"
        parts.append(f"{header}\n{d.page_content}")

    return "\n\n---\n\n".join(parts)


def _parse_llm_sources_json(raw: str) -> Tuple[str | None, List[Dict[str, Any]]]:
    """Parse answer + supporting_sources from model JSON (handles ``` fences)."""
    text = (raw or "").strip()
    if not text:
        return None, []

    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", text, re.IGNORECASE)
    if fence:
        text = fence.group(1).strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end <= start:
            return None, []
        try:
            data = json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            return None, []

    if not isinstance(data, dict):
        return None, []

    answer = data.get("answer")
    if answer is None:
        answer = data.get("response")
    answer_str = str(answer).strip() if answer is not None else ""

    raw_cites = data.get("supporting_sources")
    if raw_cites is None:
        raw_cites = data.get("sources") or data.get("citations")
    if raw_cites is None:
        raw_cites = []
    if isinstance(raw_cites, dict):
        raw_cites = [raw_cites]
    if not isinstance(raw_cites, list):
        raw_cites = []

    citations: List[Dict[str, Any]] = []
    for item in raw_cites:
        if isinstance(item, dict):
            citations.append(item)

    return (answer_str if answer_str else None), citations


def _make_chat_model() -> ChatHuggingFace:

    token = require_huggingface_api_token()
    endpoint_kwargs: Dict[str, Any] = {
        "repo_id": HF_CHAT_MODEL,
        "huggingfacehub_api_token": token,
        "return_full_text": False,
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
    """Retrieve, ask LLM (JSON answer + cited pages), return (answer, sources for UI)."""
    retriever = vectorstore.as_retriever(search_kwargs={"k": top_k})

    try:
        docs = retriever.get_relevant_documents(question)
    except Exception:
        docs = retriever.invoke(question)

    if isinstance(docs, dict) and "documents" in docs:
        docs = docs["documents"]

    context = _build_context(docs)
    fallback_sources = _format_sources(docs)
    valid_page_pairs = _retrieved_page_pairs(docs)

    system = (
        "You are DocQueryAI, a PDF question answering assistant. "
        "You MUST respond with a single JSON object only (no markdown fences, no text before or after). "
        'Schema: {"answer": string, "supporting_sources": array of '
        '{"document_id": string, "page_number": integer}}. '
        "Each CONTEXT block starts with DOCUMENT_ID and PAGE lines; use those exact values. "
        "List in supporting_sources only document_id and page_number pairs you actually used to write the answer. "
        "If the answer cannot be found in the context, set answer to "
        '"I don\'t know based on the uploaded documents." and supporting_sources to []. '
        "Do not invent document_id or page_number; each pair must match a block in CONTEXT."
    )

    user_block = (
        f"CONTEXT:\n{context}\n\n"
        f"QUESTION:\n{question}\n\n"
        "Reply with only the JSON object as specified in the system message."
    )

    chat = _make_chat_model()
    ai_msg = chat.invoke(
        [
            SystemMessage(content=system),
            HumanMessage(content=user_block),
        ]
    )
    raw = (getattr(ai_msg, "content", None) or str(ai_msg)).strip()

    parsed_answer, citations = _parse_llm_sources_json(raw)
    if parsed_answer is not None:
        answer = parsed_answer
        sources = _sources_from_llm_page_citations(docs, citations, valid_page_pairs)
    else:
        answer = raw if raw else "I could not parse the model response."
        sources = fallback_sources

    return answer, sources

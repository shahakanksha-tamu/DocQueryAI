from collections import defaultdict
from typing import Dict, List, Tuple
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import CHUNK_OVERLAP, CHUNK_SIZE


def chunk_documents(documents: List[Document]) -> List[Document]:
    """
    Split a list of page-level LangChain Documents into smaller chunk Documents.

    Metadata is preserved by the splitter so chunks retain source info like
    document_name, document_id, and page_number.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )
    chunks = splitter.split_documents(documents)
    chunks = add_chunk_ids(chunks)

    return chunks


def add_chunk_ids(chunks: List[Document]) -> List[Document]:
    """
    Add chunk ids for source tracking.

    For readability and traceability, chunk ids are page-local:
      document_id:p{page_number}:c{chunk_index_in_page}

    Also adds:
      - chunk_index_in_page (1-based)
    """
    counters: Dict[Tuple[str, int], int] = defaultdict(int)

    for chunk in chunks:
        meta = chunk.metadata or {}
        document_id = str(meta.get("document_id", "unknown"))
        page_number_raw = meta.get("page_number", 0)
        try:
            page_number = int(page_number_raw)
        except Exception:
            page_number = 0

        key = (document_id, page_number)
        counters[key] += 1
        chunk_index_in_page = counters[key]

        chunk.metadata["chunk_index_in_page"] = chunk_index_in_page
        chunk.metadata["chunk_id"] = f"{document_id}:p{page_number}:c{chunk_index_in_page}"
    return chunks
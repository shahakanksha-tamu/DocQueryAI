from rag.document_processing import process_uploaded_documents
from rag.chunking import chunk_documents
from rag.indexing import build_chroma_index

def rag_processing(uploaded_files, batch_id: str | None = None):
    """
    End-to-end preprocessing up to vector store creation (in-memory).

    Returns:
      page_docs, chunk_docs, vectorstore
    """
    page_docs = process_uploaded_documents(uploaded_files)
    chunk_docs = chunk_documents(page_docs)

    collection_name = f"batch_{batch_id}" if batch_id else None
    vectorstore = build_chroma_index(chunk_docs, collection_name=collection_name)
    return page_docs, chunk_docs, vectorstore



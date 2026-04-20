from langchain_core.documents import Document
import uuid
import fitz  # PyMuPDF


def process_uploaded_documents(uploaded_files):
    """One LangChain Document per non-empty PDF page per upload."""
    documents = []

    for file in uploaded_files:
        document_id = str(uuid.uuid4())
        pages = process_pdf_file(file)
        document = generate_document_object(pages, file.name, document_id)
        documents.extend(document)

    return documents


def process_pdf_file(file):
    """Extract text per page via PyMuPDF (skips blank pages)."""
    file_bytes = file.getvalue()
    pdf_document = fitz.open(stream=file_bytes, filetype="pdf")
    try:
        pages = []
        for i, page in enumerate(pdf_document):
            text = page.get_text()
            if not text.strip():
                continue
            pages.append(
                {
                    "text": text,
                    "page_number": i + 1,
                }
            )
        return pages
    finally:
        pdf_document.close()


def generate_document_object(pages, document_name, document_id):
    """Build LangChain Documents with metadata for each page dict."""
    documents = []
    for page in pages:
        documents.append(
            Document(
                page_content=page["text"],
                metadata={
                    "document_id": document_id,
                    "document_name": document_name,
                    "page_number": page["page_number"],
                },
            )
        )
    return documents


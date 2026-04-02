import os

# Chat session (Streamlit)
MAX_CHAT_SESSIONS_PER_DOCUMENT = 5

# Chunking and retrieval
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
TOP_K_RETRIEVAL = 5

# Embeddings: Hugging Face Hub model via sentence-transformers (token optional; from secrets/env)
HF_EMBEDDING_MODEL = os.environ.get(
    "HF_EMBEDDING_MODEL",
    "BAAI/bge-small-en-v1.5",
)
HF_EMBEDDING_DEVICE = os.environ.get("HF_EMBEDDING_DEVICE", "cpu").strip().lower()

HF_CHAT_MODEL = os.environ.get(
    "HF_CHAT_MODEL",
    "meta-llama/Llama-3.3-70B-Instruct",
)
HF_CHAT_PROVIDER = os.environ.get("HF_CHAT_PROVIDER", "").strip() or None
HF_CHAT_MAX_NEW_TOKENS = int(os.environ.get("HF_CHAT_MAX_NEW_TOKENS", "512"))
HF_CHAT_TEMPERATURE = float(os.environ.get("HF_CHAT_TEMPERATURE", "0.2"))

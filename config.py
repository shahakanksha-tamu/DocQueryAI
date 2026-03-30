# Chat session
MAX_CHAT_SESSIONS_PER_DOCUMENT = 5

# Chunking parameters
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

# Retrieval
TOP_K_RETRIEVAL = 6

# Ollama (local)
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_CHAT_MODEL = "llama3:latest"

# Embedding model (pull with `ollama pull nomic-embed-text`)
OLLAMA_EMBED_MODEL = "nomic-embed-text"

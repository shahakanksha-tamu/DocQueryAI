# DocQueryAI

DocQueryAI is a Streamlit-based document question-answering system. It uses a **Retrieval-Augmented Generation (RAG)** pipeline so users can upload one or more PDF documents, ask questions in natural language, and receive grounded answers with page-level source citations.

The system is especially useful for long, unstructured documents such as **research papers, technical documents, user manuals, game rulebooks, API documentation, project reports, and etc**, where manual keyword search is time-consuming. It is designed for workflows like academic research, technical analysis, and knowledge management.

At a high level, the system:
- extracts text from uploaded PDFs using PyMuPDF,
- splits content into chunks for semantic retrieval,
- embeds chunks with `BAAI/bge-small-en-v1.5`,
- retrieves top relevant chunks from ChromaDB, and
- generates answers using `meta-llama/Llama-3.3-70B-Instruct`.

## Architecture diagram

![DocQueryAI Architecture](assets/arch_diagram.png)

### Demo video

![DocQueryAI Demo](assets/demo_docqueryai.gif)

Full video: [assets/demo_docqueryai.mov](assets/demo_docqueryai.mov)

## 1) Local installation and run

### Prerequisites

- Python 3.10+ (3.11 recommended)

### Clone the repository

```bash
git clone https://github.com/shahakanksha-tamu/DocQueryAI.git
cd DocQueryAI
```

### Install dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

If PDF preview is unavailable, reinstall Streamlit PDF support:

```bash
pip install "streamlit[pdf]==1.54.0"
```

### Run the app locally

```bash
streamlit run app.py
```

Open `http://localhost:8501` in your browser.

## 2) Hugging Face token generation and configuration

### Generate a Hugging Face token

1. Create/sign in to a Hugging Face account: [https://huggingface.co/join](https://huggingface.co/join)
2. Go to tokens: [https://huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)
3. Click **New token**, choose appropriate access, and copy the token (`hf_...`)
4. If you use gated models (for example Llama), accept model terms on the model page first

### Configure token for DocQueryAI

DocQueryAI reads `HUGGINGFACE_API_TOKEN` in this order:
1. Environment variable `HUGGINGFACE_API_TOKEN`
2. `st.secrets["HUGGINGFACE_API_TOKEN"]` from `.streamlit/secrets.toml`

If both are set, the environment variable is used first.

The chat model requires this token. The embedding path uses the same token when available.

Option A (recommended for local development), environment variable:

```bash
export HUGGINGFACE_API_TOKEN="hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

Option B, Streamlit secrets file:

Create `.streamlit/secrets.toml`:

```toml
HUGGINGFACE_API_TOKEN = "hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

`.streamlit/secrets.toml` is already ignored by git. Do not commit real tokens.

### Runtime/model configuration

Defaults are defined in `config.py` and can be overridden via environment variables:

| Setting | Default | Env var |
|---|---|---|
| Embedding model | `BAAI/bge-small-en-v1.5` | `HF_EMBEDDING_MODEL` |
| Embedding device | `cpu` | `HF_EMBEDDING_DEVICE` |
| Chat model | `meta-llama/Llama-3.3-70B-Instruct` | `HF_CHAT_MODEL` |
| Chat provider (optional) | unset | `HF_CHAT_PROVIDER` |
| Max new tokens | `512` | `HF_CHAT_MAX_NEW_TOKENS` |
| Temperature | `0.2` | `HF_CHAT_TEMPERATURE` |
| Chunk size | `1000` | `CHUNK_SIZE` |
| Chunk overlap | `200` | `CHUNK_OVERLAP` |
| Top-k retrieval | `5` | `TOP_K_RETRIEVAL` |
| Max chat sessions per document set | `5` | `MAX_CHAT_SESSIONS_PER_DOCUMENT` |

Example overrides:

```bash
export HF_CHAT_MODEL="meta-llama/Llama-3.3-70B-Instruct"
export HF_CHAT_TEMPERATURE="0.2"
export HF_CHAT_MAX_NEW_TOKENS="512"
export HF_EMBEDDING_DEVICE="cpu"
export CHUNK_SIZE="1000"
export CHUNK_OVERLAP="200"
export TOP_K_RETRIEVAL="5"
export MAX_CHAT_SESSIONS_PER_DOCUMENT="5"
```

## 3) Deployment steps (Streamlit Community Cloud)

Live deployment: [https://docqueryaiv1.streamlit.app/](https://docqueryaiv1.streamlit.app/)

To deploy your own instance:

1. Push the code to your GitHub repository
2. Open [Streamlit Community Cloud](https://share.streamlit.io/) and sign in with GitHub
3. Click **New app**
4. Select repository and branch
5. Set **Main file path** to `app.py`
6. In app settings, add secrets:

```toml
HUGGINGFACE_API_TOKEN = "hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

Optional cloud overrides:

```toml
HF_CHAT_MODEL = "meta-llama/Llama-3.3-70B-Instruct"
HF_EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"
```

7. Deploy and wait for build completion
8. Open the generated app URL and test end-to-end (upload, chat, citations, preview)

### Pre-deployment checklist

- `requirements.txt` installs cleanly
- Hugging Face token has access to configured chat model
- No API tokens committed to the repository

## Project links

- Repository: [https://github.com/shahakanksha-tamu/DocQueryAI](https://github.com/shahakanksha-tamu/DocQueryAI)
- Demo video: [https://drive.google.com/file/d/14mGmEH6KbBdsg_aVFrXdlEpzFN7pLSn3/view](https://drive.google.com/file/d/14mGmEH6KbBdsg_aVFrXdlEpzFN7pLSn3/view)
- Chat model: [https://huggingface.co/meta-llama/Llama-3.3-70B-Instruct](https://huggingface.co/meta-llama/Llama-3.3-70B-Instruct)
- Embedding model: [https://huggingface.co/BAAI/bge-small-en-v1.5](https://huggingface.co/BAAI/bge-small-en-v1.5)

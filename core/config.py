# core/config.py
import os
import dotenv
from typing import Optional
from langchain_cerebras import ChatCerebras
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
import logging
logger = logging.getLogger(__name__)

dotenv.load_dotenv()

# ── LLM ───────────────────────────────────────────────────────
LLM_MODEL      = os.environ.get("LLM_MODEL", "qwen-3-235b-a22b-instruct-2507")
TEMPERATURE    = float(os.environ.get("LLM_TEMPERATURE", "0.2"))
MAX_REFLECTIONS= int(os.environ.get("MAX_REFLECTIONS", "2"))

# ── Vector stores ─────────────────────────────────────────────
MEM_COLLECTION = os.environ.get("MEM_COLLECTION", "mini_manus_memory")
PERSIST_DIR    = "./agent_memory"
RAG_PERSIST_DIR= "./rag_docs"
RAG_COLLECTION = "rag_docs"

# ── Embedding model ───────────────────────────────────────────
# Upgraded from all-MiniLM-L6-v2 (384-dim) to BAAI/bge-small-en-v1.5 (384-dim same size,
# but trained with BGE contrastive learning — significantly better retrieval accuracy
# on English text, especially technical/academic content).
# Alternative: "BAAI/bge-base-en-v1.5" (768-dim, higher accuracy, more RAM)
#              "thenlper/gte-small" (another strong 384-dim option)
EMBED_MODEL = os.environ.get(
    "EMBED_MODEL",
    "BAAI/bge-small-en-v1.5"   # was: all-MiniLM-L6-v2
)

# BGE models need a query prefix for retrieval tasks
# (they were trained with it — omitting it degrades quality)
EMBED_QUERY_INSTRUCTION = "Represent this sentence for searching relevant passages: "

# ── Global singletons ─────────────────────────────────────────
_llm = ChatCerebras(
    model=LLM_MODEL,
    temperature=TEMPERATURE,
    api_key=os.getenv("API_KEY"),
    streaming=True,
    max_tokens=2048,
    top_p=1,
)

_embedding_fn = HuggingFaceEmbeddings(
    model_name=EMBED_MODEL,
    model_kwargs={"device": "cpu"},
    encode_kwargs={
        "normalize_embeddings": True,
        "batch_size": 32,
    },
)

_vectorstore: Optional[Chroma] = None

print(f"✅ Core config loaded | LLM: {LLM_MODEL} | Embeddings: {EMBED_MODEL}")
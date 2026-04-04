# core/config.py

import os
import random
import time
import logging
import shutil
from dotenv import load_dotenv
from typing import Any, Optional

from langchain_cerebras import ChatCerebras
from langchain_ollama import ChatOllama
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

logger = logging.getLogger(__name__)

# Load env variables
load_dotenv()

# ══════════════════════════════════════════════════════════════
# LLM CONFIGURATION
# ══════════════════════════════════════════════════════════════

# Primary LLM (Cerebras)
_cerebras_api_key = os.getenv("API_KEY")

if not _cerebras_api_key:
    raise ValueError("API_KEY not found. Set your Cerebras API key.")

_cerebras_llm = ChatCerebras(
    model=os.environ.get("CEREBRAS_MODEL", "qwen-3-235b-a22b-instruct-2507"),
    temperature=0.2,
    api_key=_cerebras_api_key,
    max_tokens=4000,
    top_p=0.8,
)

# Fallback LLM (Ollama)
_ollama_llm = ChatOllama(
    model=os.environ.get("OLLAMA_MODEL", "my-agent"),
    base_url=os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434"),
    temperature=0.2,
    num_ctx=4096,
)

# ══════════════════════════════════════════════════════════════
# LLM ROUTER
# ══════════════════════════════════════════════════════════════

class LLMRouter:
    def __init__(self, primary_llm: Any, fallback_llm: Any):
        self.primary_llm = primary_llm
        self.fallback_llm = fallback_llm

    def invoke(
        self,
        prompt: str,
        max_retries: int = 3,
        base_delay: float = 1.5,
        task_complexity: Optional[str] = None,
    ) -> Any:

        prompt_length = len(prompt.split())

        # Smart routing
        use_ollama = (
            task_complexity == "simple"
            or prompt_length < 100
        )

        if use_ollama:
            logger.info("🟢 Routing to Ollama (fast/local)")
            try:
                return self._invoke_with_retries(
                    self.fallback_llm, prompt, max_retries, base_delay
                )
            except Exception as e:
                logger.warning(f"Ollama failed → fallback to Cerebras: {e}")
                return self._invoke_with_retries(
                    self.primary_llm, prompt, max_retries, base_delay
                )

        logger.info("🚀 Routing to Cerebras (primary)")
        try:
            return self._invoke_with_retries(
                self.primary_llm, prompt, max_retries, base_delay
            )
        except Exception as e:
            logger.warning(f"Cerebras failed → fallback to Ollama: {e}")
            return self._invoke_with_retries(
                self.fallback_llm, prompt, max_retries, base_delay
            )

    def _invoke_with_retries(
        self,
        llm: Any,
        prompt: str,
        max_retries: int,
        base_delay: float,
    ) -> Any:
        last_exc = None

        for attempt in range(max_retries):
            try:
                response = llm.invoke(prompt)

                # Normalize response
                if hasattr(response, "content"):
                    return response
                else:
                    return type("LLMResponse", (), {"content": str(response)})()

            except Exception as exc:
                last_exc = exc
                err = str(exc).lower()

                transient = any(k in err for k in [
                    "server error", "503", "502", "504", "529",
                    "rate limit", "overloaded", "timeout",
                    "connection", "api_key"
                ])

                if not transient:
                    raise

                delay = base_delay * (2 ** attempt) + random.uniform(0, 0.5)
                logger.warning(
                    f"Retry {attempt+1}/{max_retries} for {llm.__class__.__name__} "
                    f"after {delay:.2f}s → {exc}"
                )
                time.sleep(delay)

        raise last_exc


# Global LLM instance
_llm = LLMRouter(
    primary_llm=_cerebras_llm,
    fallback_llm=_ollama_llm
)

# ══════════════════════════════════════════════════════════════
# EMBEDDINGS & RAG
# ══════════════════════════════════════════════════════════════

_embedding_fn = HuggingFaceEmbeddings(
    model_name="all-MiniLM-L6-v2"
)

RAG_PERSIST_DIR = os.environ.get("RAG_PERSIST_DIR", "rag_db")
RAG_COLLECTION  = os.environ.get("RAG_COLLECTION", "multiagent_rag")

PERSIST_DIR     = os.environ.get("PERSIST_DIR", "memory_db")
MEM_COLLECTION  = os.environ.get("MEM_COLLECTION", "multiagent_memory")

MAX_REFLECTIONS = int(os.environ.get("MAX_REFLECTIONS", 3))

# ══════════════════════════════════════════════════════════════
# MEMORY STORE
# ══════════════════════════════════════════════════════════════

_vectorstore: Chroma

try:
    _vectorstore = Chroma(
        collection_name=MEM_COLLECTION,
        embedding_function=_embedding_fn,
        persist_directory=PERSIST_DIR
    )
    logger.info("Memory DB loaded")

except Exception as e:
    logger.warning(f"Resetting memory DB: {e}")
    shutil.rmtree(PERSIST_DIR, ignore_errors=True)

    _vectorstore = Chroma(
        collection_name=MEM_COLLECTION,
        embedding_function=_embedding_fn,
        persist_directory=PERSIST_DIR
    )
    logger.info("Memory DB re-initialized")
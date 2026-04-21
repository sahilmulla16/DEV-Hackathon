# agent.py
from __future__ import annotations
import os
import json
import time
import random
import logging
import re as _re
from typing import TypedDict, List, Dict, Any, Optional, Callable

from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langgraph.graph import StateGraph, END
from langchain_community.document_loaders import (
    TextLoader, PyPDFLoader, CSVLoader, UnstructuredExcelLoader,
    UnstructuredPowerPointLoader,
)

from core.config import _llm, _embedding_fn, RAG_PERSIST_DIR, RAG_COLLECTION, MAX_REFLECTIONS
from core.utils import safe_json_loads
from core.memory import mem_add, mem_recall
from frontend.src.components.tools import TOOLS

logger = logging.getLogger(__name__)

# ══════════════════════════════════════════════════════════════
# RETRY WRAPPER
# ══════════════════════════════════════════════════════════════

def _llm_invoke(prompt: str, max_retries: int = 4, base_delay: float = 1.5) -> str:
    last_exc = None
    for attempt in range(max_retries):
        try:
            return _llm.invoke(prompt).content.strip()
        except Exception as exc:
            last_exc = exc
            err = str(exc).lower()
            transient = any(k in err for k in [
                "server error","503","502","504","529",
                "rate limit","overloaded","timeout","connection","try again",
            ])
            if not transient:
                raise
            delay = base_delay * (2 ** attempt) + random.uniform(0, 0.5)
            logger.warning(f"LLM transient error (attempt {attempt+1}/{max_retries}): {exc!r}. Retry in {delay:.1f}s")
            time.sleep(delay)
    raise last_exc  # type: ignore[misc]


# ══════════════════════════════════════════════════════════════
# @ MENTION HELPERS
# ══════════════════════════════════════════════════════════════

def _parse_mentions(text: str) -> List[str]:
    return _re.findall(r'@([\w\-. ]+\.[\w]+)', text)

def _strip_mentions(text: str) -> str:
    return _re.sub(r'@[\w\-. ]+\.[\w]+', '', text).strip()


# ══════════════════════════════════════════════════════════════
# PROMPTS
# ══════════════════════════════════════════════════════════════

DIRECT_ANSWER_SYS = """
You are a helpful assistant that answers questions ONLY from the provided memory context.
The memory may contain structured facts in JSON, like {"entity":"user","attribute":"name","value":"haad"}.
Parse these JSON facts to answer precisely. Do not mention the JSON structure.
If memory does NOT contain enough info, respond ONLY with: 'NO_DIRECT_ANSWER'
"""

INTENT_DISTILLER_PROMPT = """
You are an intent distiller. Extract the user's real actionable task in one sentence.

{active_connectors_prompt_block}

RULES:
- If the user's request clearly matches an active connector's purpose (e.g., "create an issue" for GitHub), output the task directly, mentioning the connector's domain. Example: "Use GitHub to create an issue..."
- If the user references a file (@filename.ext or "in the document") AND the task is NOT related to a connector, note it: "Search file X for: <question>"
- For greetings / casual chat: output the message as-is
- For factual questions ("what is X", "explain Y", "how does Z work"): output the question directly — do NOT add tool instructions
- For image requests ("find a picture", "show me an image"): output "Find an image of: <topic>"
- For code requests: output "Write code to: <task>"
- ONLY if the user explicitly asks for a full REPORT, DEEP RESEARCH, or INVESTIGATION (e.g. "deep research on X", "write a report about X", "do a full analysis of X"): output "Research report on: <topic>"

Output ONLY the distilled task. No tool names, no meta-commentary.

Distill the following:
"""

# Keywords that signal a research request — used for the pre-planner fast-path
_RESEARCH_KEYWORDS = (
    "research", "report", "investigate", "investigation",
    "analyse", "analyze", "analysis", "summarise", "summarize", "summary",
    "compare", "comparison", "timeline", "history of", "critique", "critical analysis",
    "deep dive", "deep research", "in-depth", "write a report", "write report",
    "give me a report", "detailed report", "comprehensive", "overview of",
    "explain in detail", "tell me about", "study",
)

_MODE_KEYWORDS: Dict[str, str] = {
    "summary":   ["summarise", "summarize", "summary", "brief", "overview", "tldr"],
    "compare":   ["compare", "comparison", "vs", "versus", "difference between", "contrast"],
    "timeline":  ["timeline", "history of", "chronological", "evolution of", "over time"],
    "critique":  ["critique", "critical", "weakness", "flaw", "counter", "criticise", "criticize"],
    "questions": ["research questions", "give me questions", "generate questions", "what questions"],
    "deep":      ["research", "report", "investigate", "deep", "in-depth", "comprehensive", "detailed", "analyse", "analyze"],
}

def _detect_research_mode(text: str) -> str:
    """Return the best research mode based on keywords in the text."""
    low = text.lower()
    for mode, keywords in _MODE_KEYWORDS.items():
        if any(k in low for k in keywords):
            return mode
    return "deep"

# Only trigger research_agent_tool for EXPLICIT full-report/deep-research requests
_RESEARCH_REPORT_KEYWORDS = (
    "deep research",
    "deep dive into",
    "write a report",
    "write report",
    "give me a report",
    "detailed report",
    "full report",
    "research report",
    "comprehensive report",
    "in-depth report",
    "full analysis of",
    "do research on",
    "conduct research",
    "research paper on",
    "investigate thoroughly",
)

def _is_research_report_request(text: str) -> bool:
    """True ONLY for explicit research report / deep-research requests.
    Simple explanations, summaries and factual questions return False."""
    low = text.lower()
    return any(k in low for k in _RESEARCH_REPORT_KEYWORDS)

def _is_research_request(text: str) -> bool:
    """Return True if the text signals a research/report request."""
    low = text.lower()
    return any(k in low for k in _RESEARCH_KEYWORDS)

PLANNER_SYS = """
You are the Planner in an autonomous multi-agent system. Choose the RIGHT tool for the user's task.

TOOL SELECTION — read carefully:

1. `connector_tool` — Use for simple, direct actions on external services (e.g., "list my github issues", "send an email").
   - Look for specific connector tools in the list below.
   - If the task involves creating files or running shell commands first, use `coding_agent_tool` instead.

2. `web_search` — Search the live web for facts, explanations, current info.
   - USE for: "what is X", "explain X", "how does X work", "who is X", general knowledge questions.
   - DO NOT use for finding images. Use `image_search` for that.

3. `rag_search` — Search uploaded documents.
   - USE when: user @mentioned a file, OR question might be in uploaded docs.

4. `research_agent_tool` — Full multi-source research REPORT (takes 1-2 minutes).
   - USE ONLY when user EXPLICITLY asks for a report/deep research/investigation.
   - DO NOT use for simple explanations, summaries, or factual questions.

5. `coding_agent_tool` — A powerful sub-agent that can write code, manage files, and use other tools to complete complex software tasks.
   - USE for any multi-step coding task: writing scripts, building websites, or complex git workflows like creating a new repository and pushing initial files.
   - This tool can orchestrate other tools, like `write_file`, `run_code`, and even `connector_tool`.
   - This tool can also use `image_search` to find images for websites it builds.
   - Example: "create a new repo 'test' and add a README", "build a website about dogs".

6. `image_search` — Find and download images from the web.
   - USE for: "find a picture of", "show me an image of", "get a photo of".

7. `calculator` — Math only.

8. No tool — Greetings, casual chat, questions you can answer from your own knowledge.

DECISION GUIDE:
- "find a picture of a cat" -> `image_search`
- "create a new repo 'test'" → `coding_agent_tool`
- "list my github issues" → `connector_tool` with `connector_id='github'`
- "explain what a neural network is" → `web_search`
- "summarize the uploaded file @report.pdf" → `rag_search`
- "write a full report on climate change" → `research_agent_tool`
- "write a python script to parse a CSV file" → `coding_agent_tool`

Available tools:
{tool_list}

You MUST ONLY use tools from the "Available tools" list. Do not invent tools or use tools not listed.

Return ONLY a JSON object matching this schema: {{"steps":[{{"id":int,"thought":str,"tool":str,"args":dict,"output_key":str}}]}}
"""

EXECUTOR_SYS = """
You are the Executor. Your task is to synthesize a helpful, natural answer for the user based on the provided tool observations.

Follow these rules carefully:
1.  **Synthesize, Don't Invent**: Base your answer *only* on the information in the `Observations`. Do not add information that is not present.
2.  **Handle Search Results**: If the observations contain search results (from `web_search` or `rag_search`), integrate them into a clear, well-structured answer. Cite sources if available.
3.  **Handle Image Results**: If an observation from `image_search` contains `image_paths`, you MUST display the image using markdown, like this: `!Image`. Replace `path/to/image.jpg` with the first path from the `image_paths` list.
4.  **Handle Empty/Unhelpful Observations**: If a tool was used (e.g., `connector_tool`) but the `stdout` or `observation` is empty, contains only boilerplate, or seems unrelated to the user's request, state that the tool was run but did not provide useful information. You can suggest checking the tool's configuration. Example: "I tried to fetch your emails, but the Gmail connector didn't return any data. Please ensure it is configured correctly in the settings."
5.  **Handle No Tool**: If no tools were used (`no_tool`), answer the user's question directly from your own knowledge. This applies to greetings, casual chat, or simple factual questions.
6.  **Be Direct**: Provide ONLY the answer. Do not include meta-commentary about the tools used or the system's internal process.
"""

VERIFIER_SYS = """
You are the Verifier. Your job is to check if the draft adequately answers the user's question.

RULES — read carefully:
1. If the draft is a greeting or casual response → ALWAYS approve.
2. If the observations contain RAG/document search results (tool=rag_search) → ALWAYS approve the draft, even if the content seems incomplete or the document didn't fully answer the question. The retrieval was done correctly.
3. If the draft says "The document does not contain information about this topic" → APPROVE it — this is a valid, honest answer.
4. Only REJECT if: the draft is completely blank, or is about a totally different topic than the user asked about.
5. NEVER reject just because text was fragmented, chunked, or imperfect.

Return ONLY valid JSON (no markdown, no extra text):
{"approved": true/false, "feedback": "...", "final": "..."}

If approved=true: put the polished answer in "final".
If approved=false: put the reason in "feedback", leave "final" as "".
"""


# ══════════════════════════════════════════════════════════════
# KNOWLEDGE BASE INGESTION
# ══════════════════════════════════════════════════════════════

def _load_docx_safe(file_path: str):
    """
    Load .doc/.docx using python-docx — no spaCy / unstructured required.
    Works on Windows without admin rights.
    Install: pip install python-docx
    """
    try:
        import docx as _docx
    except ImportError:
        raise ImportError("python-docx not installed. Run: pip install python-docx")
    from langchain_core.documents import Document
    doc   = _docx.Document(file_path)
    # Extract paragraphs + table cells
    parts = [p.text for p in doc.paragraphs if p.text.strip()]
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                if cell.text.strip():
                    parts.append(cell.text.strip())
    text = "\n".join(parts)
    return [Document(page_content=text, metadata={"source": file_path})]


def _clean_text(text: str) -> str:
    """Remove common PDF/OCR artifacts and normalise whitespace."""
    import re as _re
    text = _re.sub(r'[ \t]+', ' ', text)               # collapse spaces/tabs
    text = _re.sub(r'\n{3,}', '\n\n', text)            # max 2 consecutive newlines
    text = _re.sub(r'-\n', '', text)                    # rejoin hyphenated line-breaks
    text = _re.sub(r'(?<=[a-z])\n(?=[a-z])', ' ', text) # rejoin mid-sentence line-breaks
    text = text.replace('\x00', '').replace('\xad', '') # null bytes + soft hyphens
    text = _re.sub(r'\s*\|\s*', ' | ', text)           # clean table separators
    return text.strip()


def _normalise_source(path: str) -> str:
    """Always store source with forward-slashes for cross-platform filter compat."""
    return path.replace("\\", "/")


def backfill_rag_metadata() -> str:
    """
    One-time migration: adds 'filename' metadata field to any Chroma chunks
    that were ingested before the enhanced pipeline was deployed.

    Safe to call multiple times — skips chunks that already have 'filename'.
    Call this once from app.py on startup, or trigger it via /api/rag/backfill.
    """
    try:
        rag_db = Chroma(
            persist_directory=RAG_PERSIST_DIR,
            embedding_function=_embedding_fn,
            collection_name=RAG_COLLECTION,
        )
        col    = rag_db._collection
        result = col.get(include=["metadatas", "documents"])
        ids    = result["ids"]
        metas  = result["metadatas"]

        if not ids:
            return "No chunks found in RAG store."

        to_update_ids   = []
        to_update_metas = []

        for chunk_id, meta in zip(ids, metas):
            if not meta.get("filename"):
                source = meta.get("source", "")
                fname  = os.path.basename(source.replace("\\", "/")) if source else ""
                if fname:
                    new_meta = {**meta, "filename": fname}
                    to_update_ids.append(chunk_id)
                    to_update_metas.append(new_meta)

        if not to_update_ids:
            return "All chunks already have filename metadata — nothing to backfill."

        # Update in batches of 100
        batch_size = 100
        for i in range(0, len(to_update_ids), batch_size):
            col.update(
                ids=to_update_ids[i:i+batch_size],
                metadatas=to_update_metas[i:i+batch_size],
            )

        logger.info(f"RAG backfill: patched {len(to_update_ids)} chunks with filename metadata")
        return f"Backfilled {len(to_update_ids)} chunks ({len(ids) - len(to_update_ids)} already had filename)."

    except Exception as e:
        logger.error(f"RAG backfill error: {e}")
        return f"Backfill failed: {e}"


def ingest_knowledge_base(file_path: str) -> str:
    """
    Enhanced RAG ingestion pipeline:
      1. Load document with appropriate loader
      2. Clean OCR/PDF artifacts
      3. Paragraph-aware semantic chunking
      4. Enrich metadata (filename, page, chunk_index, word_count)
      5. Deduplicate near-identical chunks
      6. Store in Chroma vector store
    """
    logger.info(f"Ingesting file: {file_path}")
    ext      = os.path.splitext(file_path)[1].lower()
    filename = os.path.basename(file_path)

    # ── Step 1: Load ────────────────────────────────────────────
    if ext in (".doc", ".docx"):
        documents = _load_docx_safe(file_path)
    else:
        loader_map = {
            ".txt":  lambda p: TextLoader(p, encoding="utf-8"),
            ".pdf":  PyPDFLoader,
            ".csv":  CSVLoader,
            ".xls":  UnstructuredExcelLoader,
            ".xlsx": UnstructuredExcelLoader,
            ".ppt":  UnstructuredPowerPointLoader,
            ".pptx": UnstructuredPowerPointLoader,
        }
        if ext not in loader_map:
            raise ValueError(f"Unsupported file type: {ext}")
        documents = loader_map[ext](file_path).load()

    # ── Step 2: Clean + normalise metadata ──────────────────────
    for doc in documents:
        doc.page_content           = _clean_text(doc.page_content)
        doc.metadata["source"]     = _normalise_source(doc.metadata.get("source", file_path))
        doc.metadata["filename"]   = filename       # fast filter by just the filename
        doc.metadata["file_ext"]   = ext.lstrip(".")

    # ── Step 3: Semantic chunking ────────────────────────────────
    # Paragraph-aware: split on section/paragraph breaks first,
    # fall back to sentence then word boundaries. chunk_size ~1000
    # chars ≈ 150–180 words — enough for full paragraphs without
    # being so large retrieval loses precision.
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150,
        separators=["\n\n\n", "\n\n", "\n", ". ", "? ", "! ", "; ", ", ", " ", ""],
        length_function=len,
        keep_separator=False,
    )
    chunks = splitter.split_documents(documents)

    # ── Step 4: Enrich chunk metadata ───────────────────────────
    for i, chunk in enumerate(chunks):
        chunk.metadata["chunk_index"] = i
        chunk.metadata["char_count"]  = len(chunk.page_content)
        chunk.metadata["word_count"]  = len(chunk.page_content.split())
        if "filename" not in chunk.metadata:
            chunk.metadata["filename"] = filename

    # ── Step 5: Quality filter + near-duplicate removal ─────────
    seen: set = set()
    clean_chunks = []
    for chunk in chunks:
        text = chunk.page_content.strip()
        if len(text) < 60 or len(text.split()) < 10:
            continue                                   # too short to be useful
        fingerprint = text[:80] + text[-80:]
        if fingerprint in seen:
            continue                                   # near-duplicate
        seen.add(fingerprint)
        clean_chunks.append(chunk)

    if not clean_chunks:
        raise ValueError(f"No usable text extracted from '{filename}'. Check the file format.")

    # ── Step 6: Store ────────────────────────────────────────────
    Chroma.from_documents(
        documents=clean_chunks,
        embedding=_embedding_fn,
        persist_directory=RAG_PERSIST_DIR,
        collection_name=RAG_COLLECTION,
    )
    logger.info(f"Ingested '{filename}': {len(clean_chunks)} chunks (from {len(chunks)} raw)")

    # Backfill any previously ingested chunks that are missing filename metadata
    # (safe no-op if all chunks already have it)
    try:
        backfill_rag_metadata()
    except Exception:
        pass

    return f"'{filename}' ingested with {len(clean_chunks)} high-quality chunks."


# ══════════════════════════════════════════════════════════════
# STATE
# ══════════════════════════════════════════════════════════════

class GraphState(TypedDict, total=False):
    user_input:          str
    clean_input:         str
    mentioned_files:     List[str]
    plan:                List[Dict[str, Any]]
    observations:        List[Dict[str, Any]]
    draft:               str
    feedback:            str
    reflections:         int
    final:               str
    file_path:           Optional[str]
    log:                 List[str]
    history:             List[Any]
    connector_configs:   Optional[Dict[str, Any]]
    _on_log:             Optional[Callable]   # streaming log callback
    _on_workspace_event: Optional[Callable]   # streaming workspace event callback


# ══════════════════════════════════════════════════════════════
# LOG HELPER
# streams immediately via callback AND stores in state
# ══════════════════════════════════════════════════════════════

def _log(state: GraphState, entry: str) -> None:
    state.setdefault("log", []).append(entry)
    cb = state.get("_on_log")
    if callable(cb):
        try:
            cb(entry)
        except Exception:
            pass


# ══════════════════════════════════════════════════════════════
# NODES
# ══════════════════════════════════════════════════════════════
def node_slash_command_parser(state: GraphState) -> Dict:
    """Fast-path for /<connector> commands."""
    user_input = state.get("user_input", "").strip()
    if not user_input.startswith('/'):
        return {}  # Not a slash command, continue to normal planning

    from frontend.src.components.tools import CONNECTORS_DEF
    connector_configs = state.get("connector_configs") or {}
    active_connectors = list(connector_configs.keys())

    # Sort by length descending to match longest prefix first (e.g., 'google-calendar' before 'google')
    active_connectors.sort(key=len, reverse=True)

    for connector_id in active_connectors:
        prefix = f"/{connector_id.lower()}"
        # Match must be the full command or followed by a space
        if user_input.lower() == prefix or user_input.lower().startswith(prefix + ' '):
            conn_def = next((c for c in CONNECTORS_DEF if c["id"] == connector_id), None)
            if not conn_def:
                continue

            # The rest of the input is everything after the command itself
            rest_of_input = user_input[len(prefix):].strip()

            _log(state, f"⚡️ Slash command detected: /{connector_id}. Routing directly to connector.")
            plan = [{
                "id": 1,
                "tool": "connector_tool",
                "args": {"connector_id": conn_def['id'], "user_input": rest_of_input},
                "thought": f"User issued a direct slash command for the {conn_def['name']} connector."
            }]
            return {"plan": plan, "log": state["log"]}

    command_part = user_input.lstrip('/').split(' ', 1)[0].lower()
    _log(state, f"⚠️ Slash command '/{command_part}' not found or not active. Treating as normal input.")
    return {}



def node_direct_answer(state: GraphState) -> GraphState:
    _log(state, "🧠 Memory: Checking long-term memory for a direct answer…")
    mem_list = list(set(mem_recall(state.get("user_input",""), k=5) + mem_recall("fact:", k=5)))
    if not mem_list:
        _log(state, "🤔 Memory: Nothing relevant found — routing to Planner.")
        return {"log": state["log"]}
    mem_text = "\n".join(mem_list)
    _log(state, f"🧠 Memory: Found {len(mem_list)} relevant memories. Evaluating…")
    try:
        response = _llm_invoke(DIRECT_ANSWER_SYS + "\nRelevant memory:\n" + mem_text + "\nUser input:\n" + state.get("user_input",""))
    except Exception as exc:
        _log(state, f"⚠️ Memory: LLM error ({exc!r}). Skipping to Planner.")
        return {**state, "log": state["log"]}
    if "NO_DIRECT_ANSWER" in response:
        _log(state, "🤔 Memory: No direct answer found — routing to Planner.")
        return {**state, "log": state["log"]}
    _log(state, "✅ Memory: Direct answer found. Skipping planning pipeline.")
    return {**state, "final": response, "log": state["log"]}


def node_planner(state: GraphState) -> GraphState:
    user_input      = state.get("user_input", "")
    file_path       = state.get("file_path")
    mentioned_files = state.get("mentioned_files", [])
    history         = state.get("history", [])
    connector_configs = state.get("connector_configs") or {}
    active_connectors = list(connector_configs.keys())

    history_str = "".join(
        f"User: {p[0]}\nAgent: {p[1]}\n"
        for p in history[-5:]
        if isinstance(p, (list,tuple)) and len(p)==2
    )

    _log(state, f"🔌 Planner: Active connectors detected: {active_connectors if active_connectors else 'None'}")

    # Fast-path: uploaded file
    if file_path:
        _log(state, f"📎 Planner: File upload detected — '{os.path.basename(file_path)}'. Searching knowledge base…")
        plan = [{"id":1,"thought":"User uploaded a file. Searching it.","tool":"rag_search",
                 "args":{"query":user_input,"source_file":os.path.basename(file_path)},
                 "output_key":"rag_results"}]
        return {"plan": plan, "log": state["log"], "file_path": file_path, "history": history}

    # Fast-path: @mention
    if mentioned_files:
        source = mentioned_files[0]
        clean  = _strip_mentions(user_input)
        _log(state, f"📎 Planner: @mention detected → will search '{source}'")
        plan = [{"id":1,"thought":f"User @mentioned {source}. Searching that file.","tool":"rag_search",
                 "args":{"query": clean or user_input,"source_file": source},"output_key":"rag_results"}]
        return {"plan": plan, "log": state["log"], "history": history}

    # Fast-path: explicit research REPORT request → research_agent_tool
    # Uses _is_research_report_request (stricter) so factual queries still go through
    # normal planning and can use rag_search + web_search as needed
    clean_input = state.get("clean_input", user_input)
    if _is_research_report_request(user_input) or _is_research_report_request(clean_input):
        mode = _detect_research_mode(user_input)
        _log(state, f"🔬 Planner: Research report request → research_agent_tool (mode={mode})")
        plan = [{
            "id":         1,
            "thought":    f"User wants a research {mode} report. Delegating to research_agent_tool.",
            "tool":       "research_agent_tool",
            "args":       {"user_input": user_input, "mode": mode},
            "output_key": "research_result",
        }]
        _log(state, f"   ↳ Step 1: [research_agent_tool] {mode} — {user_input[:60]}…")
        return {"plan": plan, "log": state["log"], "history": history}

    # General planning via LLM
    _log(state, "🎯 Planner: Distilling user intent…")
    mem_list = mem_recall(user_input, k=4)
    mem_text = "\n".join(mem_list) if mem_list else "<none>"

    # --- DYNAMIC CONNECTORS FOR DISTILLER ---
    from frontend.src.components.tools import CONNECTORS_DEF
    active_connectors_prompt_block = ""
    if active_connectors:
        connector_descs = []
        for cid in active_connectors:
            cdef = next((c for c in CONNECTORS_DEF if c["id"] == cid), None)
            if cdef:
                keywords = cdef.get('keywords', [])
                keywords_str = f" (Keywords: {', '.join(keywords)})" if keywords else ""
                connector_descs.append(f"- {cdef['name']} ({cdef['id']}): {cdef['description']}{keywords_str}")
        if connector_descs:
            active_connectors_prompt_block = "ACTIVE CONNECTORS:\n" + "\n".join(connector_descs)
    # ---

    try:
        distiller_prompt = INTENT_DISTILLER_PROMPT.replace("{active_connectors_prompt_block}", active_connectors_prompt_block)
        distilled = _llm_invoke(
            distiller_prompt
            + "\nChat History:\n" + history_str
            + "\nRelevant memory:\n" + mem_text
            + "\nUser input:\n" + user_input
        )
    except Exception as exc:
        _log(state, f"⚠️ Planner: Distiller failed ({exc!r}). Using raw input.")
        distilled = user_input

    # ── Strip any tool instructions the distiller LLM may have added ──
    # This prevents "Use research_agent_tool." from leaking into the planner
    import re as _re2
    distilled_clean = _re2.sub(
        r'(Use\s+\w+_tool\b[^.]*\.\s*|Mode:\s*\w+\s*|Tool:\s*\w+\s*)',
        '', distilled, flags=_re2.IGNORECASE
    ).strip()
    # Extract just the task description if format is "Task: <task>"
    task_match = _re2.search(r'Task:\s*(.+)', distilled_clean, _re2.IGNORECASE)
    if task_match:
        distilled_clean = task_match.group(1).strip()
    if not distilled_clean:
        distilled_clean = user_input

    _log(state, f"🎯 Planner: Intent → '{distilled_clean[:90]}{'…' if len(distilled_clean)>90 else ''}'")
    _log(state, "📝 Planner: Building execution plan…")

    # --- DYNAMIC TOOL LIST ---
    from frontend.src.components.tools import CONNECTORS_DEF

    # Base tools that are always available
    base_tools = {
        "web_search", "rag_search", "research_agent_tool",
        "coding_agent_tool", "calculator", "image_search", "write_file", "read_file",
        "list_files", "delete_file", "run_code", "start_server",
        "stop_server", "list_servers", "install_package"
    }
    dynamic_tool_descriptions = []
    for name in sorted(base_tools):
        if name in TOOLS:
            dynamic_tool_descriptions.append(f"- {name}: {TOOLS[name]['desc']}")

    # Add active connectors to the tool list for the planner
    for connector_id in active_connectors:
        conn_def = next((c for c in CONNECTORS_DEF if c["id"] == connector_id), None)
        if conn_def:
            tool_desc = f"Use the '{conn_def['name']}' connector for tasks like: {conn_def['description']}"
            dynamic_tool_descriptions.append(
                f"- connector_tool (args: connector_id='{conn_def['id']}', user_input='...'): {tool_desc}"
            )
    tool_list_str = "\n".join(dynamic_tool_descriptions)
    # --- END DYNAMIC TOOL LIST ---

    try:
        raw = _llm_invoke(
            PLANNER_SYS.replace("{tool_list}", tool_list_str)
            + "\nRelevant memory:\n" + mem_text
            + "\nUser task:\n" + distilled_clean
            + '\nRespond with ONLY JSON: {"steps":[...]}\n'
        )
    except Exception as exc:
        _log(state, f"⚠️ Planner: LLM failed after retries ({exc!r}). Empty plan.")
        return {"plan":[], "log": state["log"], "history": history}

    parsed = safe_json_loads(raw)
    steps  = parsed.get("steps",[]) if isinstance(parsed,dict) else []

    # ── Guard: correct wrong tool choices ────────────────────────
    clean_input = state.get("clean_input", user_input)
    user_task_lower = (distilled_clean or user_input).lower()

    # Helper to find a matching connector for the user's task
    def find_matching_connector():
        for connector_id in active_connectors:
            conn_def = next((c for c in CONNECTORS_DEF if c["id"] == connector_id), None)
            if conn_def:
                # Keywords: id, name, and phrases in quotes from description
                trigger_phrases = [conn_def['id'].lower(), conn_def['name'].lower()]
                if conn_def.get('description'):
                    desc_triggers = _re.findall(r'\"(.*?)\"', conn_def['description'])
                    trigger_phrases.extend([p.lower() for p in desc_triggers])

                if any(phrase in user_task_lower for phrase in trigger_phrases):
                    return conn_def  # Found a match
        return None

    # Guard 1: Empty plan. If a connector matches, use it.
    if not steps:
        matching_conn = find_matching_connector()
        if matching_conn:
            connector_id = matching_conn['id']
            _log(state, f"🔄 Planner: Corrected empty plan → connector_tool for '{connector_id}'")
            steps = [{
                "id": 1,
                "tool": "connector_tool",
                "args": {"connector_id": connector_id, "user_input": clean_input},
                "thought": f"Redirected: Empty plan → connector_tool. User task matches '{matching_conn['name']}' connector."
            }]

    # Guard 2: Non-empty plan. Check for individual mis-selections.
    for s in steps:
        tool = s.get("tool", "")

        # If coding_agent_tool is chosen, check if a connector could have been used instead.
        if tool == "coding_agent_tool":
            matching_conn = find_matching_connector()
            if matching_conn:
                connector_id = matching_conn['id']
                _log(state, f"🔄 Planner: Corrected coding_agent_tool → connector_tool for '{connector_id}'")
                s["tool"] = "connector_tool"
                s["args"] = {"connector_id": connector_id, "user_input": clean_input}
                s["thought"] = f"Redirected: coding_agent_tool → connector_tool. User task matches '{matching_conn['name']}' connector."
                continue  # Step corrected, move to next one

        # research_agent_tool: only allow if user EXPLICITLY asked for a full report
        if tool == "research_agent_tool" and not _is_research_report_request(user_input):
            # Redirect to web_search — it's a simple question
            query = distilled_clean or user_input
            s["tool"] = "web_search"
            s["args"] = {"query": query, "max_results": 4}
            s["thought"] = "Redirected: research_agent_tool → web_search (not an explicit report request)"
            _log(state, "🔄 Planner: Corrected research_agent_tool → web_search (simple question)")

        # rag_search with no file context + explicit report request → research_agent_tool
        elif tool == "rag_search" and not mentioned_files and not file_path and _is_research_report_request(user_input):
            mode = _detect_research_mode(user_input)
            s["tool"] = "research_agent_tool"
            s["args"] = {"user_input": user_input, "mode": mode}
            s["thought"] = f"Redirected: rag_search → research_agent_tool ({mode})"
            _log(state, f"🔄 Planner: Corrected rag_search → research_agent_tool ({mode})")

    _log(state, f"📝 Planner: Plan ready — {len(steps)} step(s).")
    for s in steps:
        tool = s.get("tool", "none")
        thought = s.get("thought", "")
        _log(state, f"   ↳ Step {s.get('id','?')}: [{tool}] {thought}")
    return {"plan": steps, "log": state["log"], "history": history}


def node_executor(state: GraphState) -> GraphState:
    plan = state.get("plan", [])
    tool_names = [s["tool"] for s in plan if s.get("tool")]
    if tool_names:
        _log(state, f"🛠️ Executor: Running tool(s): {', '.join(tool_names)}")
    else:
        _log(state, "🧠 Executor: No tools required — answering from general knowledge.")

    observations = []
    for step in plan:
        tool_name = step.get("tool")
        args      = step.get("args", {}) or {}
        if tool_name and tool_name in TOOLS:
            _log(state, f"⚙️ Executor: Calling '{tool_name}'…")
            try:
                # If calling the coding sub-agent, forward workspace event callback
                if tool_name == "coding_agent_tool":
                    from coding import tool_coding_agent as _tca
                    obs = _tca(
                        args.get("user_input", ""),
                        on_event=state.get("_on_workspace_event"),
                        connector_configs=state.get("connector_configs"),
                    )
                # If calling a connector, pass the specific env vars for that connector
                elif tool_name == "connector_tool":
                    from frontend.src.components.tools import tool_connector_tool as _tct
                    connector_id = args.get("connector_id", "")
                    connector_configs = state.get("connector_configs", {})

                    # Guardrail: Check if the connector is actually configured before running.
                    if not connector_configs or not connector_configs.get(connector_id):
                        _log(state, f"❌ Executor: Connector '{connector_id}' called but is not configured.")
                        obs = {"error": f"Connector '{connector_id}' is not configured. Please add your credentials in the Connectors settings and try again."}
                    else:
                        # The connector_configs from the frontend are structured as:
                        # { "github": { "GITHUB_TOKEN": "...", "GITHUB_USER": "..." } }
                        # We pass the inner dictionary as env_extra.
                        env_vars = connector_configs.get(connector_id, {})
                        obs = _tct(
                            connector_id=connector_id,
                            user_input=args.get("user_input", ""),
                            env_extra=env_vars
                        )
                # If calling the research sub-agent, forward log callback
                elif tool_name == "research_agent_tool":
                    from research import tool_research_agent as _tra
                    raw_result = _tra(
                        args.get("user_input", ""),
                        source_file=args.get("source_file"),
                        mode=args.get("mode"),
                        on_log=state.get("_on_log"),
                    )
                    # Flatten to a string so the executor/verifier can use it directly
                    if isinstance(raw_result, dict):
                        obs = raw_result.get("final") or raw_result.get("error") or str(raw_result)
                    else:
                        obs = str(raw_result)
                else:
                    obs = TOOLS[tool_name]["func"](args)
                _log(state, f"✅ Executor: '{tool_name}' completed successfully.")
            except Exception as exc:
                obs = {"error": f"tool_error: {exc}"}
                _log(state, f"❌ Executor: '{tool_name}' failed — {exc}")
        else:
            obs = {"note": "no_tool"}
        observations.append({"id": step.get("id"), "tool": tool_name, "args": args, "observation": obs})

    # ══ POST-OBSERVATION ROUTING ════════════════════════════════
    # Detect what we got back and route appropriately.
    # Use CONTENT checks, not just tool-name matching, so nothing slips through.

    for obs_item in observations:
        tool_name_obs = obs_item.get("tool", "")
        observation   = obs_item.get("observation")

        # ── Research agent report ────────────────────────────────
        if tool_name_obs == "research_agent_tool":
            text = observation if isinstance(observation, str) else ""
            if len(text.strip()) > 50:
                _log(state, "📝 Executor: Using research report directly.")
                return {"observations": observations, "draft": text, "final": text, "log": state["log"]}

        # ── RAG result ───────────────────────────────────────────
        if tool_name_obs == "rag_search":
            raw_chunks = ""
            if isinstance(observation, dict):
                raw_chunks = observation.get("results", "")
            elif isinstance(observation, str):
                raw_chunks = observation

            logger.info(f"RAG observation type={type(observation).__name__}, "
                        f"raw_chunks len={len(raw_chunks)}, "
                        f"has_content={'No relevant information' not in raw_chunks}")

            rag_has_content = (
                bool(raw_chunks.strip())
                and "No relevant information" not in raw_chunks
                and len(raw_chunks.strip()) > 80
            )

            if rag_has_content:
                _log(state, "📝 Executor: Found relevant content in knowledge base — synthesising…")
                synthesis_prompt = (
                    f"You are a helpful assistant answering from an uploaded document.\n\n"
                    f"USER QUESTION: {state.get('user_input', '')}\n\n"
                    f"RETRIEVED DOCUMENT EXCERPTS:\n{raw_chunks}\n\n"
                    f"INSTRUCTIONS:\n"
                    f"- Answer using ONLY the excerpts above\n"
                    f"- Be thorough and well-structured\n"
                    f"- Do NOT say 'No relevant info found'"
                )
                try:
                    draft = _llm_invoke(synthesis_prompt)
                except Exception as exc:
                    _log(state, f"⚠️ Synthesis LLM failed ({exc!r}). Using raw chunks.")
                    draft = f"Here are the relevant excerpts:\n\n{raw_chunks}"

                _log(state, "✅ Executor: Document answer ready.")
                # Set final directly → _should_reflect sees final → routes to 'approved' → skips verifier replan
                return {"observations": observations, "draft": draft, "final": draft, "log": state["log"]}

            else:
                # RAG empty → auto web search fallback
                _log(state, "⚠️ Executor: RAG empty — falling back to web search…")
                try:
                    from frontend.src.components.tools import tool_web_search as _ws
                    web_result = _ws(state.get("clean_input") or state.get("user_input", ""), max_results=5)
                    if web_result.get("results"):
                        parts = [
                            f"**{r.get('title','')}** ({r.get('href','')})\n{r.get('body','')}"
                            for r in web_result["results"]
                        ]
                        web_text = "\n\n".join(parts)
                        _log(state, "✅ Executor: Web fallback results received — synthesising…")
                        web_prompt = (
                            f"Answer this question using the web search results below.\n\n"
                            f"Question: {state.get('user_input', '')}\n\n"
                            f"Web Results:\n{web_text}\n\n"
                            f"Write a clear, well-structured answer. Cite sources inline."
                        )
                        draft = _llm_invoke(web_prompt)
                        observations.append({
                            "id": "web_fallback", "tool": "web_search",
                            "args": {}, "observation": {"results": web_text}
                        })
                        return {"observations": observations, "draft": draft, "final": draft, "log": state["log"]}
                except Exception as exc:
                    _log(state, f"⚠️ Web fallback failed: {exc!r}")

                draft = "The document was searched but no relevant content was found. Please re-upload the file to refresh its index."
                return {"observations": observations, "draft": draft, "final": draft, "log": state["log"]}

    # ── No special tool — single string obs ──────────────────────
    if len(observations) == 1 and isinstance(observations[0].get("observation"), str):
        raw = observations[0]["observation"]
        if raw and "No relevant" not in raw:
            _log(state, "📝 Executor: Using tool output directly as draft.")
            return {"observations": observations, "draft": raw, "log": state["log"]}

    # ── Detect if ANY real tool ran and returned real content ─────
    real_tool_ran = any(
        o.get("tool") and o.get("tool") not in (None, "no_tool")
        and o.get("observation") not in ({"note": "no_tool"}, None, "", {})
        for o in observations
    )

    if not real_tool_ran:
        # No tools ran — answer directly from LLM (greetings, casual, general knowledge)
        _log(state, "💬 Executor: Answering directly from knowledge…")
        try:
            draft = _llm_invoke(
                "You are a helpful, friendly AI assistant.\n"
                f"Conversation history context: {state.get('history', [])[-2:]}\n\n"
                f"User message: {state.get('user_input', '')}\n\n"
                "Respond naturally. "
                "For greetings: reply warmly. "
                "For simple factual questions: answer directly and accurately. "
                "For casual conversation: be friendly. "
                "Never say 'No relevant info found' — always give a real answer."
            )
        except Exception as exc:
            _log(state, f"⚠️ Direct LLM failed: {exc!r}")
            draft = "Hi! I'm here to help. What would you like to know?"
        return {"observations": observations, "draft": draft, "final": draft, "log": state["log"]}

    # ── Generic synthesis (tool ran but not RAG/research/web) ────
    _log(state, "📝 Executor: Synthesising draft answer…")
    context = (
        f"User Request: {state.get('user_input','')}\n"
        f"Observations: {json.dumps(observations, ensure_ascii=False)}"
    )
    try:
        draft = _llm_invoke(f"{EXECUTOR_SYS}\n\n{context}\n\nWrite the answer.")
    except Exception as exc:
        _log(state, f"⚠️ Executor: LLM failed ({exc!r}). Using raw observations.")
        draft = json.dumps(observations, ensure_ascii=False)

    return {"observations": observations, "draft": draft, "log": state["log"]}


def node_verifier(state: GraphState) -> GraphState:
    _log(state, "🔍 Verifier: Checking draft for accuracy and completeness…")

    draft = state.get("draft", "") or ""
    obs   = state.get("observations", [])

    # ── If executor already set final, skip verifier entirely ────
    if state.get("final") and len(state["final"].strip()) > 5:
        _log(state, "✅ Verifier: Answer pre-approved by executor.")
        return {"final": state["final"], "log": state["log"]}

    # Auto-approve rules
    # 1. RAG-based answer (rag_search tool used)
    # 2. Research agent answer (research_agent_tool used)
    # 3. Any non-trivial draft when reflections > 0 (stop the loop)
    tool_names = {o.get("tool") for o in obs}
    is_rag      = "rag_search"           in tool_names
    is_research = "research_agent_tool"  in tool_names
    reflections = state.get("reflections", 0)

    if (is_rag or is_research) and len(draft.strip()) > 30:
        label = "RAG" if is_rag else "Research"
        _log(state, f"✅ Verifier: {label}-based answer auto-approved.")
        return {"final": draft, "log": state["log"]}

    if reflections >= 1 and len(draft.strip()) > 30:
        _log(state, "✅ Verifier: Auto-approved after reflection (preventing loop).")
        return {"final": draft, "log": state["log"]}

    # For non-RAG answers, use LLM verifier
    prompt = (
        VERIFIER_SYS
        + "\nUser input:\n" + state.get("user_input", "")
        + "\nDraft:\n"      + draft
        + "\nObservations:\n" + json.dumps(obs, ensure_ascii=False)
    )
    try:
        raw = _llm_invoke(prompt)
    except Exception as exc:
        _log(state, f"⚠️ Verifier: LLM failed ({exc!r}). Approving draft as-is.")
        return {"final": state.get("draft",""), "log": state["log"]}

    parsed = safe_json_loads(raw)
    if isinstance(parsed,dict) and parsed.get("approved") and parsed.get("final"):
        _log(state, "✅ Verifier: Draft approved. Finalising answer.")
        return {"final": parsed["final"], "log": state["log"]}

    fb = parsed.get("feedback","needs another pass") if isinstance(parsed,dict) else "needs another pass"
    _log(state, f"❌ Verifier: Not approved — '{fb[:60]}…'. Replanning.")
    mem_add(f"verifier_feedback: {fb}", kind="feedback")
    return {"feedback": fb, "reflections": state.get("reflections",0)+1, "log": state["log"]}


def node_memory_update(state: GraphState) -> GraphState:
    _log(state, "💾 Memory: Saving interaction to long-term memory…")
    ui    = state.get("user_input","")
    final = state.get("final","")
    if ui:    mem_add(ui, kind="user")
    if final: mem_add(final, kind="agent")
    low = ui.lower()
    def _extract_name(src, key):
        return src.split(key,1)[-1].strip().strip(".?! ")
    if "my name is" in low:
        name = _extract_name(low,"my name is")
        if name: mem_add(json.dumps({"entity":"user","attribute":"name","value":name}), kind="fact")
    if "your name is" in low or "ur name is" in low:
        name = _extract_name(low," is ")
        if name: mem_add(json.dumps({"entity":"agent","attribute":"name","value":name}), kind="fact")
    if "my brother name is" in low:
        name = _extract_name(low,"my brother name is")
        if name: mem_add(json.dumps({"entity":"user's brother","attribute":"name","value":name}), kind="fact")
    _log(state, "✅ Memory: Interaction saved.")
    return {"log": state["log"]}


def finalizer(state: GraphState) -> GraphState:
    _log(state, "⚠️ Finalizer: Max reflections reached. Using best draft.")
    return {**state, "final": state.get("draft") or "[Agent had no result]"}


# ══════════════════════════════════════════════════════════════
# ROUTING
# ══════════════════════════════════════════════════════════════

def _should_reflect(state: GraphState) -> str:
    if state.get("final"):                              return "approved"
    if int(state.get("reflections",0)) >= MAX_REFLECTIONS: return "give_up"
    return "replan"

def should_plan_or_finish(state: GraphState) -> str:
    return "finish" if state.get("final") else "plan"


# ══════════════════════════════════════════════════════════════
# GRAPH
# ══════════════════════════════════════════════════════════════

def build_graph():
    wf = StateGraph(GraphState)
    wf.add_node("slash_parser",  node_slash_command_parser)
    wf.add_node("direct_answer", node_direct_answer)
    wf.add_node("planner",       node_planner)
    wf.add_node("executor",      node_executor)
    wf.add_node("verifier",      node_verifier)
    wf.add_node("finalizer",     finalizer)
    wf.add_node("memory",        node_memory_update)

    wf.set_entry_point("slash_parser")

    def should_continue_planning(state: GraphState) -> str:
        """If slash_parser created a plan, execute it. Otherwise, continue to normal flow."""
        return "execute" if state.get("plan") else "plan"

    wf.add_conditional_edges(
        "slash_parser",
        should_continue_planning,
        {"execute": "executor", "plan": "direct_answer"}
    )

    wf.add_conditional_edges("direct_answer", should_plan_or_finish, {"finish": "memory", "plan": "planner"})
    wf.add_edge("planner","executor")
    wf.add_edge("executor","verifier")
    wf.add_conditional_edges("verifier", _should_reflect, {"replan":"planner","approved":"memory","give_up":"finalizer"})
    wf.add_edge("finalizer","memory")
    wf.add_edge("memory", END)
    return wf.compile()


# ══════════════════════════════════════════════════════════════
# PUBLIC ENTRY POINT
# ══════════════════════════════════════════════════════════════

def run_agent_once(
    user_input:          str,
    history:             List[Any],
    file_path:           Optional[str] = None,
    connector_configs:   Optional[Dict[str, Any]] = None,
    on_log:              Optional[Callable[[str], None]] = None,
    on_workspace_event:  Optional[Callable[[Dict], None]] = None,
) -> Dict[str, Any]:
    """
    on_log              : callback fired for each agent log line (→ side panel)
    on_workspace_event  : callback fired for each workspace event (file_op / stdout / etc.)
    """
    mentioned_files = _parse_mentions(user_input)
    graph  = build_graph()
    state: GraphState = {
        "user_input":          user_input,
        "clean_input":         _strip_mentions(user_input),
        "mentioned_files":     mentioned_files,
        "reflections":         0,
        "log":                 [],
        "history":             history,
        "file_path":           file_path,
        "connector_configs":   connector_configs,
        "_on_log":             on_log,
        "_on_workspace_event": on_workspace_event,
    }
    return graph.invoke(state)
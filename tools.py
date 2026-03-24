# tools.py
"""
All agent tools, including the new sandboxed workspace tools.
Every tool that performs a visible action emits structured events
through an optional  on_event(event_dict)  callback so the frontend
can render live agentic behaviour (create/edit/run/server/output).
"""
from __future__ import annotations
import os
import ast
import re
from typing import Dict, Any, List, Optional, Callable

from langchain_chroma import Chroma
from ddgs import DDGS

from core.config import logger


from core.config import _embedding_fn, RAG_PERSIST_DIR, RAG_COLLECTION
from sandbox import (
    ws_write_file, ws_read_file, ws_list_files, ws_delete_file,
    ws_run_code, ws_run_code_streaming,
    ws_start_server, ws_stop_server, ws_list_servers,
    ws_install_package, ws_reset,
)


# ══════════════════════════════════════════════════════════════
# GLOBAL EVENT CALLBACK
# Set by the coding agent before executing a plan so events are
# forwarded to the SSE stream in real time.
# ══════════════════════════════════════════════════════════════

_on_event: Optional[Callable[[Dict[str, Any]], None]] = None

def set_event_callback(cb: Optional[Callable]) -> None:
    global _on_event
    _on_event = cb

def _emit(event: Dict[str, Any]) -> None:
    if callable(_on_event):
        try:
            _on_event(event)
        except Exception:
            pass


# ══════════════════════════════════════════════════════════════
# WEB SEARCH
# ══════════════════════════════════════════════════════════════

def tool_web_search(query: str, max_results: int = 3) -> Dict[str, Any]:
    """Search the web for a given query."""
    results: List[Dict[str, Any]] = []
    try:
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                results.append({"title": r.get("title"), "href": r.get("href"), "body": r.get("body")})
    except Exception as e:
        return {"error": f"search_failed: {e}"}
    return {"results": results}


# ══════════════════════════════════════════════════════════════
# CALCULATOR
# ══════════════════════════════════════════════════════════════

class _MathVisitor(ast.NodeVisitor):
    allowed_nodes = (
        ast.Expression, ast.BinOp, ast.UnaryOp, ast.Num, ast.Load,
        ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Mod, ast.Pow,
        ast.USub, ast.UAdd, ast.FloorDiv, ast.Constant,
    )
    def visit(self, node):
        if not isinstance(node, self.allowed_nodes):
            raise ValueError(f"disallowed expression: {type(node).__name__}")
        return super().visit(node)

def tool_calculator(expression: str) -> Dict[str, Any]:
    """Evaluate a safe arithmetic expression."""
    try:
        node  = ast.parse(expression, mode="eval")
        _MathVisitor().visit(node)
        value = eval(compile(node, "<calc>", "eval"), {"__builtins__": {}}, {})
        return {"ok": True, "result": value}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# ══════════════════════════════════════════════════════════════
# SANDBOXED WORKSPACE FILE TOOLS
# ══════════════════════════════════════════════════════════════

def tool_write_file(file_path: str, content: str) -> Dict[str, Any]:
    """
    Write (create or edit) a file inside workspace/.
    Emits a live event so the frontend can show the file being created.
    """
    _emit({
        "type":    "file_op",
        "op":      "write",
        "path":    file_path,
        "preview": content[:200] + ("…" if len(content) > 200 else ""),
    })
    result = ws_write_file(file_path, content)
    _emit({
        "type":   "file_op_done",
        "op":     result.get("action", "write"),
        "path":   file_path,
        "status": result["status"],
    })
    return result


def tool_read_file(file_path: str) -> Dict[str, Any]:
    """Read a file from workspace/."""
    _emit({"type": "file_op", "op": "read", "path": file_path})
    return ws_read_file(file_path)


def tool_list_files(subpath: str = "") -> Dict[str, Any]:
    """List files in workspace/ or a sub-directory."""
    return ws_list_files(subpath)


def tool_delete_file(file_path: str) -> Dict[str, Any]:
    """Delete a file from workspace/."""
    _emit({"type": "file_op", "op": "delete", "path": file_path})
    return ws_delete_file(file_path)


# ══════════════════════════════════════════════════════════════
# CODE EXECUTION  (streaming live output)
# ══════════════════════════════════════════════════════════════

def tool_run_code(command: str, timeout: int = 30) -> Dict[str, Any]:
    """
    Execute a shell command inside workspace/ with live output streaming.
    stdout lines are emitted as events in real time.
    Returns the complete { status, stdout, stderr, exit_code } when done.
    """
    _emit({"type": "run_start", "command": command})
    stdout_lines: List[str] = []
    stderr_lines: List[str] = []

    for event in ws_run_code_streaming(command, timeout=timeout):
        if event["type"] == "stdout":
            stdout_lines.append(event["line"])
            _emit({"type": "stdout", "line": event["line"]})
        elif event["type"] == "stderr":
            stderr_lines.append(event["line"])
            _emit({"type": "stderr", "line": event["line"]})
        elif event["type"] == "done":
            _emit({
                "type":      "run_done",
                "exit_code": event["exit_code"],
                "duration":  event["duration"],
            })

    stdout = "\n".join(stdout_lines)
    stderr = "\n".join(stderr_lines)
    return {
        "status":  "success" if not stderr_lines else "error",
        "stdout":  stdout,
        "stderr":  stderr,
        "output":  stdout,      # backwards compat alias
    }


# ══════════════════════════════════════════════════════════════
# SERVER MANAGEMENT
# ══════════════════════════════════════════════════════════════

def tool_start_server(command: str, port: int = 5001, label: str = "") -> Dict[str, Any]:
    """
    Start a long-running server (Flask, Node, etc.) inside workspace/.
    The server is accessible at http://localhost:<port>.
    """
    _emit({"type": "server_start", "command": command, "port": port})
    result = ws_start_server(command, port, label)
    _emit({"type": "server_started" if result["status"] == "started" else "server_error", **result})
    return result


def tool_stop_server(port: int) -> Dict[str, Any]:
    """Stop a running server."""
    _emit({"type": "server_stop", "port": port})
    return ws_stop_server(port)


def tool_list_servers() -> Dict[str, Any]:
    """List all running servers started by the agent."""
    return ws_list_servers()


# ══════════════════════════════════════════════════════════════
# PACKAGE INSTALLATION
# ══════════════════════════════════════════════════════════════

def tool_install_package(package: str) -> Dict[str, Any]:
    """pip install a Python package inside the sandbox."""
    _emit({"type": "install", "package": package})
    result = ws_install_package(package)
    _emit({"type": "install_done", "package": package, "status": result["status"]})
    return result


# ══════════════════════════════════════════════════════════════
# RAG SEARCH
# ══════════════════════════════════════════════════════════════

def _rag_get_docs_for_file(rag_db, fname: str) -> list:
    """
    Fetch ALL stored chunks for a specific filename using direct Chroma
    collection access — bypasses vector search filters entirely, so it works
    regardless of how the source path was stored (backslash / forward-slash,
    with or without filename metadata).
    Returns a list of (doc_id, text, metadata) tuples sorted by chunk_index.
    """
    try:
        col    = rag_db._collection
        result = col.get(include=["documents", "metadatas"])
        ids    = result.get("ids", [])
        docs   = result.get("documents", [])
        metas  = result.get("metadatas", [])

        matched = []
        for doc_id, text, meta in zip(ids, docs, metas):
            if not text or not text.strip():
                continue
            src  = meta.get("source", "")
            fn   = meta.get("filename", "")
            # Match by filename field OR basename of source (handles all path variants)
            src_base = os.path.basename(src.replace("\\", "/"))
            if fname == fn or fname == src_base or fname in src:
                matched.append((meta.get("chunk_index", 0), text, meta))

        # Sort by chunk_index so we get coherent reading order
        matched.sort(key=lambda x: x[0])
        return matched
    except Exception as e:
        logger.warning(f"Direct collection get failed: {e}")
        return []


def tool_rag_search(query: str, source_file: str | None = None) -> Dict[str, Any]:
    """
    RAG search with 4-level fallback:
      1. Vector search with filename filter   (fast, new chunks)
      2. Vector search with source= variants  (old chunks, both path separators)
      3. Direct collection scan by basename   (nuclear fallback — always works)
      4. Unfiltered vector search             (no source_file given)
    Steps 1-2 use MMR for diverse results; step 3 ranks by embedding similarity.
    """
    try:
        rag_db = Chroma(
            persist_directory=RAG_PERSIST_DIR,
            embedding_function=_embedding_fn,
            collection_name=RAG_COLLECTION,
        )

        def _vsearch(flt: Dict | None, k: int = 6) -> list:
            """Vector search (MMR → similarity fallback)."""
            try:
                if flt:
                    return rag_db.max_marginal_relevance_search(
                        query, filter=flt, k=k, fetch_k=k*3, lambda_mult=0.7
                    )
                return rag_db.max_marginal_relevance_search(
                    query, k=k, fetch_k=k*3, lambda_mult=0.7
                )
            except Exception:
                sk: Dict[str, Any] = {"k": k}
                if flt:
                    sk["filter"] = flt
                return rag_db.similarity_search(query, **sk)

        docs: list = []

        if source_file and source_file.lower() not in ("none", "null", ""):
            fname = os.path.basename(source_file)
            fwd   = "uploads/" + fname
            back  = "uploads\\" + fname

            # ── Level 1: filename metadata ──────────────────────
            docs = _vsearch({"filename": {"$eq": fname}})
            logger.info(f"RAG [filename={fname}]: {len(docs)} results")

            # ── Level 2a: source forward-slash ──────────────────
            if not docs:
                docs = _vsearch({"source": {"$eq": fwd}})
                logger.info(f"RAG [source={fwd}]: {len(docs)} results")

            # ── Level 2b: source backslash ──────────────────────
            if not docs:
                docs = _vsearch({"source": {"$eq": back}})
                logger.info(f"RAG [source(\\)={back}]: {len(docs)} results")

            # ── Level 3: direct collection scan ─────────────────
            # Bypasses ALL filter/path issues — reads raw SQLite, matches by basename
            if not docs:
                logger.warning(f"RAG: vector filters all failed for '{fname}' — scanning collection directly")
                raw_matched = _rag_get_docs_for_file(rag_db, fname)
                if raw_matched:
                    # Re-rank the matched chunks by embedding similarity to the query
                    from langchain_core.documents import Document as _Doc
                    candidate_docs = [
                        _Doc(page_content=text, metadata=meta)
                        for _, text, meta in raw_matched
                    ]
                    # Score by simple keyword overlap if embedding fails
                    try:
                        q_emb   = _embedding_fn.embed_query(query)
                        c_embs  = _embedding_fn.embed_documents([d.page_content for d in candidate_docs])
                        import math
                        def cosine(a, b):
                            dot  = sum(x*y for x,y in zip(a,b))
                            norm = math.sqrt(sum(x*x for x in a)) * math.sqrt(sum(x*x for x in b))
                            return dot/norm if norm else 0
                        scored = sorted(
                            zip(candidate_docs, c_embs),
                            key=lambda p: cosine(q_emb, p[1]),
                            reverse=True,
                        )
                        docs = [d for d, _ in scored[:6]]
                    except Exception:
                        docs = candidate_docs[:6]
                    logger.info(f"RAG direct scan [{fname}]: {len(raw_matched)} chunks, returning top {len(docs)}")

        # ── Level 4: unfiltered ──────────────────────────────────
        if not docs:
            if source_file:
                logger.warning("RAG: all file-specific methods failed, falling back to unfiltered")
            docs = _vsearch(None)

        if not docs:
            return {"results": "No relevant information found in the knowledge base."}

        # ── Format results ───────────────────────────────────────
        parts = []
        for i, doc in enumerate(docs, 1):
            meta     = doc.metadata
            page     = meta.get("page", "")
            src      = meta.get("filename") or os.path.basename(
                meta.get("source", "document").replace("\\", "/")
            )
            page_str = f" | p.{int(page)+1}" if page != "" else ""
            parts.append(f"[Chunk {i} | {src}{page_str}]\n{doc.page_content.strip()}")

        result_text = "\n\n---\n\n".join(parts)
        logger.info(f"RAG returning {len(docs)} chunks, first 120 chars: {result_text[:120]!r}")
        return {
            "results":     result_text,
            "chunk_count": len(docs),
            "source_file": source_file or "all files",
        }

    except Exception as e:
        logger.error(f"RAG search error: {e}")
        return {"error": f"rag_search_failed: {e}"}


# ══════════════════════════════════════════════════════════════
# CODING AGENT TOOL  (delegates to coding.py)
# ══════════════════════════════════════════════════════════════

def _get_coding_agent():
    from coding import tool_coding_agent
    return tool_coding_agent


def _get_research_agent():
    from research import tool_research_agent
    return tool_research_agent


# ══════════════════════════════════════════════════════════════
# TOOL REGISTRY
# ══════════════════════════════════════════════════════════════

TOOLS: Dict[str, Dict[str, Any]] = {

    # ── Web & Math ──────────────────────────────────────────
    "web_search": {
        "desc": "Search the web for general information, current events, or real-world facts.",
        "func": lambda a: tool_web_search(a.get("query",""), int(a.get("max_results",3))),
    },
    "calculator": {
        "desc": "Evaluate arithmetic expressions.",
        "func": lambda a: tool_calculator(a.get("expression","")),
    },

    # ── RAG / Knowledge base ────────────────────────────────
    "rag_search": {
        "desc": (
            "Search the uploaded knowledge base. "
            "Use source_file='filename.ext' to target a specific file."
        ),
        "func": lambda a: tool_rag_search(a.get("query",""), a.get("source_file")),
    },

    # ── Workspace: files ────────────────────────────────────
    "write_file": {
        "desc": (
            "Create or overwrite a file inside workspace/. "
            "Args: file_path (relative), content (string)."
        ),
        "func": lambda a: tool_write_file(a.get("file_path",""), a.get("content", a.get("text",""))),
    },
    "read_file": {
        "desc": "Read a file from workspace/. Args: file_path (relative).",
        "func": lambda a: tool_read_file(a.get("file_path","")),
    },
    "list_files": {
        "desc": "List files in workspace/ or a sub-directory.",
        "func": lambda a: tool_list_files(a.get("subpath","")),
    },
    "delete_file": {
        "desc": "Delete a file from workspace/. Args: file_path (relative).",
        "func": lambda a: tool_delete_file(a.get("file_path","")),
    },

    # ── Workspace: execution ────────────────────────────────
    "run_code": {
        "desc": (
            "Execute a shell command inside workspace/ with live output streaming. "
            "All paths are relative to workspace/. "
            "Examples: 'python app.py', 'node index.js', 'pytest test_app.py'. "
            "Args: command (string), timeout (int, optional, default 30)."
        ),
        "func": lambda a: tool_run_code(a.get("command",""), int(a.get("timeout",30))),
    },

    # ── Workspace: servers ──────────────────────────────────
    "start_server": {
        "desc": (
            "Start a long-running server inside workspace/ (Flask, Express, etc.). "
            "The server runs at http://localhost:<port>. "
            "Args: command (string), port (int), label (string, optional)."
        ),
        "func": lambda a: tool_start_server(
            a.get("command",""), int(a.get("port",5001)), a.get("label","")
        ),
    },
    "stop_server": {
        "desc": "Stop a running server by port. Args: port (int).",
        "func": lambda a: tool_stop_server(int(a.get("port",5001))),
    },
    "list_servers": {
        "desc": "List all servers currently running in the sandbox.",
        "func": lambda a: tool_list_servers(),
    },

    # ── Workspace: packages ─────────────────────────────────
    "install_package": {
        "desc": "pip install a Python package in the sandbox. Args: package (string).",
        "func": lambda a: tool_install_package(a.get("package","")),
    },

    # ── Coding agent (sub-agent) ────────────────────────────
    "coding_agent_tool": {
        "desc": (
            "Specialized coding sub-agent that plans, writes, executes and debugs code. "
            "Use for any coding task. Args: user_input (string)."
        ),
        "func": lambda a: _get_coding_agent()(a.get("user_input","")),
    },

    # ── Research agent (sub-agent) ──────────────────────────
    "research_agent_tool": {
        "desc": (
            "Specialized research sub-agent for in-depth investigation of topics. "
            "Modes: questions | summary | deep | compare | timeline | critique. "
            "Searches the web AND uploaded documents. Saves a Markdown report to workspace/. "
            "Args: user_input (string), source_file (string, optional filename), "
            "mode (string, optional — one of the modes above)."
        ),
        "func": lambda a: _get_research_agent()(
            a.get("user_input", ""),
            source_file=a.get("source_file"),
            mode=a.get("mode"),
        ),
    },
}
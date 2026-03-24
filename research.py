# research.py
"""
Enhanced Research Agent
========================
Modes:
  questions   → generates 5 targeted research questions
  summary     → concise document/topic summary
  deep        → full multi-source research report with citations
  compare     → compare two topics / documents side-by-side
  timeline    → chronological overview of a topic
  critique    → critical analysis & counter-arguments

All modes:
  - support @mention file context (RAG)
  - stream logs via on_log callback (same pattern as agent.py)
  - save output to workspace/ as Markdown
  - integrate with main agent.py via TOOLS registry
"""
from __future__ import annotations

import os
import re
import time
import random
import logging
from typing import TypedDict, List, Dict, Any, Optional, Callable

from langchain_cerebras import ChatCerebras
from langchain_chroma import Chroma
from langgraph.graph import StateGraph, END

from core.config import _embedding_fn, RAG_PERSIST_DIR, RAG_COLLECTION
from tools import tool_web_search, tool_write_file

logger = logging.getLogger(__name__)

# ══════════════════════════════════════════════════════════════
# LLM
# ══════════════════════════════════════════════════════════════

_research_llm = ChatCerebras(
    model=os.environ.get("RESEARCH_MODEL", "qwen-3-235b-a22b-instruct-2507"),
    temperature=0.3,
    api_key=os.getenv("API_KEY"),
    max_tokens=4000,
)


def _llm(prompt: str, retries: int = 3, base_delay: float = 1.5) -> str:
    """Invoke LLM with exponential-backoff retry on transient errors."""
    last = None
    for attempt in range(retries):
        try:
            return _research_llm.invoke(prompt).content.strip()
        except Exception as exc:
            last = exc
            err = str(exc).lower()
            if not any(k in err for k in ["429","503","529","rate limit","timeout","try again"]):
                raise
            delay = base_delay * (2 ** attempt) + random.uniform(0, 0.4)
            logger.warning(f"Research LLM transient error (attempt {attempt+1}): {exc!r}. Retry in {delay:.1f}s")
            time.sleep(delay)
    raise last  # type: ignore


# ══════════════════════════════════════════════════════════════
# RAG HELPER
# ══════════════════════════════════════════════════════════════

def _rag_search(query: str, source_file: Optional[str] = None, k: int = 5) -> str:
    """Search the knowledge base, return formatted chunk text."""
    try:
        rag_db = Chroma(
            embedding_function=_embedding_fn,
            persist_directory=RAG_PERSIST_DIR,
            collection_name=RAG_COLLECTION,
        )
        kwargs: Dict[str, Any] = {"k": k}
        if source_file:
            fname = os.path.basename(source_file)
            kwargs["filter"] = {"filename": {"$eq": fname}}
        try:
            docs = rag_db.max_marginal_relevance_search(
                query, fetch_k=k * 3, lambda_mult=0.7, **kwargs
            )
        except Exception:
            docs = rag_db.similarity_search(query, **kwargs)

        if not docs and source_file:
            docs = rag_db.similarity_search(query, k=k)

        if not docs:
            return ""

        parts = []
        for i, doc in enumerate(docs, 1):
            page = doc.metadata.get("page", "")
            fname = doc.metadata.get("filename", "document")
            page_str = f" p.{int(page)+1}" if page != "" else ""
            parts.append(f"[{fname}{page_str}] {doc.page_content.strip()}")
        return "\n\n".join(parts)
    except Exception as e:
        logger.error(f"RAG search error in research agent: {e}")
        return ""


def _web_search(query: str, max_results: int = 4) -> str:
    """Run web search, return formatted results."""
    result = tool_web_search(query, max_results)
    if "error" in result or not result.get("results"):
        return ""
    parts = []
    for r in result["results"]:
        title = r.get("title", "")
        url   = r.get("href", "")
        body  = r.get("body", "")
        parts.append(f"**{title}** ({url})\n{body}")
    return "\n\n".join(parts)


# ══════════════════════════════════════════════════════════════
# STATE
# ══════════════════════════════════════════════════════════════

VALID_MODES = {"questions", "summary", "deep", "compare", "timeline", "critique"}

class ResearchState(TypedDict, total=False):
    user_input:   str
    source_file:  Optional[str]
    mode:         str                  # detected or forced mode
    forced_mode:  Optional[str]        # caller can force a mode
    questions:    List[str]
    findings:     List[Dict[str, Any]] # [{question, web, rag, answer}]
    citations:    List[str]
    draft:        str
    final:        str
    log:          List[str]
    saved_path:   Optional[str]
    _on_log:      Optional[Callable]


# ══════════════════════════════════════════════════════════════
# LOG HELPER
# ══════════════════════════════════════════════════════════════

def _log(state: ResearchState, msg: str) -> None:
    state.setdefault("log", []).append(msg)
    cb = state.get("_on_log")
    if callable(cb):
        try:
            cb(msg)
        except Exception:
            pass


# ══════════════════════════════════════════════════════════════
# NODE 1 — INTENT DETECTOR
# detects mode and validates source_file
# ══════════════════════════════════════════════════════════════

def node_intent_detector(state: ResearchState) -> Dict:
    _log(state, "🔍 Research: Detecting mode and intent…")

    # Caller can force a mode (e.g. from the TOOLS registry)
    if state.get("forced_mode") and state["forced_mode"] in VALID_MODES:
        mode = state["forced_mode"]
        _log(state, f"⚙️ Research: Mode forced → {mode}")
        return {"mode": mode, "log": state["log"]}

    query = state["user_input"]
    prompt = f"""Classify this research request into exactly ONE mode:

  questions  → user wants research questions to investigate a topic
  summary    → user wants a concise summary of a topic or document
  deep       → user wants a full, in-depth research report
  compare    → user wants two things compared or contrasted
  timeline   → user wants a chronological history of a topic
  critique   → user wants critical analysis, counter-arguments, weaknesses

Request: "{query}"

Reply with ONLY the single mode word (no punctuation, no explanation)."""

    raw = _llm(prompt).lower().strip().split()[0]
    mode = raw if raw in VALID_MODES else "deep"
    _log(state, f"⚙️ Research: Mode detected → {mode}")
    return {"mode": mode, "log": state["log"]}


# ══════════════════════════════════════════════════════════════
# NODE 2 — QUESTION GENERATOR
# always runs — produces 5 targeted research questions
# ══════════════════════════════════════════════════════════════

def node_question_generator(state: ResearchState) -> Dict:
    _log(state, "❓ Research: Generating research questions…")

    query       = state["user_input"]
    source_file = state.get("source_file")
    mode        = state.get("mode", "deep")

    # Mode-specific question framing
    mode_instruction = {
        "questions":  "Generate 5 open-ended investigative questions.",
        "summary":    "Generate 3 questions that identify the key points to summarise.",
        "deep":       "Generate 5 specific research questions covering different aspects.",
        "compare":    "Generate 4 questions that highlight similarities and differences.",
        "timeline":   "Generate 4 chronological questions tracing development over time.",
        "critique":   "Generate 4 critical questions exposing weaknesses, gaps, and counter-arguments.",
    }.get(mode, "Generate 5 research questions.")

    # Include RAG context if a file is provided
    context_block = ""
    if source_file:
        rag_text = _rag_search(query, source_file, k=4)
        if rag_text:
            context_block = f"\n\nDocument Context:\n{rag_text[:3000]}"
            _log(state, f"📎 Research: Using document context from '{os.path.basename(source_file)}'")

    prompt = f"""You are an expert research analyst.

Topic / Request: {query}{context_block}

Task: {mode_instruction}

Rules:
- Each question must explore a DIFFERENT angle
- Be specific, not generic
- No overlapping questions

Return ONLY a numbered list. One question per line."""

    response = _llm(prompt)
    questions = [
        re.sub(r'^[\d\.\-\*\s]+', '', q).strip()
        for q in response.splitlines()
        if q.strip() and len(q.strip()) > 10
    ][:5]

    _log(state, f"✅ Research: Generated {len(questions)} questions")
    return {"questions": questions, "log": state["log"]}


# ══════════════════════════════════════════════════════════════
# NODE 3 — MULTI-SOURCE EXECUTOR
# web search + RAG per question, with citations
# ══════════════════════════════════════════════════════════════

def node_executor(state: ResearchState) -> Dict:
    questions   = state.get("questions", [])
    source_file = state.get("source_file")
    mode        = state.get("mode", "deep")
    findings    = []
    citations   = []

    _log(state, f"🛠️ Research: Investigating {len(questions)} question(s) from web + documents…")

    for idx, question in enumerate(questions, 1):
        _log(state, f"🔎 Research: [{idx}/{len(questions)}] {question[:70]}…")

        # ── Web search ───────────────────────────────────────────
        web_text = _web_search(question, max_results=4)
        if web_text:
            # Extract URLs for citations
            urls = re.findall(r'\(https?://[^\)]+\)', web_text)
            citations.extend(u.strip("()") for u in urls)

        # ── RAG (document) ───────────────────────────────────────
        rag_text = _rag_search(question, source_file, k=4) if source_file else ""

        # ── Synthesise answer ────────────────────────────────────
        sources_block = ""
        if web_text:
            sources_block += f"### Web Sources\n{web_text}\n\n"
        if rag_text:
            sources_block += f"### Document Excerpts\n{rag_text}\n\n"
        if not sources_block:
            sources_block = "No external sources available — use your knowledge."

        answer_prompt = f"""Answer this research question using the sources below.

Question: {question}

Sources:
{sources_block}

Instructions:
- Be precise and evidence-based
- Cite sources inline like [Source: title or URL]
- 2–4 paragraphs
- Do NOT invent facts not present in sources"""

        answer = _llm(answer_prompt)
        findings.append({
            "question": question,
            "answer":   answer,
            "has_web":  bool(web_text),
            "has_rag":  bool(rag_text),
        })

    _log(state, "📝 Research: Synthesising full report…")
    return {
        "findings":  findings,
        "citations": list(dict.fromkeys(citations)),  # deduplicate
        "log":       state["log"],
    }


# ══════════════════════════════════════════════════════════════
# NODE 4 — REPORT WRITER
# builds mode-specific structured report
# ══════════════════════════════════════════════════════════════

_REPORT_TEMPLATES = {
    "deep": """
Write a comprehensive research report with these sections:

# {title}

## Executive Summary
## Introduction
## Key Findings
{findings_block}
## Research Gaps & Limitations
## Future Research Directions
## Conclusion
## References
{citations_block}
""",
    "summary": """
Write a clear, structured summary with:

# Summary: {title}

## Key Points
## Main Arguments / Findings
## Takeaways
""",
    "compare": """
Write a comparison report with:

# Comparison: {title}

## Overview
## Similarities
## Differences
## Strengths & Weaknesses of Each
## Verdict / Recommendation
## References
{citations_block}
""",
    "timeline": """
Write a chronological research report:

# Timeline: {title}

## Overview
## Historical Development (ordered chronologically)
## Key Milestones
## Current State
## Future Outlook
## References
{citations_block}
""",
    "critique": """
Write a critical analysis:

# Critical Analysis: {title}

## Overview
## Core Arguments / Claims
## Strengths
## Weaknesses & Limitations
## Counter-Arguments
## Balanced Assessment
## References
{citations_block}
""",
}


def node_report_writer(state: ResearchState) -> Dict:
    findings  = state.get("findings", [])
    citations = state.get("citations", [])
    mode      = state.get("mode", "deep")
    query     = state["user_input"]

    findings_block = "\n".join(
        f"### Q{i}: {f['question']}\n{f['answer']}\n"
        for i, f in enumerate(findings, 1)
    )

    citations_block = "\n".join(f"- {c}" for c in citations[:20]) or "- Web search results"
    template = _REPORT_TEMPLATES.get(mode, _REPORT_TEMPLATES["deep"])

    prompt = f"""You are an expert research writer.

{template.format(
    title=query[:80],
    findings_block=findings_block,
    citations_block=citations_block,
)}

Research Data to incorporate:
{findings_block}

Write the complete report now. Use markdown formatting.
Be thorough, professional, and cite sources where relevant."""

    draft = _llm(prompt)
    _log(state, "✅ Research: Report written.")
    return {"draft": draft, "log": state["log"]}


# ══════════════════════════════════════════════════════════════
# NODE 5 — FINALISER + SAVE
# verifies quality, adds metadata, saves to workspace/
# ══════════════════════════════════════════════════════════════

def node_finaliser(state: ResearchState) -> Dict:
    draft = state.get("draft", "")
    mode  = state.get("mode", "deep")

    if mode == "questions":
        # Questions mode — return questions directly
        questions = state.get("questions", [])
        final = "## Research Questions\n\n" + "\n".join(
            f"{i}. {q}" for i, q in enumerate(questions, 1)
        )
    elif not draft:
        _log(state, "❌ Research: Report generation failed.")
        return {"final": "Research failed — no content generated.", "log": state["log"]}
    else:
        # Add header metadata
        source_info = ""
        if state.get("source_file"):
            source_info = f"\n> 📎 Source document: `{os.path.basename(state['source_file'])}`"
        final = (
            f"> 🔬 Research Mode: **{mode.upper()}**  "
            f"| 📊 Sources: {sum(1 for f in state.get('findings',[]) if f.get('has_web'))} web"
            f" + {sum(1 for f in state.get('findings',[]) if f.get('has_rag'))} document"
            f"{source_info}\n\n"
            + draft
        )

    # Save to workspace as markdown
    safe_title = re.sub(r'[^\w\-]', '_', state['user_input'][:40]).strip('_')
    filename   = f"research_{safe_title}_{mode}.md"
    save_result = tool_write_file(filename, final)
    saved_path = save_result.get("path", filename) if save_result.get("status") == "success" else None

    if saved_path:
        _log(state, f"💾 Research: Report saved → workspace/{saved_path}")

    _log(state, "✅ Research: Complete.")
    return {"final": final, "saved_path": saved_path, "log": state["log"]}


# ══════════════════════════════════════════════════════════════
# GRAPH
# ══════════════════════════════════════════════════════════════

def _build_graph():
    wf = StateGraph(ResearchState)

    wf.add_node("intent",    node_intent_detector)
    wf.add_node("questions", node_question_generator)
    wf.add_node("executor",  node_executor)
    wf.add_node("writer",    node_report_writer)
    wf.add_node("finalise",  node_finaliser)

    wf.set_entry_point("intent")
    wf.add_edge("intent", "questions")

    # Questions-only mode skips executor + writer
    wf.add_conditional_edges(
        "questions",
        lambda s: "skip" if s.get("mode") == "questions" else "execute",
        {"skip": "finalise", "execute": "executor"},
    )

    wf.add_edge("executor", "writer")
    wf.add_edge("writer",   "finalise")
    wf.add_edge("finalise", END)

    return wf.compile()


# ══════════════════════════════════════════════════════════════
# PUBLIC ENTRY POINT
# ══════════════════════════════════════════════════════════════

def tool_research_agent(
    user_input:  str,
    source_file: Optional[str]   = None,
    mode:        Optional[str]   = None,   # force a mode (skip detection)
    on_log:      Optional[Callable[[str], None]] = None,
) -> Dict[str, Any]:
    """
    Run the enhanced research agent.

    Parameters
    ----------
    user_input  : Research topic or question
    source_file : Optional path to an uploaded file (enables RAG)
    mode        : Force one of: questions | summary | deep | compare | timeline | critique
    on_log      : Callback for real-time log streaming (same pattern as main agent)

    Returns
    -------
    {
      status:     "success" | "error",
      mode:       str,
      final:      str,           # formatted markdown report
      questions:  List[str],     # always present
      citations:  List[str],
      saved_path: str | None,    # workspace/ path where report was saved
      log:        List[str],
    }
    """
    graph = _build_graph()
    state: ResearchState = {
        "user_input":  user_input,
        "source_file": source_file,
        "forced_mode": mode,
        "mode":        "",
        "questions":   [],
        "findings":    [],
        "citations":   [],
        "draft":       "",
        "final":       "",
        "log":         [],
        "saved_path":  None,
        "_on_log":     on_log,
    }
    try:
        result = graph.invoke(state)
        return {
            "status":     "success",
            "mode":       result.get("mode", ""),
            "final":      result.get("final", ""),
            "questions":  result.get("questions", []),
            "citations":  result.get("citations", []),
            "saved_path": result.get("saved_path"),
            "log":        result.get("log", []),
        }
    except Exception as exc:
        logger.error(f"Research agent error: {exc}")
        return {"status": "error", "error": str(exc), "log": state.get("log", [])}
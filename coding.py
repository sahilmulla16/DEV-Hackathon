"""
coding.py  —  Sandboxed Coding Agent (Enhanced)
=================================================
- All coding agent files go into  workspace/coding/
- Research agent files go into    workspace/research/
- Always: writes code → explains → runs → starts server if web app
- Supports Python, JavaScript/Node, React (Vite), Bash
"""
from __future__ import annotations

import json
import os
import re
import time
import random
from typing import TypedDict, List, Dict, Any, Optional, Callable

from langgraph.graph import StateGraph, END
from langchain_cerebras import ChatCerebras

import tools as _tools_module
from tools import TOOLS
from sandbox import BASE_DIR

# ── Subdirectory constants ──────────────────────────────────────
CODING_DIR   = "coding"
RESEARCH_DIR = "research"

for _d in (BASE_DIR / CODING_DIR, BASE_DIR / RESEARCH_DIR):
    _d.mkdir(parents=True, exist_ok=True)

# ── LLM ────────────────────────────────────────────────────────
_coding_llm = ChatCerebras(
    model="qwen-3-235b-a22b-instruct-2507", temperature=0.2,
    api_key=os.getenv("API_KEY"), max_tokens=6000, top_p=0.8,
)

def _llm_invoke(prompt: str, retries: int = 3, base_delay: float = 1.5) -> str:
    last = None
    for attempt in range(retries):
        try:
            return _coding_llm.invoke(prompt).content.strip()
        except Exception as exc:
            last = exc
            if not any(k in str(exc).lower() for k in ["server error","503","529","rate limit","timeout","try again"]):
                raise
            time.sleep(base_delay * (2 ** attempt) + random.uniform(0, 0.4))
    raise last

# ══════════════════════════════════════════════════════════════
# STATE
# ══════════════════════════════════════════════════════════════

class CodingState(TypedDict, total=False):
    user_input:   str
    subdir:       str
    plan:         List[Dict[str, Any]]
    observations: List[Dict[str, Any]]
    events:       List[Dict[str, Any]]
    draft:        str
    final:        str
    retries:      int
    _on_event:    Optional[Callable]

CODING_TOOL_NAMES = [
    "write_file","read_file","list_files","delete_file",
    "run_code","start_server","stop_server","install_package",
]
_TOOL_DOCS = "\n".join(
    f"  {n}: {TOOLS[n]['desc']}" for n in CODING_TOOL_NAMES if n in TOOLS
)

# ══════════════════════════════════════════════════════════════
# PLANNER PROMPT
# ══════════════════════════════════════════════════════════════

_PLANNER_PROMPT = """\
You are an expert AI coding agent. All your files MUST go in workspace/{subdir}/.

WORKSPACE RULES:
- Every file_path must start with "{subdir}/" e.g. "{subdir}/app.py"
- run_code commands are run from workspace root: "python {subdir}/app.py"
- For React/Vite: create in "{subdir}/app/", run "npm install" then "npm run dev -- --port 5001"
- install_package BEFORE any import of third-party libs
- ALWAYS run/test code after writing it
- For any web app (Flask, FastAPI, Express, React): use start_server so user can visit it

AVAILABLE TOOLS:
{tool_docs}

USER REQUEST:
{user_input}

PLAN REQUIREMENTS — you MUST:
1. Write all necessary code files with FULL correct content
2. Install required packages first
3. Run/test the code
4. Start a server if it's a web application

Return ONLY a JSON array, no markdown fences, no explanation:
[
  {{"tool":"install_package","args":{{"package":"flask"}}}},
  {{"tool":"write_file","args":{{"file_path":"{subdir}/app.py","content":"# full code here"}}}},
  {{"tool":"run_code","args":{{"command":"python {subdir}/app.py","timeout":15}}}},
  {{"tool":"start_server","args":{{"command":"python {subdir}/app.py","port":5001,"label":"My App"}}}}
]
"""

# ══════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════

def _emit(on_event, evt):
    if callable(on_event):
        try: on_event(evt)
        except: pass

# ══════════════════════════════════════════════════════════════
# NODES
# ══════════════════════════════════════════════════════════════

def node_planner(state: CodingState) -> Dict:
    on_event = state.get("_on_event")
    subdir   = state.get("subdir", CODING_DIR)
    _emit(on_event, {"type":"agent_step","step":"planner",
                     "label":f"📝 Planning — files → workspace/{subdir}/"})

    raw = _llm_invoke(_PLANNER_PROMPT.format(
        subdir=subdir, tool_docs=_TOOL_DOCS, user_input=state["user_input"]
    ))

    if "```" in raw:
        m = re.search(r"```(?:json)?\s*([\s\S]+?)```", raw)
        raw = m.group(1).strip() if m else raw.split("```")[1].strip()

    try:
        plan = json.loads(raw)
        if not isinstance(plan, list): plan = []
    except Exception:
        plan = []

    # Enforce subdir prefix
    for step in plan:
        fp = step.get("args",{}).get("file_path","")
        if fp and not fp.startswith(subdir):
            step["args"]["file_path"] = f"{subdir}/{fp.lstrip('/\\')}"

    _emit(on_event, {"type":"plan_ready","steps":len(plan),"plan":plan})
    return {"plan": plan}


def node_executor(state: CodingState) -> Dict:
    on_event     = state.get("_on_event")
    plan         = state.get("plan", [])
    observations: List[Dict[str, Any]] = []

    _tools_module.set_event_callback(on_event)

    for i, step in enumerate(plan):
        tool_name = step.get("tool","")
        args      = step.get("args",{}) or {}
        _emit(on_event, {"type":"step_start","index":i+1,"total":len(plan),
                         "tool":tool_name,"args":args,
                         "label":f"▶ Step {i+1}/{len(plan)}: {tool_name}"})
        tool_entry = TOOLS.get(tool_name)
        try:
            result = tool_entry["func"](args) if tool_entry else {"status":"error","error":f"Unknown: {tool_name}"}
        except Exception as exc:
            result = {"status":"error","error":str(exc)}

        success = result.get("status") != "error" and "error" not in result
        _emit(on_event, {"type":"step_done","index":i+1,"tool":tool_name,
                         "success":success,"result":result})
        observations.append({"step":i+1,"tool":tool_name,"args":args,
                              "result":result,"success":success})

    _tools_module.set_event_callback(None)

    _emit(on_event, {"type":"agent_step","step":"drafting","label":"✍️ Writing explanation…"})

    obs_summary = json.dumps([{
        "step":o["step"],"tool":o["tool"],"success":o["success"],
        "stdout":o["result"].get("stdout","")[:600],
        "stderr":o["result"].get("stderr","")[:300],
        "error": o["result"].get("error","")[:300],
        "message":o["result"].get("message","")[:200],
    } for o in observations], indent=2)

    subdir = state.get("subdir", CODING_DIR)
    draft = _llm_invoke(f"""\
You are a senior software engineer explaining your work clearly.

USER REQUEST: {state['user_input']}
FILES LOCATION: workspace/{subdir}/
EXECUTION RESULTS: {obs_summary}

Write a thorough explanation with these sections:
## What Was Built
## How It Works
## Output / Result
## How to Use It

Show key code in fenced blocks. Mention the workspace/{subdir}/ path.
If a server was started, tell the user to check the Preview tab.
""")
    return {"observations":observations,"events":list(state.get("events",[])),"draft":draft}


def node_debugger(state: CodingState) -> Dict:
    observations = state.get("observations", [])
    retries      = state.get("retries", 0)
    on_event     = state.get("_on_event")
    failed = [o for o in observations if not o["success"]]
    if not failed or retries >= 2:
        return {}
    _emit(on_event, {"type":"agent_step","step":"debugger","label":"🔧 Auto-debugging…"})
    err_sum = json.dumps([{"tool":o["tool"],"args":o["args"],
        "error":o["result"].get("error","") or o["result"].get("stderr","")} for o in failed], indent=2)
    fix = _llm_invoke(f"""\
Debug these failures:
{err_sum}
Request: {state.get('user_input','')}
Subdir: workspace/{state.get('subdir',CODING_DIR)}/
Explain root cause and provide corrected code. Use fenced code blocks.
""")
    return {"draft":(state.get("draft") or "")+"\n\n---\n### 🔧 Auto-Debug\n\n"+fix,
            "retries":retries+1}


def node_verifier(state: CodingState) -> Dict:
    on_event = state.get("_on_event")
    obs      = state.get("observations", [])
    success  = sum(1 for o in obs if o["success"])
    fail     = len(obs) - success
    subdir   = state.get("subdir", CODING_DIR)
    _emit(on_event, {"type":"execution_summary","total":len(obs),"success":success,"failed":fail})

    from sandbox import ws_list_servers
    servers = ws_list_servers().get("servers", {})
    server_note = ""
    if servers:
        urls = " · ".join(f"[{v['url']}]({v['url']})" for v in servers.values())
        server_note = f"\n\n🌐 **Live:** {urls} — open the **Preview** tab in the Workspace panel"

    final = (state.get("draft") or "") + (
        f"\n\n---\n✅ **{success}/{len(obs)} steps succeeded**"
        + (f" ({fail} failed)" if fail else "")
        + f"\n📁 Files in `workspace/{subdir}/`"
        + server_note
    )
    return {"final": final}


# ══════════════════════════════════════════════════════════════
# GRAPH
# ══════════════════════════════════════════════════════════════

def _build_graph():
    g = StateGraph(CodingState)
    g.add_node("planner",  node_planner)
    g.add_node("executor", node_executor)
    g.add_node("debugger", node_debugger)
    g.add_node("verifier", node_verifier)
    g.set_entry_point("planner")
    g.add_edge("planner",  "executor")
    g.add_edge("executor", "debugger")
    g.add_edge("debugger", "verifier")
    g.add_edge("verifier", END)
    return g.compile()


# ══════════════════════════════════════════════════════════════
# PUBLIC ENTRY POINT
# ══════════════════════════════════════════════════════════════

def tool_coding_agent(
    user_input: str,
    on_event:   Optional[Callable[[Dict[str, Any]], None]] = None,
    subdir:     str = CODING_DIR,
) -> str:
    """
    Run the sandboxed coding agent.
    Files go to workspace/{subdir}/ (default: workspace/coding/).
    Always explains, runs, and starts a server for web apps.
    """
    (BASE_DIR / subdir).mkdir(parents=True, exist_ok=True)
    result = _build_graph().invoke({
        "user_input":user_input,"subdir":subdir,
        "plan":[],"observations":[],"events":[],"draft":"","final":"","retries":0,
        "_on_event":on_event,
    })
    return result.get("final","No response generated.")
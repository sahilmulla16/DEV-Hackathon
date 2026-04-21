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

from core.config import logger
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
    has_failed:   bool
    _on_event:    Optional[Callable]
    connector_configs: Optional[Dict[str, Any]]

CODING_TOOL_NAMES = [
    "write_file","read_file","list_files","delete_file",
    "run_code","start_server","stop_server","install_package","image_search", "connector_tool",
]
_TOOL_DOCS = "\n".join(
    f"  {n}: {TOOLS[n]['desc']}" for n in CODING_TOOL_NAMES if n in TOOLS
)

# ══════════════════════════════════════════════════════════════
# PLANNER PROMPT
# ══════════════════════════════════════════════════════════════

_PLANNER_PROMPT = """
You are an expert AI coding agent. Your goal is to complete the user's request by planning and executing tool calls. All files are in `workspace/{subdir}/`.

GENERAL WORKFLOW:
1. **Explore (if necessary):** If you need to understand an existing project, use `list_files` to see the directory structure.
2. **Plan:** Create a step-by-step plan to achieve the user's goal.
3. **Execute:** Carry out the plan, installing packages, writing code, and running commands.

AVAILABLE TOOLS:
{tool_docs}

USER REQUEST:
{user_input}

**Complex Workflow Examples:**

*   **To create a new GitHub repository and push files:**
    1.  First, use `write_file` to create your local files (like a `README.md`).
    2.  Then, use `connector_tool` with `connector_id: 'github'` to create the remote repository.
    3.  Finally, use `run_code` to execute the necessary `git` commands (`git init`, `git add`, `git commit`, `git remote add`, `git push`).

*   **To run an existing Node.js project:**
    1.  First, use `list_files` to find the `package.json`.
    2.  Then, use `run_code` to `cd` into the directory and run `npm install`.
    3.  Finally, use `start_server` with the correct run command (e.g., `npm start`).

Based on the user's request, create a plan as a JSON array of tool calls. Do not add explanations.
""".format(tool_docs=_TOOL_DOCS, subdir="{subdir}", user_input="{user_input}")

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
        try:
            if tool_name == "connector_tool":
                from tools import tool_connector_tool as _tct
                connector_id = args.get("connector_id")
                connector_configs = state.get("connector_configs", {})
                env_vars = connector_configs.get(connector_id, {})
                result = _tct(
                    connector_id=connector_id,
                    user_input=args.get("user_input", ""),
                    env_extra=env_vars
                )
            else:
                tool_entry = TOOLS.get(tool_name)
                if tool_entry:
                    result = tool_entry["func"](args)
                else:
                    result = {"status":"error","error":f"Unknown tool: {tool_name}"}
        except Exception as exc:
            result = {"status":"error","error":str(exc)}

        success = result.get("status") != "error" and "error" not in result
        _emit(on_event, {"type":"step_done","index":i+1,"tool":tool_name,
                         "success":success,"result":result})
        observations.append({
            "step": i + 1, "tool": tool_name, "args": args,
            "result": result, "success": success
        })

    _tools_module.set_event_callback(None)

    has_failed_step = any(not o["success"] for o in observations)

    _emit(on_event, {"type":"agent_step","step":"drafting","label":"✍️ Writing explanation…"})

    obs_summary = json.dumps([{
        "step": o.get("step"), "tool": o.get("tool"), "success": o.get("success"),
        "stdout": o.get("result", {}).get("stdout","")[:600],
        "stderr": o.get("result", {}).get("stderr","")[:300],
        "error": o.get("result", {}).get("error","")[:300],
        "message": o.get("result", {}).get("message","")[:200],
        "image_paths": o.get("result", {}).get("image_paths"),
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
If the results include 'image_paths', you MUST display the image using markdown. The URL must be the full absolute URL. The base is `http://localhost:5000` and the path is `/api/workspace/view/` followed by the path from `image_paths`. Example: `!Image`.
If a server was started, tell the user to check the Preview tab.
""")
    return {"observations": observations, "draft": draft, "has_failed": has_failed_step}


def node_debugger(state: CodingState) -> Dict:
    """
    This node is a re-planner. It gets triggered when the executor has
    a failed step. It analyzes the error and creates a new plan to fix it.
    """
    observations = state.get("observations", [])
    retries      = state.get("retries", 0)
    on_event     = state.get("_on_event")
    subdir       = state.get("subdir", CODING_DIR)

    failed = [o for o in observations if not o["success"]]
    _emit(on_event, {"type":"agent_step","step":"debugger","label":"🔧 Auto-debugging…"})
    # Use .get() to robustly access keys that might be missing in a malformed observation
    err_sum = json.dumps([{"tool": o.get("tool"), "args": o.get("args"),
        "error": o.get("result", {}).get("error", "") or o.get("result", {}).get("stderr", "")} for o in failed], indent=2)

    debug_planner_prompt = f"""\
You are a debugging expert. A plan failed. Analyze the errors and create a NEW, corrected plan to achieve the original goal.

ORIGINAL REQUEST: {state.get('user_input','')}
SUBDIR: {subdir}
FAILED STEPS:
{err_sum}
PREVIOUS PLAN:
{json.dumps(state.get('plan', []), indent=2)}

Analyze the errors and create a new JSON array of tool calls to fix the problem and complete the task.
- If a file was not found, use `list_files` to find it.
- If a command failed (e.g. `pnpm install`), try a different command (e.g. `npm install`).
- If a package was missing, add an `install_package` step.
- If you need more information, read a file.
- Keep the `subdir` prefix for all file paths.

Return ONLY the new JSON plan.
"""
    raw = _llm_invoke(debug_planner_prompt)

    if "```" in raw:
        m = re.search(r"```(?:json)?\s*([\s\S]+?)```", raw)
        raw = m.group(1).strip() if m else raw.split("```")[1].strip()

    try:
        new_plan = json.loads(raw)
        if not isinstance(new_plan, list): new_plan = []
    except Exception:
        new_plan = []

    _emit(on_event, {"type":"plan_ready","steps":len(new_plan),"plan":new_plan, "is_fix": True})

    return {"plan": new_plan, "retries": retries + 1, "observations": []}


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

def should_debug(state: CodingState) -> str:
    """Decide whether to enter the debugging loop."""
    if state.get("retries", 0) >= 2:
        return "end"
    return "debug" if state.get("has_failed") else "end"

def _build_graph():
    g = StateGraph(CodingState)
    g.add_node("planner",  node_planner)
    g.add_node("executor", node_executor)
    g.add_node("debugger", node_debugger)
    g.add_node("verifier", node_verifier)

    g.set_entry_point("planner")
    g.add_edge("planner",  "executor")
    g.add_conditional_edges(
        "executor",
        should_debug,
        {"debug": "debugger", "end": "verifier"}
    )
    g.add_edge("debugger", "executor") # Loop back to executor with the new plan
    g.add_edge("verifier", END)
    return g.compile()


# ══════════════════════════════════════════════════════════════
# PUBLIC ENTRY POINT
# ══════════════════════════════════════════════════════════════

def tool_coding_agent(
    user_input: str,
    on_event:   Optional[Callable[[Dict[str, Any]], None]] = None,
    subdir:     str = CODING_DIR,
    connector_configs: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Run the sandboxed coding agent.
    Files go to workspace/{subdir}/ (default: workspace/coding/).
    Always explains, runs, and starts a server for web apps.
    """
    (BASE_DIR / subdir).mkdir(parents=True, exist_ok=True)
    try:
        result = _build_graph().invoke({
            "user_input": user_input, "subdir": subdir, "connector_configs": connector_configs,
            "plan": [], "observations": [], "events": [], "draft": "", "final": "", "retries": 0, "has_failed": False,
            "_on_event": on_event,
        })
        # Ensure result is a dict before calling .get()
        if isinstance(result, dict):
            return result.get("final", "No response generated.")
        else:
            logger.error(f"Coding agent returned unexpected type: {type(result).__name__}. Result: {result!r}")
            return {"status": "error", "error": f"Coding agent returned unexpected output: {str(result)[:200]}"}
    except Exception as e:
        logger.error(f"Coding agent invocation failed: {e}")
        err_str = str(e).lower()
        if "rate limit" in err_str or "429" in err_str:
            return {"status": "error", "error": "The coding agent could not complete the request due to high traffic on the AI model. Please try again in a moment."}
        return {"status": "error", "error": f"The coding agent encountered an unexpected error: {e}"}
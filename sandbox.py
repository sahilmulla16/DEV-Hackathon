# sandbox.py
"""
Sandboxed Workspace Manager  (Windows + Linux compatible)
==========================================================
All file operations are jailed inside  ./workspace/
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import threading
import time
import sys
from pathlib import Path
from typing import Dict, Any, Generator, Optional

IS_WINDOWS = sys.platform == "win32"

BASE_DIR      = Path("workspace").resolve()
EXEC_TIMEOUT  = 30
MAX_OUTPUT    = 50_000
MAX_FILE_SIZE = 2 * 1024 * 1024

BASE_DIR.mkdir(parents=True, exist_ok=True)

_servers: Dict[int, subprocess.Popen] = {}
_servers_lock = threading.Lock()


# ── Path safety ────────────────────────────────────────────────
def _safe_path(relative: str) -> Path:
    relative = re.sub(r'^[/\\]+', '', str(relative))
    full = (BASE_DIR / relative).resolve()
    if not str(full).startswith(str(BASE_DIR)):
        raise ValueError(f"Path escape blocked: {relative!r}")
    return full

def _rel(path: Path) -> str:
    try:
        return str(path.relative_to(BASE_DIR))
    except ValueError:
        return str(path)


# ── File operations ────────────────────────────────────────────
def ws_write_file(path: str, content: str) -> Dict[str, Any]:
    try:
        target = _safe_path(path)
        action = "edited" if target.exists() else "created"
        if len(content.encode()) > MAX_FILE_SIZE:
            return {"status": "error", "error": f"File too large (max {MAX_FILE_SIZE // 1024} KB)"}
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return {
            "status": "success", "action": action,
            "path": _rel(target), "size": target.stat().st_size,
            "message": f"✅ File {action}: workspace/{_rel(target)}",
        }
    except ValueError as e:
        return {"status": "error", "error": str(e)}
    except Exception as e:
        return {"status": "error", "error": f"write_failed: {e}"}


def ws_read_file(path: str) -> Dict[str, Any]:
    try:
        target = _safe_path(path)
        if not target.exists():
            return {"status": "error", "error": f"File not found: workspace/{_rel(target)}"}
        return {"status": "success", "path": _rel(target), "content": target.read_text(encoding="utf-8")}
    except ValueError as e:
        return {"status": "error", "error": str(e)}
    except Exception as e:
        return {"status": "error", "error": f"read_failed: {e}"}


def ws_list_files(subpath: str = "") -> Dict[str, Any]:
    try:
        base = _safe_path(subpath) if subpath else BASE_DIR
        if not base.is_dir():
            return {"status": "error", "error": f"Not a directory: {subpath}"}
        files = []
        for p in sorted(base.rglob("*")):
            if p.is_file():
                st = p.stat()
                files.append({
                    "path": _rel(p), "size": st.st_size,
                    "modified": time.strftime("%H:%M:%S", time.localtime(st.st_mtime)),
                })
        return {"status": "success", "files": files}
    except ValueError as e:
        return {"status": "error", "error": str(e)}


def ws_delete_file(path: str) -> Dict[str, Any]:
    try:
        target = _safe_path(path)
        if not target.exists():
            return {"status": "error", "error": "File not found"}
        shutil.rmtree(target) if target.is_dir() else target.unlink()
        return {"status": "success", "message": f"🗑️ Deleted: workspace/{_rel(target)}"}
    except ValueError as e:
        return {"status": "error", "error": str(e)}


# ── Process helpers ────────────────────────────────────────────
def _popen_flags() -> dict:
    """Extra Popen kwargs — Windows needs CREATE_NEW_PROCESS_GROUP."""
    if IS_WINDOWS:
        return {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP}
    return {"start_new_session": True}   # Linux: own session so killpg works


def _kill_proc(proc: subprocess.Popen) -> None:
    """Kill a process tree cross-platform."""
    try:
        if IS_WINDOWS:
            subprocess.call(
                ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
        else:
            import signal as _sig
            try:
                os.killpg(os.getpgid(proc.pid), _sig.SIGTERM)
            except Exception:
                proc.terminate()
        proc.wait(timeout=3)
    except Exception:
        try: proc.kill()
        except Exception: pass


# ── Code execution ─────────────────────────────────────────────
def ws_run_code(command: str, timeout: int = EXEC_TIMEOUT,
                env_extra: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    run_dir = BASE_DIR / "coding"
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONUNBUFFERED": "1"}
    if env_extra:
        env.update(env_extra)
    start = time.time()
    try:
        proc = subprocess.run(
            command, shell=True, capture_output=True, text=True,
            cwd=str(run_dir), timeout=timeout, env=env
        )
        elapsed = round(time.time() - start, 2)
        return {
            "status": "success" if proc.returncode == 0 else "error",
            "stdout": proc.stdout[:MAX_OUTPUT],
            "stderr": proc.stderr[:MAX_OUTPUT],
            "exit_code": proc.returncode,
            "duration": elapsed,
            "message": f"⚡ Ran in {elapsed}s (exit {proc.returncode})",
        }
    except subprocess.TimeoutExpired:
        return {"status": "error", "error": f"Timed out after {timeout}s",
                "stdout": "", "stderr": "", "exit_code": -1, "duration": timeout}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def ws_run_code_streaming(command: str,
                          timeout: int = EXEC_TIMEOUT,
                          env_extra: Optional[Dict[str, str]] = None) -> Generator[Dict[str, Any], None, None]:
    run_dir = BASE_DIR / "coding"
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONUNBUFFERED": "1"}
    if env_extra:
        env.update(env_extra)
    start = time.time()
    try:
        proc = subprocess.Popen(
            command, shell=True,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, cwd=str(run_dir), env=env,
            **_popen_flags(),
        )

        def _timeout_kill():
            time.sleep(timeout)
            if proc.poll() is None:
                _kill_proc(proc)

        threading.Thread(target=_timeout_kill, daemon=True).start()

        for line in proc.stdout:
            yield {"type": "stdout", "line": line.rstrip("\n")}

        proc.wait()
        yield {"type": "done", "exit_code": proc.returncode,
               "duration": round(time.time() - start, 2)}

    except Exception as e:
        yield {"type": "stderr", "line": f"Error: {e}"}
        yield {"type": "done", "exit_code": -1, "duration": round(time.time() - start, 2)}


# ── Server management ──────────────────────────────────────────
def ws_start_server(command: str, port: int, label: str = "") -> Dict[str, Any]:
    with _servers_lock:
        if port in _servers:
            _kill_proc(_servers.pop(port))
        env = {**os.environ, "PYTHONUNBUFFERED": "1", "PORT": str(port)}
        try:
            proc = subprocess.Popen(
                command, shell=True,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True, cwd=str(BASE_DIR), env=env,
                **_popen_flags(),
            )
            time.sleep(3)
            if proc.poll() is not None:
                err = proc.stderr.read(2000)
                return {"status": "error", "error": f"Server exited immediately: {err}"}
            _servers[port] = proc
            url = f"http://localhost:{port}"
            return {
                "status": "started", "port": port, "pid": proc.pid,
                "url": url, "label": label or command[:40],
                "message": f"🚀 Server started on {url} (pid {proc.pid})",
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}


def ws_stop_server(port: int) -> Dict[str, Any]:
    with _servers_lock:
        proc = _servers.pop(port, None)
        if proc is None:
            return {"status": "error", "error": f"No server on port {port}"}
        _kill_proc(proc)
        return {"status": "stopped", "port": port, "message": f"🛑 Server on port {port} stopped"}


def ws_list_servers() -> Dict[str, Any]:
    with _servers_lock:
        alive = {}
        for port, proc in list(_servers.items()):
            if proc.poll() is None:
                alive[port] = {"pid": proc.pid, "url": f"http://localhost:{port}"}
            else:
                del _servers[port]
        return {"status": "success", "servers": alive}


# ── Package install ────────────────────────────────────────────
def ws_install_package(package: str) -> Dict[str, Any]:
    if not re.match(r'^[a-zA-Z0-9_\-\.\[\]>=<!, ]+$', package):
        return {"status": "error", "error": f"Invalid package name: {package!r}"}
    flag = "" if IS_WINDOWS else " --break-system-packages"
    return ws_run_code(f"pip install {package} --quiet{flag}", timeout=120)


# ── Workspace reset ────────────────────────────────────────────
def ws_reset() -> Dict[str, Any]:
    for port in list(_servers.keys()):
        ws_stop_server(port)
    if BASE_DIR.exists():
        shutil.rmtree(BASE_DIR)
    BASE_DIR.mkdir(parents=True, exist_ok=True)
    return {"status": "success", "message": "🧹 Workspace reset"}
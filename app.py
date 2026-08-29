import os
import json
import queue
import traceback
import logging
import threading
from datetime import datetime

from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS
from langchain_chroma import Chroma
from werkzeug.utils import secure_filename

from agent import run_agent_once, ingest_knowledge_base, backfill_rag_metadata
from sandbox import ws_list_files, ws_read_file, ws_reset, BASE_DIR
import core.config


# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)


class Config:
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'uploads')
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', 'http://localhost:3000').split(',')
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() in ('true', '1', 't')


app.config.from_object(Config)
CORS(app, resources={r"/api/*": {"origins": app.config['CORS_ORIGINS']}})

# Ensure uploads folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Vector store
core.config._vectorstore = Chroma(
    collection_name=core.config.MEM_COLLECTION,
    embedding_function=core.config._embedding_fn,
    persist_directory=core.config.PERSIST_DIR
)

# Allowed file types
ALLOWED = {'.pdf', '.doc', '.docx', '.txt', '.csv', '.xlsx', '.xls', '.ppt', '.pptx'}

# 🔥 Fallback: Track last uploaded file
LAST_UPLOADED_FILE = None


# ─────────────────────────────────────────────
# STARTUP
# ─────────────────────────────────────────────

try:
    _bf = backfill_rag_metadata()
    logger.info(f"RAG startup backfill: {_bf}")
except Exception as e:
    logger.warning(f"RAG startup backfill failed: {e}")


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def _fi(fn):
    p = os.path.join(app.config['UPLOAD_FOLDER'], fn)
    st = os.stat(p)
    return {
        "name": fn,
        "size": st.st_size,
        "uploaded": datetime.fromtimestamp(st.st_mtime).isoformat(),
        "ext": os.path.splitext(fn)[1].lstrip('.').lower()
    }


def _sse(ev, d):
    return f"event: {ev}\ndata: {json.dumps(d)}\n\n"


# ─────────────────────────────────────────────
# CHAT ROUTES
# ─────────────────────────────────────────────

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json or {}
    user_input = data.get('message', '').strip()
    history = data.get('history', [])

    if not user_input:
        return jsonify({"error": "No message"}), 400

    try:
        r = run_agent_once(
            user_input=user_input,
            history=history,
            file_path=LAST_UPLOADED_FILE  # 🔥 fallback added
        )
        return jsonify({"answer": r.get("final", "Error."), "log": r.get("log", [])})
    except Exception as e:
        logger.error(e)
        return jsonify({"error": "Internal error."}), 500


@app.route('/api/chat/stream', methods=['POST'])
def chat_stream():
    data = request.json or {}
    user_input = data.get('message', '').strip()
    history = data.get('history', [])

    if not user_input:
        return jsonify({"error": "No message"}), 400

    q = queue.Queue()

    def on_log(e):
        q.put({"_e": "log", "entry": e})

    def on_ws(e):
        q.put({"_e": "workspace_event", **e})

    def run():
        try:
            r = run_agent_once(
                user_input=user_input,
                history=history,
                file_path=LAST_UPLOADED_FILE,  # 🔥 fallback added
                on_log=on_log,
                on_workspace_event=on_ws
            )
            q.put({"_e": "answer", "text": r.get("final", "No answer.")})
        except Exception as exc:
            logger.error(f"Agent error: {exc}\n{traceback.format_exc()}")
            q.put({"_e": "error", "message": str(exc)})
        finally:
            q.put({"_e": "done"})

    threading.Thread(target=run, daemon=True).start()

    def generate():
        yield ": ok\n\n"
        while True:
            item = q.get()
            if item["_e"] == "done":
                yield _sse("done", {})
                break
            ev = item.pop("_e")
            yield _sse(ev, item)

    return Response(stream_with_context(generate()), mimetype="text/event-stream")


# ─────────────────────────────────────────────
# FILE ROUTES
# ─────────────────────────────────────────────

@app.route('/api/files', methods=['GET'])
def list_files():
    try:
        fld = app.config['UPLOAD_FOLDER']
        files = [
            _fi(f) for f in os.listdir(fld)
            if os.path.isfile(os.path.join(fld, f)) and os.path.splitext(f)[1].lower() in ALLOWED
        ]
        files.sort(key=lambda x: x['uploaded'], reverse=True)
        return jsonify(files), 200
    except Exception as e:
        logger.error(e)
        return jsonify({"error": "Could not list files."}), 500


@app.route('/api/files/<filename>', methods=['DELETE'])
def del_file(filename):
    safe = secure_filename(filename)
    path = os.path.join(app.config['UPLOAD_FOLDER'], safe)

    if not os.path.exists(path):
        return jsonify({"error": "Not found."}), 404

    os.remove(path)
    return jsonify({"status": "deleted", "name": safe}), 200


@app.route('/api/upload', methods=['POST'])
def upload():
    global LAST_UPLOADED_FILE

    if 'file' not in request.files:
        return jsonify({"error": "No file"}), 400

    f = request.files['file']

    if not f.filename:
        return jsonify({"error": "No filename"}), 400

    ext = os.path.splitext(f.filename)[1].lower()
    if ext not in ALLOWED:
        return jsonify({"error": f"Unsupported: {ext}"}), 400

    fn = secure_filename(f.filename)
    fp = os.path.join(app.config['UPLOAD_FOLDER'], fn)

    # Save locally
    f.save(fp)

    # 🔥 Track last uploaded file
    LAST_UPLOADED_FILE = fn

    try:
        ingest_knowledge_base(fp)
        content = f"Extracted content from {fn}"
    except Exception as e:
        logger.warning(f"Extraction failed: {e}")
        content = f"No text extracted from {fn}"

    return jsonify({
        "status": f"'{fn}' uploaded.",
        "content": content,
        "file": _fi(fn)
    })


# ─────────────────────────────────────────────
# MISC
# ─────────────────────────────────────────────

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "workspace": str(BASE_DIR)}), 200


@app.route('/api/status', methods=['GET'])
def status():
    return jsonify({
        "activeAgents": 4,
        "tasksInProgress": 6,
        "systemStatus": "Online"
    })


# ─────────────────────────────────────────────

if __name__ == "__main__":
    app.run(debug=True, port=5000)
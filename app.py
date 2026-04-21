import os, json, queue, traceback, logging, threading, shutil, time
from datetime import datetime
from flask import Flask, request, jsonify, Response, stream_with_context, send_from_directory
from flask_cors import CORS
from langchain_chroma import Chroma
from werkzeug.utils import secure_filename
from agent import run_agent_once, ingest_knowledge_base, backfill_rag_metadata
from sandbox import ws_list_files, ws_read_file, ws_reset, BASE_DIR
import core.config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
app = Flask(__name__)

class Config:
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER','uploads')
    CORS_ORIGINS  = os.environ.get('CORS_ORIGINS','http://localhost:3000').split(',')
    DEBUG = os.environ.get('FLASK_DEBUG','False').lower() in ('true','1','t')

app.config.from_object(Config)
CORS(app, resources={r"/api/*": {"origins": app.config['CORS_ORIGINS']}})
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
# --- ChromaDB Initialization with Auto-Reset on Corruption ---
try:
    logger.info("Attempting to load ChromaDB vectorstore for agent memory...")
    core.config._vectorstore = Chroma(collection_name=core.config.MEM_COLLECTION, embedding_function=core.config._embedding_fn, persist_directory=core.config.PERSIST_DIR)
    logger.info("ChromaDB memory store loaded successfully.")
except Exception as e:
    # Check for the specific PanicException message or class name
    if "PanicException" in str(e) or "range start index" in str(e):
        logger.warning("ChromaDB panicked on startup. This indicates corrupted data. Deleting and recreating the memory persistence directory.")
        if os.path.exists(core.config.PERSIST_DIR):
            shutil.rmtree(core.config.PERSIST_DIR)
            time.sleep(0.5) 
        logger.info(f"Directory '{core.config.PERSIST_DIR}' removed. Retrying ChromaDB initialization.")
        core.config._vectorstore = Chroma(collection_name=core.config.MEM_COLLECTION, embedding_function=core.config._embedding_fn, persist_directory=core.config.PERSIST_DIR)
        logger.info("ChromaDB memory store re-initialized successfully after reset.")
    else:
        raise  # Re-raise other exceptions
ALLOWED = {'.pdf','.doc','.docx','.txt','.csv','.xlsx','.xls','.ppt','.pptx'}

# ── Startup: patch any old RAG chunks missing 'filename' metadata ──
try:
    _bf = backfill_rag_metadata()
    logger.info(f"RAG startup backfill: {_bf}")
except Exception as _e:
    logger.warning(f"RAG startup backfill failed (non-fatal): {_e}")

def _fi(fn):
    p=os.path.join(app.config['UPLOAD_FOLDER'],fn); st=os.stat(p)
    return {"name":fn,"size":st.st_size,"uploaded":datetime.fromtimestamp(st.st_mtime).isoformat(),"ext":os.path.splitext(fn)[1].lstrip('.').lower()}

def _sse(ev,d): return f"event: {ev}\ndata: {json.dumps(d)}\n\n"

@app.route('/api/chat/stream', methods=['POST'])
def chat_stream():
    data=request.json or {}
    user_input=data.get('message','').strip()
    history=data.get('history',[])
    connector_configs=data.get('connector_configs',{})  # env vars from active connectors

    if not user_input: return jsonify({"error":"No message"}),400

    q=queue.Queue()
    def on_log(e): q.put({"_e":"log","entry":e})
    def on_ws(e): q.put({"_e":"workspace_event",**e})
    def run():
        try:
            r=run_agent_once(user_input=user_input,history=history,on_log=on_log,on_workspace_event=on_ws, connector_configs=connector_configs)
            q.put({"_e":"answer","text":r.get("final","No answer.")})
        except Exception as exc:
            logger.error(f"Agent error: {exc}\n{traceback.format_exc()}")
            q.put({"_e":"error","message":str(exc)})
        finally: q.put({"_e":"done"})
    threading.Thread(target=run,daemon=True).start()
    def generate():
        yield ": ok\n\n"
        while True:
            try: item=q.get(timeout=90)
            except queue.Empty: yield ": ka\n\n"; continue
            ev=item.pop("_e")
            if ev=="done": yield _sse("done",{}); break
            yield _sse(ev,item)
    return Response(stream_with_context(generate()),mimetype="text/event-stream",
        headers={"Cache-Control":"no-cache","X-Accel-Buffering":"no","Access-Control-Allow-Origin":"*"})

@app.route('/api/chat', methods=['POST'])
def chat():
    d=request.json or {}; u=d.get('message','').strip(); h=d.get('history',[])
    connector_configs = d.get('connector_configs', {})
    if not u: return jsonify({"error":"No message"}),400
    try:
        r=run_agent_once(user_input=u,history=h, connector_configs=connector_configs)
        return jsonify({"answer":r.get("final","Error."),"log":r.get("log",[])})
    except Exception as exc:
        logger.error(f"{exc}"); return jsonify({"error":"Internal error."}),500

# Workspace routes
@app.route('/api/workspace/files',methods=['GET'])
def ws_files(): return jsonify(ws_list_files())
@app.route('/api/workspace/files/<path:fp>',methods=['GET'])
def ws_file_get(fp): r=ws_read_file(fp); return (jsonify(r),404) if r["status"]=="error" else jsonify(r)

@app.route('/api/workspace/view/<path:filepath>')
def serve_workspace_file(filepath):
    """Serves a file from the workspace directory."""
    # Security: Ensure the path is within the workspace
    safe_path = os.path.abspath(os.path.join(BASE_DIR, filepath))
    if not str(safe_path).startswith(os.path.abspath(BASE_DIR)):
        return "Path traversal detected", 400
    
    directory = os.path.dirname(safe_path)
    filename = os.path.basename(safe_path)
    return send_from_directory(directory, filename)

@app.route('/api/workspace/files/<path:fp>',methods=['POST'])
def ws_file_write(fp):
    """Write a file to the workspace. Body: {content: str}"""
    from sandbox import ws_write_file
    data = request.json or {}
    content = data.get('content','')
    result = ws_write_file(fp, content)
    return jsonify(result), (200 if result.get('status')=='success' else 400)

@app.route('/api/workspace/run', methods=['POST'])
def ws_run():
    """Run a command in the workspace and stream output via SSE."""
    from sandbox import ws_run_code_streaming
    data    = request.json or {}
    command = data.get('command','').strip()
    env_extra = data.get('env', None)
    if not command:
        return jsonify({"error":"No command"}), 400
    q = queue.Queue()
    def _run():
        try:
            for evt in ws_run_code_streaming(command, env_extra=env_extra):
                q.put(evt)
        except Exception as exc:
            q.put({"type":"stderr","line":str(exc)})
        finally:
            q.put(None)  # sentinel
    threading.Thread(target=_run, daemon=True).start()
    def generate():
        yield ": ok\n\n"
        while True:
            item = q.get()
            if item is None:
                yield _sse("run_done", {})
                break
            yield _sse(item.get("type","stdout"), item)
    return Response(stream_with_context(generate()), mimetype="text/event-stream",
        headers={"Cache-Control":"no-cache","X-Accel-Buffering":"no","Access-Control-Allow-Origin":"*"})

@app.route('/api/workspace/reset',methods=['POST'])
def ws_reset_route(): return jsonify(ws_reset())
@app.route('/api/workspace/servers',methods=['GET'])
def ws_svrs():
    from sandbox import ws_list_servers; return jsonify(ws_list_servers())
@app.route('/api/workspace/servers/<int:port>',methods=['DELETE'])
def ws_stop(port):
    from sandbox import ws_stop_server; return jsonify(ws_stop_server(port))

# Upload routes
@app.route('/api/files',methods=['GET'])
def list_files():
    try:
        fld=app.config['UPLOAD_FOLDER']
        files=[_fi(f) for f in os.listdir(fld) if os.path.isfile(os.path.join(fld,f)) and os.path.splitext(f)[1].lower() in ALLOWED]
        files.sort(key=lambda x:x['uploaded'],reverse=True); return jsonify(files),200
    except Exception as exc: logger.error(exc); return jsonify({"error":"Could not list files."}),500

@app.route('/api/files/<filename>',methods=['DELETE'])
def del_file(filename):
    safe=secure_filename(filename); p=os.path.join(app.config['UPLOAD_FOLDER'],safe)
    if not os.path.exists(p): return jsonify({"error":"Not found."}),404
    os.remove(p); return jsonify({"status":"deleted","name":safe}),200

@app.route('/api/upload',methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request"}), 400
    files = request.files.getlist('file')
    if not files or all(f.filename == '' for f in files):
        return jsonify({"error": "No selected files"}), 400

    results = []
    errors = []
    for f in files:
        if f and f.filename:
            ext = os.path.splitext(f.filename)[1].lower()
            if ext not in ALLOWED:
                errors.append(f"Unsupported file type: {f.filename}")
                continue
            
            fn = secure_filename(f.filename)
            fp = os.path.join(app.config['UPLOAD_FOLDER'], fn)
            f.save(fp)
            
            try:
                ingest_knowledge_base(fp)
                results.append({"status": f"'{fn}' uploaded.", "file": _fi(fn)})
            except Exception as exc:
                logger.error(f"Error processing {fn}: {exc}")
                errors.append(f"Failed to process '{fn}'.")

    if errors:
        error_message = ". ".join(errors)
        if results:
            return jsonify({"status": f"Partial success: {len(results)} uploaded, {len(errors)} failed.", "error": error_message, "files": [r['file'] for r in results]}), 207
        return jsonify({"error": error_message}), 500

    status_message = f"{len(results)} file(s) uploaded successfully."
    return jsonify({"status": status_message, "files": [r['file'] for r in results]})

@app.route('/api/health',methods=['GET'])
def health(): return jsonify({"status":"ok","workspace":str(BASE_DIR)}),200

@app.route('/api/rag/backfill',methods=['POST'])
def rag_backfill():
    """Manually trigger metadata backfill for old RAG chunks."""
    result = backfill_rag_metadata()
    return jsonify({"status":"ok","message":result}),200
@app.route('/api/status',methods=['GET'])
def status(): return jsonify({"activeAgents":4,"tasksInProgress":6,"systemStatus":"Online","agents":["LLaMA","Cerebras","Research","Critic"]})
@app.route('/api/features',methods=['GET'])
def features(): return jsonify([{"id":1,"icon":"code","title":"Sandboxed Execution","description":"All code runs inside workspace/."},{"id":2,"icon":"search","title":"Web Search","description":"Real-time DuckDuckGo search."},{"id":3,"icon":"file-text","title":"File System","description":"Create, edit, run files in the sandbox."}])

@app.route('/api/connectors', methods=['GET'])
def get_connectors():
    """Returns a list of available connectors for slash commands."""
    from tools import CONNECTORS_DEF
    return jsonify(CONNECTORS_DEF)
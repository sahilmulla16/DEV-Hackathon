/**
 * api.js  —  Frontend service layer
 * Place this file at:  src/services/api.js
 *
 * All components should import from here, never call fetch() directly.
 */

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

// ─── generic helper ────────────────────────────────────────────
const fetchJson = async (url, options = {}) => {
    const response = await fetch(url, options);
    if (!response.ok) {
        const err = await response.json().catch(() => ({ error: 'Network error' }));
        throw new Error(err.error || `HTTP ${response.status}`);
    }
    return response.json();
};


// ════════════════════════════════════════════════════════════════
// CHAT
// ════════════════════════════════════════════════════════════════

/**
 * Standard (non-streaming) chat call.
 * Prefer postChatStream for real-time log/workspace events.
 */
export const postChatMessage = (message, history) =>
    fetchJson(`${API_BASE_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message, history }),
    });

/**
 * SSE streaming chat.
 * Returns a ReadableStream reader — call from Chat.js.
 * Events emitted by the server:
 *   log              { entry }
 *   workspace_event  { type, ... }
 *   answer           { text }
 *   error            { message }
 *   done             {}
 */
export const postChatStream = async (message, history) => {
    const response = await fetch(`${API_BASE_URL}/chat/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message, history }),
    });
    if (!response.ok) throw new Error(`Stream error: HTTP ${response.status}`);
    return response.body.getReader();
};


// ════════════════════════════════════════════════════════════════
// KNOWLEDGE BASE  (uploaded files — src/uploads/)
// ════════════════════════════════════════════════════════════════

/**
 * List all uploaded knowledge-base files.
 * Returns: [{ name, size, uploaded, ext }]
 */
export const listKnowledgeFiles = () =>
    fetchJson(`${API_BASE_URL}/files`);

/**
 * Upload a file to the knowledge base.
 * Supported: .pdf .doc .docx .txt .csv .xlsx .xls .ppt .pptx
 */
export const uploadFile = (file) => {
    const fd = new FormData();
    fd.append('file', file);
    return fetchJson(`${API_BASE_URL}/upload`, { method: 'POST', body: fd });
};

/**
 * Delete an uploaded knowledge-base file by filename.
 */
export const deleteKnowledgeFile = (filename) =>
    fetchJson(`${API_BASE_URL}/files/${encodeURIComponent(filename)}`, {
        method: 'DELETE',
    });


// ════════════════════════════════════════════════════════════════
// WORKSPACE  (agent sandbox — workspace/ directory)
// ════════════════════════════════════════════════════════════════

/**
 * List all files in the agent's workspace sandbox.
 * Returns: { status, files: [{ path, size, modified }] }
 *
 * Route: GET /api/workspace/files
 * NOTE: This route lives in app.py — make sure you are running
 *       the latest app.py (the one that imports workspace.py).
 */
export const listWorkspaceFiles = () =>
    fetchJson(`${API_BASE_URL}/workspace/files`);

/**
 * Read the content of a workspace file.
 * Returns: { status, path, content }
 *
 * Route: GET /api/workspace/files/<path>
 */
export const readWorkspaceFile = (filePath) =>
    fetchJson(`${API_BASE_URL}/workspace/files/${encodeURIComponent(filePath)}`);

/**
 * Wipe the entire workspace and stop all running servers.
 * Route: POST /api/workspace/reset
 */
export const resetWorkspace = () =>
    fetchJson(`${API_BASE_URL}/workspace/reset`, { method: 'POST' });

/**
 * List all servers started by the agent.
 * Returns: { status, servers: { [port]: { url, pid } } }
 *
 * Route: GET /api/workspace/servers
 */
export const listWorkspaceServers = () =>
    fetchJson(`${API_BASE_URL}/workspace/servers`);

/**
 * Stop a running workspace server by port.
 * Route: DELETE /api/workspace/servers/<port>
 */
export const stopWorkspaceServer = (port) =>
    fetchJson(`${API_BASE_URL}/workspace/servers/${port}`, { method: 'DELETE' });


// ════════════════════════════════════════════════════════════════
// MISC
// ════════════════════════════════════════════════════════════════

export const getHealth  = () => fetchJson(`${API_BASE_URL}/health`);
export const getStatus  = () => fetchJson(`${API_BASE_URL}/status`);
export const getFeatures= () => fetchJson(`${API_BASE_URL}/features`);
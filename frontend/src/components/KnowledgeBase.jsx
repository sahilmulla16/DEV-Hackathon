import React, { useState, useEffect, useCallback } from 'react';
import {
    FileText, File, FileSpreadsheet, FileCode, Presentation,
    Trash2, RefreshCw, Database, AtSign, Copy, Check,
    ChevronDown, AlertCircle,
} from 'lucide-react';
import './KnowledgeBase.css';

/* ── File type metadata ─────────────────────────────────── */
const EXT_META = {
    pdf:  { icon: <FileText  size={14}/>, color:'#f87171', label:'PDF' },
    docx: { icon: <FileText  size={14}/>, color:'#60a5fa', label:'DOCX' },
    doc:  { icon: <FileText  size={14}/>, color:'#60a5fa', label:'DOC' },
    txt:  { icon: <FileCode  size={14}/>, color:'#a78bfa', label:'TXT' },
    csv:  { icon: <FileSpreadsheet size={14}/>, color:'#34d399', label:'CSV' },
    xlsx: { icon: <FileSpreadsheet size={14}/>, color:'#34d399', label:'XLSX' },
    xls:  { icon: <FileSpreadsheet size={14}/>, color:'#34d399', label:'XLS' },
    pptx: { icon: <Presentation size={14}/>, color:'#fb923c', label:'PPTX' },
    ppt:  { icon: <Presentation size={14}/>, color:'#fb923c', label:'PPT' },
};

function getMeta(ext) {
    return EXT_META[ext?.toLowerCase()] || { icon:<File size={14}/>, color:'#a0a0a0', label: (ext||'FILE').toUpperCase() };
}

function fmtSize(bytes) {
    if (!bytes) return '—';
    if (bytes < 1024)       return `${bytes} B`;
    if (bytes < 1024**2)    return `${(bytes/1024).toFixed(1)} KB`;
    return `${(bytes/1024**2).toFixed(1)} MB`;
}

function fmtDate(iso) {
    if (!iso) return '';
    const d = new Date(iso);
    return d.toLocaleDateString('en-US', { month:'short', day:'numeric', year:'numeric' });
}

/* ── Single file row ─────────────────────────────────────── */
const FileRow = ({ file, onDelete, onMentionCopy }) => {
    const meta    = getMeta(file.ext);
    const [confirmDelete, setConfirmDelete] = useState(false);
    const [mentionCopied, setMentionCopied] = useState(false);

    const handleDelete = () => {
        if (!confirmDelete) { setConfirmDelete(true); setTimeout(() => setConfirmDelete(false), 3000); return; }
        onDelete(file.name);
    };

    const handleMention = () => {
        const token = `@${file.name}`;
        navigator.clipboard.writeText(token).catch(() => {});
        onMentionCopy(token);
        setMentionCopied(true);
        setTimeout(() => setMentionCopied(false), 2000);
    };

    return (
        <div className="kb-file-row">
            {/* Icon + ext badge */}
            <div className="kb-file-icon" style={{ color: meta.color, background: `${meta.color}18`, border:`1px solid ${meta.color}30` }}>
                {meta.icon}
                <span className="kb-file-ext" style={{ color: meta.color }}>{meta.label}</span>
            </div>

            {/* Info */}
            <div className="kb-file-info">
                <span className="kb-file-name" title={file.name}>{file.name}</span>
                <span className="kb-file-meta">{fmtSize(file.size)} · {fmtDate(file.uploaded)}</span>
            </div>

            {/* Actions */}
            <div className="kb-file-actions">
                {/* @ mention button */}
                <button
                    className={`kb-action-btn kb-mention-btn ${mentionCopied ? 'active' : ''}`}
                    onClick={handleMention}
                    title={`Copy @${file.name} to clipboard`}
                >
                    {mentionCopied ? <Check size={11}/> : <AtSign size={11}/>}
                </button>

                {/* Delete button */}
                <button
                    className={`kb-action-btn kb-delete-btn ${confirmDelete ? 'confirm' : ''}`}
                    onClick={handleDelete}
                    title={confirmDelete ? 'Click again to confirm' : 'Delete file'}
                >
                    <Trash2 size={11}/>
                    {confirmDelete && <span className="kb-confirm-label">Sure?</span>}
                </button>
            </div>
        </div>
    );
};

/* ── Main KnowledgeBase component ────────────────────────── */
const KnowledgeBase = ({ onMentionInsert }) => {
    const [files,     setFiles]     = useState([]);
    const [loading,   setLoading]   = useState(false);
    const [error,     setError]     = useState('');
    const [collapsed, setCollapsed] = useState(false);
    const [toastMsg,  setToastMsg]  = useState('');

    const fetchFiles = useCallback(async () => {
        setLoading(true);
        setError('');
        try {
            const res  = await fetch('http://localhost:5000/api/files');
            if (!res.ok) throw new Error(`${res.status}`);
            const data = await res.json();
            setFiles(Array.isArray(data) ? data : []);
        } catch (err) {
            setError('Could not load files. Is the server running?');
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => { fetchFiles(); }, [fetchFiles]);

    const handleDelete = async (filename) => {
        try {
            const res = await fetch(`http://localhost:5000/api/files/${encodeURIComponent(filename)}`, { method:'DELETE' });
            if (!res.ok) throw new Error(`${res.status}`);
            setFiles(prev => prev.filter(f => f.name !== filename));
            showToast(`'${filename}' deleted.`);
        } catch {
            showToast('Delete failed.');
        }
    };

    const handleMentionCopy = (token) => {
        showToast(`${token} copied — paste it in the chat!`);
        if (onMentionInsert) onMentionInsert(token);
    };

    const showToast = (msg) => {
        setToastMsg(msg);
        setTimeout(() => setToastMsg(''), 3000);
    };

    return (
        <div className="kb-root">

            {/* Header */}
            <div className="kb-header" onClick={() => setCollapsed(v => !v)}>
                <div className="kb-header-left">
                    <div className="kb-header-icon"><Database size={12}/></div>
                    <span className="kb-header-title">Knowledge Base</span>
                    {files.length > 0 && (
                        <span className="kb-count-badge">{files.length}</span>
                    )}
                </div>
                <div className="kb-header-right">
                    <button
                        className="kb-refresh-btn"
                        onClick={e => { e.stopPropagation(); fetchFiles(); }}
                        title="Refresh file list"
                        disabled={loading}
                    >
                        <RefreshCw size={12} className={loading ? 'spin' : ''}/>
                    </button>
                    <ChevronDown size={13} className={`kb-chevron ${collapsed ? 'rotated' : ''}`}/>
                </div>
            </div>

            {/* Body */}
            <div className={`kb-body ${collapsed ? 'kb-body--collapsed' : ''}`}>

                {/* Hint */}
                <div className="kb-hint">
                    <AtSign size={10}/>
                    <span>Type <strong>@filename</strong> in chat to query a specific file</span>
                </div>

                {/* Error */}
                {error && (
                    <div className="kb-error">
                        <AlertCircle size={12}/>
                        <span>{error}</span>
                    </div>
                )}

                {/* Loading shimmer */}
                {loading && files.length === 0 && (
                    <div className="kb-shimmer-list">
                        {[1,2,3].map(i => <div key={i} className="kb-shimmer-row"/>)}
                    </div>
                )}

                {/* Empty state */}
                {!loading && !error && files.length === 0 && (
                    <div className="kb-empty">
                        <File size={22}/>
                        <p>No files uploaded yet</p>
                        <span>Upload a file above to get started</span>
                    </div>
                )}

                {/* File list */}
                {files.length > 0 && (
                    <div className="kb-file-list">
                        {files.map(f => (
                            <FileRow
                                key={f.name}
                                file={f}
                                onDelete={handleDelete}
                                onMentionCopy={handleMentionCopy}
                            />
                        ))}
                    </div>
                )}
            </div>

            {/* Toast */}
            {toastMsg && (
                <div className="kb-toast">
                    <Check size={11}/> {toastMsg}
                </div>
            )}
        </div>
    );
};

export default KnowledgeBase;
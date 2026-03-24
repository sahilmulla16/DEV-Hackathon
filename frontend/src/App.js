import React, { useState, useCallback, useRef, useEffect } from 'react';
import Chat from './components/Chat';
import FileUpload from './components/FileUpload';
import KnowledgeBase from './components/KnowledgeBase';
import WorkspacePanel from './components/WorkspacePanel';
import AgentLog from './components/AgentLog';
import {
    Menu, X, Sparkles, Monitor, TerminalSquare,
    PanelLeftClose, PanelLeftOpen, Cpu,
} from 'lucide-react';
import './App.css';

/* ─── Drag-resize hook ───────────────────────────────────── */
function useDragResize({ direction, minSize, maxSize, defaultSize, storageKey }) {
    const [size, setSize] = useState(() => {
        const saved = localStorage.getItem(storageKey);
        return saved ? parseInt(saved, 10) : defaultSize;
    });
    const dragging = useRef(false);
    const startPos = useRef(0);
    const startSize = useRef(0);

    const onMouseDown = useCallback((e) => {
        e.preventDefault();
        dragging.current = true;
        startPos.current  = direction === 'x' ? e.clientX : e.clientY;
        startSize.current = size;
        document.body.style.cursor     = 'col-resize';
        document.body.style.userSelect = 'none';
    }, [size, direction]);

    useEffect(() => {
        const onMove = (e) => {
            if (!dragging.current) return;
            const delta = e.clientX - startPos.current;
            const raw   = startSize.current + (direction === 'x' ? delta : -delta);
            setSize(Math.min(maxSize, Math.max(minSize, raw)));
        };
        const onUp = () => {
            if (!dragging.current) return;
            dragging.current = false;
            document.body.style.cursor     = '';
            document.body.style.userSelect = '';
            localStorage.setItem(storageKey, String(size));
        };
        window.addEventListener('mousemove', onMove);
        window.addEventListener('mouseup',   onUp);
        return () => {
            window.removeEventListener('mousemove', onMove);
            window.removeEventListener('mouseup',   onUp);
        };
    }, [direction, minSize, maxSize, size, storageKey]);

    return { size, setSize, onMouseDown };
}

/* ─── Panel header ───────────────────────────────────────── */
const PanelHeader = ({ icon, title, accent, actions }) => (
    <div className="panel-header">
        <div className="panel-header-left">
            <div className="panel-header-icon" style={{ '--accent': accent || '#f5a623' }}>{icon}</div>
            <span className="panel-header-title">{title}</span>
        </div>
        <div className="panel-header-actions">{actions}</div>
    </div>
);

/* ═══════════════════════════════════════════════════════════
   MAIN APP
═══════════════════════════════════════════════════════════ */
export default function App() {
    const [uploadStatus,   setUploadStatus]  = useState('');
    const [isUploading,    setIsUploading]   = useState(false);
    const [chatKey,        setChatKey]       = useState(Date.now());
    const [agentLog,       setAgentLog]      = useState([]);
    const [isLogLoading,   setIsLogLoading]  = useState(false);
    const [pendingMention, setPendingMention]= useState(null);
    const [kbKey,          setKbKey]         = useState(0);

    // Left sidebar
    const [sidebarOpen,    setSidebarOpen]   = useState(true);

    // Right panel: null=closed, 'workspace'=open, 'logs'=open
    const [rightPanel,     setRightPanel]    = useState(null);

    // Mobile
    const [mobileSidebar,  setMobileSidebar] = useState(false);
    const [mobilePanel,    setMobilePanel]   = useState(false);

    // Workspace SSE state
    const [workspaceEvents, setWorkspaceEvents] = useState([]);
    const [outputLines,     setOutputLines]     = useState([]);
    const [isRunning,       setIsRunning]        = useState(false);

    // Resizable panels
    const sidebar = useDragResize({ direction:'x', minSize:200, maxSize:480, defaultSize:280, storageKey:'sidebar-width' });
    const rightW  = useDragResize({ direction:'x', minSize:300, maxSize:700, defaultSize:400, storageKey:'right-panel-width' });

    // Handlers
    const handleUploadSuccess = s => {
        setUploadStatus(s); setIsUploading(false);
        setKbKey(v => v + 1);
        setTimeout(() => setUploadStatus(''), 5000);
    };
    const handleUploadError = e => { setUploadStatus(`Upload failed: ${e}`); setIsUploading(false); };

    const handleNewChat = () => {
        setChatKey(Date.now()); setUploadStatus(''); setAgentLog([]);
        setWorkspaceEvents([]); setOutputLines([]); setIsRunning(false);
        setMobileSidebar(false);
    };

    const handleWorkspaceEvent = useCallback((event) => {
        setWorkspaceEvents(prev => [...prev, event]);
        if (event.type === 'stdout')     setOutputLines(prev => [...prev, event.line]);
        if (event.type === 'stderr')     setOutputLines(prev => [...prev, `[stderr] ${event.line}`]);
        if (event.type === 'run_start') { setIsRunning(true); setOutputLines(prev => [...prev, `$ ${event.command}`]); }
        if (event.type === 'run_done')   setIsRunning(false);
    }, []);

    // Run code from chat code block → writes file + streams output to workspace Output tab
    const handleRunCode = useCallback(async (code, lang) => {
        // Open workspace panel on Output tab
        setRightPanel('workspace');

        const extMap = { python:'py', py:'py', bash:'sh', sh:'sh',
                         javascript:'js', js:'js', node:'js', typescript:'ts', ts:'ts' };
        const ext      = extMap[lang] || 'py';
        const filename = `coding/run_${Date.now()}.${ext}`;
        const cmdMap   = { py:'python', sh:'bash', js:'node', ts:'ts-node' };
        const cmd      = (cmdMap[ext] || 'python') + ' ' + filename;

        try {
            // 1. Write the code file into workspace/coding/
            await fetch(`http://localhost:5000/api/workspace/files/${filename}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ content: code }),
            });

            // 2. Stream the run output via SSE → triggers workspace events
            const res = await fetch('http://localhost:5000/api/workspace/run', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ command: cmd }),
            });
            if (!res.body) return;

            const reader = res.body.getReader();
            const dec    = new TextDecoder();
            let buf      = '';

            handleWorkspaceEvent({ type:'run_start', command: cmd });

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                buf += dec.decode(value, { stream: true });
                const lines = buf.split('\n');
                buf = lines.pop();
                for (const line of lines) {
                    if (!line.startsWith('data:')) continue;
                    try {
                        const payload = JSON.parse(line.slice(5).trim());
                        if (payload.line !== undefined) {
                            handleWorkspaceEvent({ type: payload.type || 'stdout', line: payload.line });
                        }
                    } catch {}
                }
            }
            handleWorkspaceEvent({ type:'run_done' });
        } catch (err) {
            handleWorkspaceEvent({ type:'stderr', line:`Run error: ${err.message}` });
            handleWorkspaceEvent({ type:'run_done' });
        }
    }, [handleWorkspaceEvent]);

    // Toggle right panel
    const togglePanel = (name) => setRightPanel(p => p === name ? null : name);

    const RIGHT_TABS = [
        { id:'workspace', icon:<Monitor size={16}/>,       title:'Workspace',   accent:'#60a5fa' },
        { id:'logs',      icon:<TerminalSquare size={16}/>, title:'System Logs', accent:'#f5a623' },
    ];

    return (
        <div className="App">
            {/* Mobile topbar */}
            <header className="mobile-header">
                <button className="icon-btn" onClick={() => { setMobileSidebar(!mobileSidebar); setMobilePanel(false); }}>
                    <Menu size={20}/>
                </button>
                <div className="mobile-header-brand">
                    <Cpu size={15} style={{ color:'#f5a623' }}/><span>AI Agent</span>
                </div>
                <button className="icon-btn" onClick={() => { setMobilePanel(!mobilePanel); setMobileSidebar(false); }}>
                    <Monitor size={20}/>
                </button>
            </header>

            <main className="App-main">
                {(mobileSidebar || mobilePanel) && (
                    <div className="mobile-overlay fade-in"
                        onClick={() => { setMobileSidebar(false); setMobilePanel(false); }}/>
                )}

                {/* ══ LEFT SIDEBAR ═══════════════════════════════════ */}
                <aside
                    className={`sidebar ${!sidebarOpen ? 'sidebar--collapsed' : ''} ${mobileSidebar ? 'sidebar--mobile-open' : ''}`}
                    style={{ width: sidebarOpen ? sidebar.size : 0 }}
                >
                    <PanelHeader
                        icon={<Sparkles size={14}/>} title="Menu" accent="#f5a623"
                        actions={
                            <>
                                <button className="panel-header-btn mobile-only" onClick={() => setMobileSidebar(false)}><X size={15}/></button>
                                <button className="panel-header-btn desktop-only" onClick={() => setSidebarOpen(false)} title="Collapse"><PanelLeftClose size={15}/></button>
                            </>
                        }
                    />
                    <div className="sidebar-content">
                        <button onClick={handleNewChat} className="new-chat-button">
                            <Sparkles size={14}/> New Chat
                        </button>
                        <section className="sidebar-section">
                            <div className="sidebar-section-label">Upload Knowledge</div>
                            <FileUpload onUploadSuccess={handleUploadSuccess} onUploadError={handleUploadError} setIsUploading={setIsUploading}/>
                            {isUploading && <p className="status-message">⏳ Uploading…</p>}
                            {uploadStatus && !isUploading && <p className="status-message">{uploadStatus}</p>}
                        </section>
                        <KnowledgeBase key={kbKey} onMentionFile={filename => {
                            setPendingMention(filename);
                            setTimeout(() => setPendingMention(null), 300);
                        }}/>
                    </div>
                    {sidebarOpen && (
                        <div className="resize-handle resize-handle--right" onMouseDown={sidebar.onMouseDown}>
                            <div className="resize-handle-bar"/>
                        </div>
                    )}
                </aside>

                {/* Collapsed sidebar re-open */}
                {!sidebarOpen && (
                    <button className="panel-reopen-btn panel-reopen-btn--left desktop-only"
                        onClick={() => setSidebarOpen(true)} title="Open sidebar">
                        <PanelLeftOpen size={16}/>
                    </button>
                )}

                {/* ══ CHAT ════════════════════════════════════════ */}
                <div className="chat-container">
                    <Chat
                        key={chatKey}
                        setAgentLog={setAgentLog}
                        setIsLogLoading={setIsLogLoading}
                        onWorkspaceEvent={handleWorkspaceEvent}
                        pendingMention={pendingMention}
                        onRunCode={handleRunCode}
                    />
                </div>

                {/* ══ RIGHT PANEL (slides in/out) ══════════════════ */}
                {rightPanel && (
                    <aside
                        className="right-panel-drawer"
                        style={{ width: rightW.size }}
                    >
                        {/* Drag handle */}
                        <div className="resize-handle resize-handle--left" onMouseDown={rightW.onMouseDown}>
                            <div className="resize-handle-bar"/>
                        </div>

                        {/* Panel header */}
                        <PanelHeader
                            icon={rightPanel === 'workspace' ? <Monitor size={14}/> : <TerminalSquare size={14}/>}
                            title={rightPanel === 'workspace' ? 'Workspace' : 'System Logs'}
                            accent={rightPanel === 'workspace' ? '#60a5fa' : '#f5a623'}
                            actions={
                                <button className="panel-header-btn" onClick={() => setRightPanel(null)} title="Close">
                                    <X size={15}/>
                                </button>
                            }
                        />

                        {/* Panel content */}
                        <div style={{ flex:1, overflow:'hidden', display:'flex', flexDirection:'column' }}>
                            {rightPanel === 'workspace' && (
                                <WorkspacePanel
                                    workspaceEvents={workspaceEvents}
                                    outputLines={outputLines}
                                    isRunning={isRunning}
                                    agentLog={agentLog}
                                    isLogLoading={isLogLoading}
                                />
                            )}
                            {rightPanel === 'logs' && (
                                <AgentLog log={agentLog} isLoading={isLogLoading}/>
                            )}
                        </div>
                    </aside>
                )}

                {/* ══ RIGHT ICON SIDEBAR ══════════════════════════ */}
                <div className="right-icon-sidebar">
                    {RIGHT_TABS.map(tab => (
                        <button
                            key={tab.id}
                            className={`right-icon-btn ${rightPanel === tab.id ? 'right-icon-btn--active' : ''}`}
                            onClick={() => togglePanel(tab.id)}
                            title={tab.title}
                            style={{ '--tab-accent': tab.accent }}
                        >
                            {tab.icon}
                            <span className="right-icon-label">{tab.title}</span>
                        </button>
                    ))}
                </div>
            </main>
        </div>
    );
}
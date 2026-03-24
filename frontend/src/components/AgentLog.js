import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
    CheckCircle, AlertCircle, Brain, Zap, Wrench,
    Database, Search, TerminalSquare, Activity,
    ChevronDown, Clock,
} from 'lucide-react';

/* ─── Log categorisation ────────────────────────────────── */
const CATS = [
    { re:/^✅/,   type:'success', icon:<CheckCircle size={11}/>,  label:'OK',     col:'#22c55e' },
    { re:/^❌/,   type:'error',   icon:<AlertCircle size={11}/>,  label:'ERR',    col:'#ef4444' },
    { re:/^⚠️/,  type:'warning', icon:<AlertCircle size={11}/>,  label:'WARN',   col:'#f59e0b' },
    { re:/^🧠/,   type:'memory',  icon:<Brain size={11}/>,        label:'MEM',    col:'#a78bfa' },
    { re:/^🤔/,   type:'memory',  icon:<Brain size={11}/>,        label:'MEM',    col:'#a78bfa' },
    { re:/^💾/,   type:'memory',  icon:<Database size={11}/>,     label:'MEM',    col:'#e879f9' },
    { re:/^🎯/,   type:'plan',    icon:<Zap size={11}/>,          label:'PLAN',   col:'#f5a623' },
    { re:/^📝/,   type:'plan',    icon:<Zap size={11}/>,          label:'PLAN',   col:'#f5a623' },
    { re:/^📎/,   type:'plan',    icon:<Zap size={11}/>,          label:'PLAN',   col:'#f5a623' },
    { re:/^🛠️/,  type:'exec',    icon:<Wrench size={11}/>,       label:'EXEC',   col:'#fb923c' },
    { re:/^⚙️/,  type:'exec',    icon:<Wrench size={11}/>,       label:'EXEC',   col:'#fb923c' },
    { re:/^🔍/,   type:'verify',  icon:<Search size={11}/>,       label:'CHECK',  col:'#38bdf8' },
    { re:/^ +↳/, type:'substep', icon:null,                       label:'',       col:'#4a4a4a' },
];

function categorize(text) {
    for (const c of CATS) {
        if (c.re.test(text)) return c;
    }
    return { type:'info', icon:<Activity size={11}/>, label:'INFO', col:'#60a5fa' };
}

/* ─── Phase detection ───────────────────────────────────── */
const PHASES = [
    { re:/Memory.*Checking|Direct Answer/i,  label:'Memory Check',    col:'#a78bfa', icon:<Brain size={10}/> },
    { re:/Planner.*Distilling|Planner.*Intent/i, label:'Planning',    col:'#f5a623', icon:<Zap size={10}/> },
    { re:/Planner.*Plan ready|step\(s\)/i,   label:'Execution Plan',  col:'#fb923c', icon:<Zap size={10}/> },
    { re:/Executor.*Running|Executor.*Call/i,label:'Executing Tools', col:'#34d399', icon:<Wrench size={10}/> },
    { re:/Executor.*Synthesising|draft/i,    label:'Drafting Answer', col:'#60a5fa', icon:<Activity size={10}/> },
    { re:/Verifier/i,                        label:'Verifying',       col:'#38bdf8', icon:<Search size={10}/> },
    { re:/Memory.*Saving/i,                  label:'Saving Memory',   col:'#e879f9', icon:<Database size={10}/> },
    { re:/approved/i,                        label:'Complete',        col:'#22c55e', icon:<CheckCircle size={10}/> },
];

function detectPhase(log) {
    for (let i = log.length - 1; i >= 0; i--) {
        for (const p of PHASES) {
            if (p.re.test(log[i])) return p;
        }
    }
    return null;
}

/* ─── Typewriter hook ───────────────────────────────────── */
function useTypewriter(text, speed = 18, onDone) {
    // Always call with a string — never null/undefined
    const safeText = text || '';
    const [displayed, setDisplayed] = useState('');
    const [done, setDone]           = useState(false);

    useEffect(() => {
        if (!safeText) {
            setDisplayed('');
            setDone(true);
            return;
        }
        setDisplayed('');
        setDone(false);
        let i = 0;
        const id = setInterval(() => {
            i++;
            setDisplayed(safeText.slice(0, i));
            if (i >= safeText.length) {
                clearInterval(id);
                setDone(true);
                onDone?.();
            }
        }, speed);
        return () => clearInterval(id);
    }, [safeText]); // eslint-disable-line react-hooks/exhaustive-deps

    return { displayed, done };
}

/* ─── Single log row ─────────────────────────────────────── */
const LogRow = React.memo(({ entry, index, isLast }) => {
    const cat      = categorize(entry);
    const isSubstep = /^ +↳/.test(entry);

    // Always pass a string — pass entry when last (animates), empty string otherwise (instant)
    const { displayed } = useTypewriter(isLast ? entry : '', 14);
    const text = isLast ? displayed : entry;

    return (
        <div style={{
            display:     'flex',
            gap:         0,
            borderBottom:'1px solid rgba(255,255,255,0.025)',
            paddingLeft: isSubstep ? '36px' : 0,
            animation:   'al-in 0.22s ease both',
            borderLeft:  isSubstep ? 'none' : `2px solid ${cat.col}30`,
            transition:  'background 0.12s',
        }}
        onMouseEnter={e => e.currentTarget.style.background='rgba(255,255,255,0.02)'}
        onMouseLeave={e => e.currentTarget.style.background='transparent'}
        >
            {/* Gutter */}
            {!isSubstep && (
                <div style={{ width:'42px',flexShrink:0,display:'flex',flexDirection:'column',alignItems:'center',padding:'5px 0',gap:'2px' }}>
                    <span style={{ fontFamily:"'Geist Mono',monospace",fontSize:'0.5rem',color:'#333' }}>
                        {String(index+1).padStart(3,'0')}
                    </span>
                    {cat.icon && (
                        <span style={{ width:'16px',height:'16px',borderRadius:'3px',background:`${cat.col}18`,display:'flex',alignItems:'center',justifyContent:'center',color:cat.col }}>
                            {cat.icon}
                        </span>
                    )}
                </div>
            )}

            {/* Text */}
            <div style={{ flex:1,padding:'5px 10px 5px 2px',minWidth:0,display:'flex',flexWrap:'wrap',alignItems:'baseline',gap:'5px' }}>
                {!isSubstep && cat.label && (
                    <span style={{
                        fontFamily:"'Geist Mono',monospace",fontSize:'0.54rem',fontWeight:700,
                        padding:'1px 5px',borderRadius:'3px',letterSpacing:'0.6px',flexShrink:0,
                        background:`${cat.col}18`,border:`1px solid ${cat.col}30`,color:cat.col,
                    }}>
                        {cat.label}
                    </span>
                )}
                <span style={{ fontSize:'0.7rem',color:isLast?'#c4c4c4':'#808080',lineHeight:1.5,wordBreak:'break-word',flex:1,minWidth:0,fontFamily:"'Outfit',sans-serif" }}>
                    {text}
                    {isLast && text.length < entry.length && (
                        <span style={{ display:'inline-block',width:'6px',height:'0.82em',background:'#f5a623',marginLeft:'2px',verticalAlign:'text-bottom',borderRadius:'1px',animation:'al-blink 0.8s step-end infinite' }}/>
                    )}
                </span>
            </div>
        </div>
    );
});

/* ─── Phase progress bar ─────────────────────────────────── */
const PhaseBar = ({ phase, isActive }) => {
    if (!phase) return null;
    return (
        <div style={{
            display:'flex',alignItems:'center',gap:'7px',
            padding:'7px 14px',
            background:`${phase.col}10`,
            borderBottom:'1px solid rgba(255,255,255,0.06)',
            animation:'al-in 0.25s ease',
        }}>
            <span style={{ color:phase.col,display:'flex',alignItems:'center' }}>{phase.icon}</span>
            <span style={{ fontSize:'0.68rem',fontWeight:600,color:phase.col,letterSpacing:'0.3px' }}>
                {phase.label}
            </span>
            {isActive && (
                <div style={{ flex:1,height:'2px',background:'rgba(255,255,255,0.07)',borderRadius:'2px',overflow:'hidden',marginLeft:'4px' }}>
                    <div style={{ height:'100%',width:'40%',background:phase.col,borderRadius:'2px',animation:'al-slide 1.4s ease-in-out infinite' }}/>
                </div>
            )}
            {!isActive && (
                <span style={{ marginLeft:'auto',fontSize:'0.6rem',color:'#22c55e',background:'rgba(34,197,94,0.08)',border:'1px solid rgba(34,197,94,0.2)',borderRadius:'10px',padding:'1px 6px' }}>✓ Done</span>
            )}
        </div>
    );
};

/* ─── Main AgentLog ──────────────────────────────────────── */
const AgentLog = ({ log = [], isLoading = false }) => {
    const [collapsed, setCollapsed] = useState(false);
    const [elapsed,   setElapsed]   = useState(0);
    const bottomRef  = useRef(null);
    const startTime  = useRef(null);
    const timerRef   = useRef(null);

    /* Elapsed timer */
    useEffect(() => {
        if (isLoading && !startTime.current) {
            startTime.current = Date.now();
            timerRef.current  = setInterval(() => {
                setElapsed(Math.floor((Date.now() - startTime.current) / 1000));
            }, 1000);
        }
        if (!isLoading) {
            clearInterval(timerRef.current);
            startTime.current = null;
        }
        return () => clearInterval(timerRef.current);
    }, [isLoading]);

    /* Auto-scroll */
    useEffect(() => {
        if (!collapsed) {
            bottomRef.current?.scrollIntoView({ behavior:'smooth' });
        }
    }, [log, collapsed]);

    const phase = detectPhase(log);
    const okCount  = log.filter(l=>/^✅/.test(l)).length;
    const errCount = log.filter(l=>/^❌/.test(l)).length;

    return (
        <>
            <style>{`
                @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600&family=Geist+Mono:wght@400;500&display=swap');
                @keyframes al-in   { from{opacity:0;transform:translateX(-5px)} to{opacity:1;transform:translateX(0)} }
                @keyframes al-blink{ 0%,100%{opacity:1} 50%{opacity:0} }
                @keyframes al-pulse{ 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:0.35;transform:scale(0.6)} }
                @keyframes al-slide{ 0%{transform:translateX(-100%)} 100%{transform:translateX(350%)} }
                @keyframes al-spin { to{transform:rotate(360deg)} }
            `}</style>

            <div style={{
                display:'flex',flexDirection:'column',height:'100%',
                background:'#0a0a0a',fontFamily:"'Outfit',sans-serif",
                borderLeft:'1px solid rgba(255,255,255,0.07)',overflow:'hidden',
                backgroundImage:'repeating-linear-gradient(0deg,transparent,transparent 2px,rgba(255,255,255,0.006) 2px,rgba(255,255,255,0.006) 4px)',
            }}>

                {/* ── Header ── */}
                <div
                    onClick={() => setCollapsed(v=>!v)}
                    style={{ display:'flex',alignItems:'center',justifyContent:'space-between',padding:'0 14px',height:'52px',flexShrink:0,background:'rgba(16,16,16,0.95)',borderBottom:'1px solid rgba(255,255,255,0.07)',cursor:'pointer',userSelect:'none',gap:'8px' }}
                >
                    <div style={{ display:'flex',alignItems:'center',gap:'8px' }}>
                        {/* Icon box */}
                        <div style={{ width:'26px',height:'26px',background:'rgba(245,166,35,0.12)',border:'1px solid rgba(245,166,35,0.22)',borderRadius:'6px',display:'flex',alignItems:'center',justifyContent:'center',color:'#f5a623' }}>
                            <TerminalSquare size={13}/>
                        </div>
                        <span style={{ fontSize:'0.82rem',fontWeight:600,color:'#ececec' }}>System Logs</span>

                        {/* LIVE badge */}
                        {isLoading && (
                            <div style={{ display:'flex',alignItems:'center',gap:'4px',padding:'2px 7px',background:'rgba(239,68,68,0.1)',border:'1px solid rgba(239,68,68,0.28)',borderRadius:'10px',fontSize:'0.58rem',fontWeight:700,color:'#f87171',letterSpacing:'1px',animation:'al-in 0.3s ease' }}>
                                <span style={{ width:'5px',height:'5px',background:'#ef4444',borderRadius:'50%',animation:'al-pulse 1s ease-in-out infinite' }}/>
                                LIVE
                            </div>
                        )}

                        {/* Timer */}
                        {isLoading && (
                            <div style={{ display:'flex',alignItems:'center',gap:'3px',fontSize:'0.62rem',color:'#606060',fontFamily:"'Geist Mono',monospace" }}>
                                <Clock size={10}/>
                                {elapsed}s
                            </div>
                        )}
                    </div>

                    <div style={{ display:'flex',alignItems:'center',gap:'7px' }}>
                        {/* Stats */}
                        {log.length > 0 && (
                            <div style={{ display:'flex',gap:'4px' }}>
                                <span style={{ fontFamily:"'Geist Mono',monospace",fontSize:'0.6rem',fontWeight:600,padding:'1px 6px',borderRadius:'8px',background:'rgba(255,255,255,0.05)',color:'#606060',border:'1px solid rgba(255,255,255,0.07)' }}>{log.length}</span>
                                {okCount  > 0 && <span style={{ fontFamily:"'Geist Mono',monospace",fontSize:'0.6rem',fontWeight:700,padding:'1px 6px',borderRadius:'8px',background:'rgba(34,197,94,0.1)',color:'#4ade80',border:'1px solid rgba(34,197,94,0.2)' }}>{okCount}✓</span>}
                                {errCount > 0 && <span style={{ fontFamily:"'Geist Mono',monospace",fontSize:'0.6rem',fontWeight:700,padding:'1px 6px',borderRadius:'8px',background:'rgba(239,68,68,0.1)',color:'#f87171',border:'1px solid rgba(239,68,68,0.2)' }}>{errCount}✗</span>}
                            </div>
                        )}
                        <ChevronDown size={14} style={{ color:'#505050',transition:'transform 0.26s ease',transform:collapsed?'rotate(-90deg)':'rotate(0deg)' }}/>
                    </div>
                </div>

                {/* ── Phase bar ── */}
                {!collapsed && phase && <PhaseBar phase={phase} isActive={isLoading}/>}

                {/* ── Log body ── */}
                <div style={{
                    flex:1,overflowY:'auto',overflowX:'hidden',
                    transition:'max-height 0.32s ease',
                    ...(collapsed ? {maxHeight:0,overflow:'hidden'} : {}),
                }}>
                    {/* Empty state */}
                    {log.length === 0 && (
                        <div style={{ display:'flex',flexDirection:'column',alignItems:'center',justifyContent:'center',height:'180px',gap:'8px',color:'#303030',textAlign:'center',padding:'20px' }}>
                            <TerminalSquare size={22}/>
                            <p style={{ fontFamily:"'Outfit',sans-serif",fontSize:'0.8rem',color:'#505050',margin:0 }}>Waiting for activity…</p>
                            <span style={{ fontSize:'0.65rem',color:'#333' }}>Logs appear here as the agent thinks</span>
                        </div>
                    )}

                    {/* Log rows */}
                    {log.length > 0 && (
                        <div>
                            {log.map((entry, i) => (
                                <LogRow key={i} entry={entry} index={i} isLast={i === log.length - 1 && isLoading}/>
                            ))}
                        </div>
                    )}

                    {/* Thinking indicator at bottom */}
                    {isLoading && log.length > 0 && (
                        <div style={{ display:'flex',alignItems:'center',gap:'8px',padding:'10px 14px',background:'rgba(245,166,35,0.04)',borderTop:'1px solid rgba(255,255,255,0.05)' }}>
                            <div style={{ display:'flex',gap:'3px' }}>
                                {[0,1,2].map(i=>(
                                    <span key={i} style={{ width:'5px',height:'5px',background:'#f5a623',borderRadius:'50%',display:'block',opacity:0.5,animation:`al-pulse 1.3s ease-in-out ${i*0.15}s infinite` }}/>
                                ))}
                            </div>
                            <span style={{ fontSize:'0.68rem',color:'#606060',fontStyle:'italic' }}>Agent is processing…</span>
                        </div>
                    )}

                    <div ref={bottomRef}/>
                </div>
            </div>
        </>
    );
};

export default AgentLog;
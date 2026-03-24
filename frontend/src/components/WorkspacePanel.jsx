import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
    Code2, Terminal, Globe, TerminalSquare,
    ChevronDown, ChevronRight, RefreshCw, X,
    Copy, Check, Play, Square, FileText, Folder,
} from 'lucide-react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { atomDark } from 'react-syntax-highlighter/dist/esm/styles/prism';

/* ─── tokens ─────────────────────────────────────────── */
const C = {
    bg0:'#0a0a0a', bg1:'#111111', bg2:'#161616', bg3:'#1c1c1c', bg4:'#222222',
    border:'rgba(255,255,255,0.07)',
    gold:'#f5a623', goldDim:'rgba(245,166,35,0.1)',
    t0:'#ececec', t1:'#909090', t2:'#444444',
    green:'#22c55e', red:'#ef4444', blue:'#60a5fa', amber:'#f59e0b',
};

/* ─── helpers ────────────────────────────────────────── */
function langOf(p=''){const e=p.split('.').pop().toLowerCase();return({py:'python',js:'javascript',jsx:'jsx',ts:'typescript',tsx:'tsx',html:'html',css:'css',json:'json',md:'markdown',sh:'bash',txt:'text',yml:'yaml',yaml:'yaml'})[e]||'text';}
function colorOf(p=''){const e=p.split('.').pop().toLowerCase();return({py:'#3b82f6',js:'#eab308',jsx:'#22d3ee',ts:'#60a5fa',html:'#f97316',css:'#a78bfa',json:'#34d399',md:'#94a3b8',sh:'#22c55e'})[e]||C.t2;}

/* ─── CopyBtn ─────────────────────────────────────────── */
const CopyBtn=({text})=>{const[ok,set]=useState(false);const go=async()=>{try{await navigator.clipboard.writeText(text);}catch{}set(true);setTimeout(()=>set(false),1800);};return(<button onClick={go} style={{display:'flex',alignItems:'center',gap:4,padding:'3px 8px',background:ok?'rgba(34,197,94,.1)':'rgba(255,255,255,.05)',border:`1px solid ${ok?'rgba(34,197,94,.3)':C.border}`,borderRadius:5,color:ok?C.green:C.t1,fontSize:'0.63rem',fontWeight:500,cursor:'pointer',transition:'all .15s',whiteSpace:'nowrap',fontFamily:"'Outfit',sans-serif"}}>{ok?<Check size={10}/>:<Copy size={10}/>}<span>{ok?'Copied':'Copy'}</span></button>);};

/* ─── FileTree ────────────────────────────────────────── */
const FileTree=({files,selected,onSelect})=>{
    if(!files.length)return(<div style={{padding:'20px 12px',textAlign:'center',color:C.t2,fontSize:'0.7rem'}}><Folder size={18} style={{opacity:.25,display:'block',margin:'0 auto 6px'}}/> No files yet</div>);
    return(<div style={{overflowY:'auto',flex:1}}>{files.map(f=>(<button key={f.path} onClick={()=>onSelect(f)} style={{display:'flex',alignItems:'center',gap:7,width:'100%',padding:'5px 10px',background:'transparent',border:'none',borderLeft:selected?.path===f.path?`2px solid ${C.gold}`:'2px solid transparent',backgroundColor:selected?.path===f.path?C.goldDim:'transparent',cursor:'pointer',textAlign:'left',transition:'all .12s'}} onMouseEnter={e=>{if(selected?.path!==f.path)e.currentTarget.style.background='rgba(255,255,255,0.025)';}} onMouseLeave={e=>{if(selected?.path!==f.path)e.currentTarget.style.background='transparent';}}>
        <FileText size={11} style={{color:colorOf(f.path),flexShrink:0}}/>
        <span style={{fontSize:'0.68rem',color:selected?.path===f.path?C.t0:C.t1,overflow:'hidden',textOverflow:'ellipsis',whiteSpace:'nowrap',flex:1,fontFamily:"'Geist Mono',monospace"}}>{f.path}</span>
        <span style={{fontSize:'0.57rem',color:C.t2,flexShrink:0,fontFamily:"'Geist Mono',monospace"}}>{f.size<1024?`${f.size}B`:`${(f.size/1024).toFixed(1)}K`}</span>
    </button>))}</div>);
};

/* ─── Code tab ────────────────────────────────────────── */
const CodeTab=({files,workspaceEvents})=>{
    const[sel,setSel]=useState(null);
    const[content,setContent]=useState('');
    const[loading,setLoading]=useState(false);

    // auto-select last written file
    useEffect(()=>{
        if(!workspaceEvents.length)return;
        const last=workspaceEvents[workspaceEvents.length-1];
        if((last.type==='file_op_done')&&(last.op==='created'||last.op==='edited')){
            setSel({path:last.path});
        }
    },[workspaceEvents]);

    useEffect(()=>{
        if(!sel)return;
        setLoading(true);setContent('');
        fetch(`http://localhost:5000/api/workspace/files/${encodeURIComponent(sel.path)}`)
            .then(r=>r.json()).then(d=>{if(d.content!=null)setContent(d.content);}).catch(()=>{}).finally(()=>setLoading(false));
    },[sel]);

    return(
        <div style={{flex:1,display:'flex',flexDirection:'column',minHeight:0}}>
            {/* file tree */}
            <div style={{maxHeight:200,flexShrink:0,borderBottom:`1px solid ${C.border}`,background:C.bg1,display:'flex',flexDirection:'column'}}>
                <div style={{padding:'5px 10px',borderBottom:`1px solid ${C.border}`,display:'flex',alignItems:'center',gap:6,flexShrink:0}}>
                    <Folder size={10} style={{color:C.gold}}/>
                    <span style={{fontSize:'0.62rem',fontWeight:700,letterSpacing:'0.8px',textTransform:'uppercase',color:C.t2}}>workspace/</span>
                    <span style={{fontSize:'0.58rem',color:C.t2,marginLeft:'auto',fontFamily:"'Geist Mono',monospace"}}>{files.length} file{files.length!==1?'s':''}</span>
                </div>
                <FileTree files={files} selected={sel} onSelect={setSel}/>
            </div>
            {/* viewer */}
            {!sel?(
                <div style={{flex:1,display:'flex',alignItems:'center',justifyContent:'center',flexDirection:'column',gap:8,color:C.t2}}>
                    <Code2 size={26} style={{opacity:.2}}/><span style={{fontSize:'0.72rem'}}>Select a file to view</span>
                </div>
            ):loading?(
                <div style={{flex:1,display:'flex',alignItems:'center',justifyContent:'center',color:C.t2}}>
                    <RefreshCw size={14} style={{animation:'ws-spin .7s linear infinite',marginRight:6}}/><span style={{fontSize:'0.72rem'}}>Loading…</span>
                </div>
            ):(
                <div style={{flex:1,overflow:'auto',minHeight:0}}>
                    <div style={{display:'flex',alignItems:'center',justifyContent:'space-between',padding:'6px 12px',background:C.bg2,borderBottom:`1px solid ${C.border}`,position:'sticky',top:0,zIndex:1,gap:8}}>
                        <div style={{display:'flex',alignItems:'center',gap:6}}>
                            <FileText size={11} style={{color:colorOf(sel.path)}}/>
                            <span style={{fontSize:'0.68rem',color:C.t0,fontFamily:"'Geist Mono',monospace"}}>{sel.path}</span>
                        </div>
                        <CopyBtn text={content}/>
                    </div>
                    <SyntaxHighlighter style={atomDark} language={langOf(sel.path)} showLineNumbers
                        customStyle={{margin:0,padding:'12px 14px',background:'#0c0c0c',fontSize:'0.75rem',lineHeight:'1.65',minHeight:'100%'}}
                        lineNumberStyle={{color:'#222',minWidth:'1.8em',paddingRight:'10px',userSelect:'none',fontSize:'0.68rem'}}>
                        {content||''}
                    </SyntaxHighlighter>
                </div>
            )}
        </div>
    );
};

/* ─── Output tab ──────────────────────────────────────── */
const OutputTab=({lines,running})=>{
    const btm=useRef(null);
    useEffect(()=>{btm.current?.scrollIntoView({behavior:'smooth',block:'nearest'});},[lines]);
    return(
        <div style={{flex:1,display:'flex',flexDirection:'column',minHeight:0}}>
            <div style={{display:'flex',alignItems:'center',justifyContent:'space-between',padding:'6px 12px',background:C.bg2,borderBottom:`1px solid ${C.border}`,flexShrink:0,gap:8}}>
                <div style={{display:'flex',alignItems:'center',gap:6}}>
                    <span style={{width:7,height:7,background:running?C.green:C.t2,borderRadius:'50%',display:'block',animation:running?'ws-pulse 1s ease infinite':'none'}}/>
                    <span style={{fontSize:'0.67rem',color:running?C.green:C.t2,fontWeight:600}}>{running?'Running':'Idle'}</span>
                    <span style={{fontSize:'0.62rem',color:C.t2,marginLeft:2}}>{lines.length} line{lines.length!==1?'s':''}</span>
                </div>
                <CopyBtn text={lines.join('\n')}/>
            </div>
            <div style={{flex:1,overflow:'auto',padding:'10px 14px',background:'#080808',fontFamily:"'Geist Mono',monospace",fontSize:'0.74rem',lineHeight:1.65}}>
                {lines.length===0?(
                    <div style={{display:'flex',flexDirection:'column',alignItems:'center',justifyContent:'center',height:'100%',gap:8,color:C.t2}}>
                        <Terminal size={22} style={{opacity:.2}}/><span style={{fontSize:'0.72rem',fontFamily:"'Outfit',sans-serif"}}>Output will appear here when code runs</span>
                    </div>
                ):lines.map((l,i)=>{
                    const isErr=/^(\[stderr\]|error|traceback|exception)/i.test(l);
                    const isWarn=/^(warn|warning|\[warn)/i.test(l);
                    const isCmd=/^\$/.test(l);
                    const isOk=/^(✅|success|done|started|running)/i.test(l);
                    const col=isErr?'#fca5a5':isWarn?'#fcd34d':isCmd?C.amber:isOk?'#86efac':C.t1;
                    return(<div key={i} style={{padding:'1px 0',color:col,wordBreak:'break-all'}}>{l||<span style={{opacity:.25}}>(empty)</span>}</div>);
                })}
                <div ref={btm}/>
            </div>
        </div>
    );
};

/* ─── Server/Preview tab ──────────────────────────────── */
const ServerTab=({servers,onStop})=>{
    const[url,setUrl]=useState('');
    const[active,setActive]=useState('');
    const svrs=Object.entries(servers);
    useEffect(()=>{if(svrs.length&&!active){const u=svrs[0][1].url;setActive(u);setUrl(u);}},[svrs.length]);
    return(
        <div style={{flex:1,display:'flex',flexDirection:'column',minHeight:0}}>
            {/* server list */}
            <div style={{flexShrink:0,borderBottom:`1px solid ${C.border}`,background:C.bg1,padding:'8px 10px',display:'flex',flexDirection:'column',gap:5}}>
                <div style={{display:'flex',alignItems:'center',gap:6,marginBottom:4}}>
                    <Globe size={11} style={{color:svrs.length?C.green:C.t2}}/>
                    <span style={{fontSize:'0.67rem',fontWeight:700,color:C.t0}}>Running Servers</span>
                    {svrs.length>0&&<span style={{fontSize:'0.58rem',background:'rgba(34,197,94,.12)',border:'1px solid rgba(34,197,94,.22)',color:C.green,borderRadius:8,padding:'1px 5px'}}>{svrs.length}</span>}
                </div>
                {svrs.length===0?(
                    <div style={{fontSize:'0.67rem',color:C.t2,padding:'4px 0'}}>No servers running</div>
                ):svrs.map(([port,info])=>(
                    <div key={port} style={{display:'flex',alignItems:'center',gap:8,padding:'6px 8px',background:C.bg3,borderRadius:6,border:`1px solid ${C.border}`}}>
                        <span style={{width:6,height:6,background:C.green,borderRadius:'50%',flexShrink:0,animation:'ws-pulse 1.4s ease infinite'}}/>
                        <div style={{flex:1,minWidth:0}}>
                            <div style={{fontSize:'0.7rem',color:C.t0,fontWeight:600}}>{info.label||`Port ${port}`}</div>
                            <button onClick={()=>{setActive(info.url);setUrl(info.url);}} style={{background:'none',border:'none',cursor:'pointer',color:C.blue,fontSize:'0.63rem',padding:0,fontFamily:"'Geist Mono',monospace"}}>{info.url}</button>
                        </div>
                        <button onClick={()=>onStop(parseInt(port))} title="Stop" style={{background:'rgba(239,68,68,.1)',border:'1px solid rgba(239,68,68,.2)',color:C.red,borderRadius:4,padding:'3px 5px',cursor:'pointer',display:'flex'}}><Square size={9}/></button>
                    </div>
                ))}
            </div>
            {/* URL bar */}
            <div style={{display:'flex',alignItems:'center',gap:6,padding:'6px 10px',background:C.bg2,borderBottom:`1px solid ${C.border}`,flexShrink:0}}>
                <Globe size={11} style={{color:C.t2,flexShrink:0}}/>
                <input value={url} onChange={e=>setUrl(e.target.value)} onKeyDown={e=>e.key==='Enter'&&setActive(url)} placeholder="http://localhost:5001"
                    style={{flex:1,background:'rgba(255,255,255,.04)',border:`1px solid ${C.border}`,borderRadius:4,padding:'3px 7px',color:C.t0,fontFamily:"'Geist Mono',monospace",fontSize:'0.67rem',outline:'none'}}/>
                <button onClick={()=>setActive(url)} style={{background:C.goldDim,border:`1px solid rgba(245,166,35,.25)`,color:C.gold,borderRadius:4,padding:'4px 8px',cursor:'pointer',fontSize:'0.63rem',fontWeight:600,fontFamily:"'Outfit',sans-serif",display:'flex',alignItems:'center',gap:3}}><Play size={9}/> Go</button>
            </div>
            {/* iframe */}
            {active?(
                <iframe key={active} src={active} title="Live Preview" style={{flex:1,border:'none',background:'#fff'}} sandbox="allow-scripts allow-same-origin allow-forms allow-popups"/>
            ):(
                <div style={{flex:1,display:'flex',flexDirection:'column',alignItems:'center',justifyContent:'center',gap:10,color:C.t2,background:C.bg0}}>
                    <Globe size={28} style={{opacity:.18}}/><span style={{fontSize:'0.73rem',fontFamily:"'Outfit',sans-serif"}}>No preview yet</span>
                    <span style={{fontSize:'0.63rem',maxWidth:200,textAlign:'center',lineHeight:1.5,fontFamily:"'Outfit',sans-serif"}}>Ask the agent to start a server — it will appear here automatically</span>
                </div>
            )}
        </div>
    );
};

/* ─── MiniLog (collapsed system log at bottom) ────────── */
const MiniLog=({log,isLoading})=>{
    const[open,setOpen]=useState(false);
    const btm=useRef(null);
    useEffect(()=>{if(open)btm.current?.scrollIntoView({behavior:'smooth',block:'nearest'});},[log,open]);
    const ok=log.filter(l=>/^✅/.test(l)).length;
    const err=log.filter(l=>/^❌/.test(l)).length;
    return(
        <div style={{borderTop:`1px solid ${C.border}`,flexShrink:0,background:C.bg1}}>
            <button onClick={()=>setOpen(v=>!v)} style={{display:'flex',alignItems:'center',justifyContent:'space-between',width:'100%',padding:'8px 12px',background:'transparent',border:'none',cursor:'pointer',gap:8}}>
                <div style={{display:'flex',alignItems:'center',gap:7}}>
                    <TerminalSquare size={12} style={{color:C.gold}}/>
                    <span style={{fontSize:'0.7rem',fontWeight:600,color:C.t0,fontFamily:"'Outfit',sans-serif"}}>System Logs</span>
                    {isLoading&&<span style={{display:'flex',alignItems:'center',gap:3,fontSize:'0.58rem',color:C.red,background:'rgba(239,68,68,.1)',border:'1px solid rgba(239,68,68,.22)',borderRadius:8,padding:'1px 5px'}}><span style={{width:5,height:5,background:C.red,borderRadius:'50%',animation:'ws-pulse 1s ease infinite'}}/>LIVE</span>}
                </div>
                <div style={{display:'flex',alignItems:'center',gap:5}}>
                    {log.length>0&&<span style={{fontFamily:"'Geist Mono',monospace",fontSize:'0.58rem',color:C.t2,background:'rgba(255,255,255,.04)',borderRadius:7,padding:'1px 5px'}}>{log.length}</span>}
                    {ok>0&&<span style={{fontSize:'0.58rem',color:C.green}}>✓{ok}</span>}
                    {err>0&&<span style={{fontSize:'0.58rem',color:C.red}}>✗{err}</span>}
                    <ChevronDown size={12} style={{color:C.t2,transform:open?'rotate(0)':'rotate(-90deg)',transition:'transform .2s'}}/>
                </div>
            </button>
            {open&&(
                <div style={{maxHeight:200,overflowY:'auto',background:C.bg0,borderTop:`1px solid ${C.border}`}}>
                    {log.length===0?(<div style={{padding:'14px',textAlign:'center',fontSize:'0.68rem',color:C.t2,fontFamily:"'Outfit',sans-serif"}}>Waiting for activity…</div>
                    ):log.map((e,i)=>(
                        <div key={i} style={{padding:'3px 12px',fontSize:'0.66rem',color:/^✅/.test(e)?'#86efac':/^❌/.test(e)?'#fca5a5':C.t2,borderBottom:'1px solid rgba(255,255,255,.02)',lineHeight:1.5,fontFamily:"'Outfit',sans-serif"}}>{e}</div>
                    ))}
                    <div ref={btm}/>
                </div>
            )}
        </div>
    );
};

/* ════════════════════════════════════════════════════════
   MAIN WorkspacePanel
════════════════════════════════════════════════════════ */
const WorkspacePanel=({workspaceEvents=[],outputLines=[],isRunning=false,agentLog=[],isLogLoading=false})=>{
    const[tab,setTab]=useState('code');
    const[files,setFiles]=useState([]);
    const[servers,setServers]=useState({});
    const[outBadge,setOutBadge]=useState(false);
    const[srvBadge,setSrvBadge]=useState(false);

    const refreshFiles=useCallback(async()=>{
        try{const r=await fetch('http://localhost:5000/api/workspace/files');const d=await r.json();if(d.files)setFiles(d.files);}catch{}
    },[]);
    const refreshServers=useCallback(async()=>{
        try{const r=await fetch('http://localhost:5000/api/workspace/servers');const d=await r.json();if(d.servers)setServers(d.servers);}catch{}
    },[]);

    useEffect(()=>{refreshFiles();refreshServers();},[]);

    // React to SSE workspace events
    useEffect(()=>{
        if(!workspaceEvents.length)return;
        const last=workspaceEvents[workspaceEvents.length-1];
        if(last.type==='file_op_done')refreshFiles();
        if(last.type==='run_done')refreshFiles();
        if(last.type==='run_start'){setTab('output');setOutBadge(false);}
        if(last.type==='stdout'||last.type==='stderr'){
            if(tab!=='output')setOutBadge(true);
        }
        if(last.type==='server_started'){refreshServers();setTab('server');setSrvBadge(true);}
    },[workspaceEvents]);

    const stopServer=async(port)=>{
        await fetch(`http://localhost:5000/api/workspace/servers/${port}`,{method:'DELETE'});
        refreshServers();
    };

    const switchTab=t=>{setTab(t);if(t==='output')setOutBadge(false);if(t==='server')setSrvBadge(false);};

    const TABS=[
        {id:'code',   icon:<Code2 size={13}/>,   label:'Code',    badge:files.length||null},
        {id:'output', icon:<Terminal size={13}/>, label:'Output',  badge:outBadge?'●':null},
        {id:'server', icon:<Globe size={13}/>,    label:'Preview', badge:srvBadge||Object.keys(servers).length?(Object.keys(servers).length||'●'):null},
    ];

    return(
        <>
            <style>{`
                @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600&family=Geist+Mono:wght@400;500&display=swap');
                @keyframes ws-spin{to{transform:rotate(360deg)}}
                @keyframes ws-pulse{0%,100%{opacity:1;transform:scale(1)}50%{opacity:.35;transform:scale(.55)}}
            `}</style>
            <div style={{display:'flex',flexDirection:'column',height:'100%',background:C.bg0,fontFamily:"'Outfit',sans-serif"}}>

                {/* tab bar */}
                <div style={{display:'flex',alignItems:'center',height:'46px',flexShrink:0,background:C.bg1,borderBottom:`1px solid ${C.border}`,padding:'0 4px',gap:2}}>
                    {TABS.map(t=>(
                        <button key={t.id} onClick={()=>switchTab(t.id)} style={{display:'flex',alignItems:'center',gap:5,padding:'5px 11px',border:'none',borderRadius:6,background:tab===t.id?C.bg3:'transparent',color:tab===t.id?C.t0:C.t2,cursor:'pointer',fontSize:'0.72rem',fontWeight:500,fontFamily:"'Outfit',sans-serif",transition:'all .14s',position:'relative'}}>
                            <span style={{color:tab===t.id?C.gold:'inherit'}}>{t.icon}</span>
                            {t.label}
                            {t.badge!=null&&(
                                <span style={{minWidth:15,height:15,borderRadius:7,background:typeof t.badge==='string'?'transparent':'rgba(245,166,35,.18)',color:typeof t.badge==='string'?C.red:C.gold,fontSize:'0.57rem',fontWeight:700,display:'flex',alignItems:'center',justifyContent:'center',padding:'0 3px'}}>{t.badge}</span>
                            )}
                        </button>
                    ))}
                    <button onClick={()=>{refreshFiles();refreshServers();}} title="Refresh" style={{marginLeft:'auto',background:'none',border:'none',color:C.t2,cursor:'pointer',padding:'4px 8px',display:'flex',alignItems:'center',borderRadius:5,transition:'color .15s'}} onMouseEnter={e=>e.currentTarget.style.color=C.t1} onMouseLeave={e=>e.currentTarget.style.color=C.t2}><RefreshCw size={12}/></button>
                </div>

                {/* tab body */}
                {tab==='code'&&<CodeTab files={files} workspaceEvents={workspaceEvents}/>}
                {tab==='output'&&<OutputTab lines={outputLines} running={isRunning}/>}
                {tab==='server'&&<ServerTab servers={servers} onStop={stopServer}/>}

                {/* collapsed system log */}
                <MiniLog log={agentLog} isLoading={isLogLoading}/>
            </div>
        </>
    );
};

export default WorkspacePanel;
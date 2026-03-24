import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { atomDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import {
    Copy, Check, Send, Sparkles, Bot, User, Code2,
    AtSign, FileText, X, ChevronRight, Clock, Play,
} from 'lucide-react';

const T = {
    bg0:'#0f0f0f',bg1:'#161616',bg2:'#1e1e1e',bg3:'#252525',bg4:'#2e2e2e',
    border:'rgba(255,255,255,0.08)',gold:'#f5a623',goldDim:'rgba(245,166,35,0.13)',
    goldGlow:'rgba(245,166,35,0.22)',goldTxt:'#fbbf24',
    text0:'#ececec',text1:'#a0a0a0',text2:'#606060',codeBg:'#0d0d0d',codeHead:'#141414',
};

const CSS=`
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=Instrument+Serif:ital@0;1&family=Geist+Mono:wght@400;500&display=swap');
@keyframes fadein   { from{opacity:0;transform:translateY(10px)} to{opacity:1;transform:translateY(0)} }
@keyframes bounce3  { 0%,60%,100%{transform:translateY(0);opacity:.5} 30%{transform:translateY(-5px);opacity:1} }
@keyframes statpls  { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:.4;transform:scale(.6)} }
@keyframes mention-pop { from{opacity:0;transform:translateY(6px) scale(0.97)} to{opacity:1;transform:translateY(0) scale(1)} }
@keyframes think-in    { from{opacity:0;transform:translateX(-4px)} to{opacity:1;transform:translateX(0)} }
@keyframes spin-slow   { to{transform:rotate(360deg)} }
@keyframes blink-cur   { 0%,100%{opacity:1} 50%{opacity:0} }
@keyframes agent-in    { from{opacity:0;transform:translateY(8px)} to{opacity:1;transform:translateY(0)} }
.chat-scroll::-webkit-scrollbar       { width:5px }
.chat-scroll::-webkit-scrollbar-track { background:transparent }
.chat-scroll::-webkit-scrollbar-thumb { background:rgba(255,255,255,.08);border-radius:3px }
.mention-dd::-webkit-scrollbar        { width:3px }
.mention-dd::-webkit-scrollbar-thumb  { background:rgba(255,255,255,.1);border-radius:2px }
.think-scroll::-webkit-scrollbar      { width:2px }
.think-scroll::-webkit-scrollbar-thumb{ background:rgba(255,255,255,.05);border-radius:2px }
.send-active:hover { background:#fbbf24!important;transform:translateY(-1px)!important }
.sugg-btn:hover    { background:#252525!important;border-color:rgba(245,166,35,.3)!important;color:#ececec!important;transform:translateY(-2px)!important }
/* Agent reply typography */
.agent-reply { font-family:'Outfit',sans-serif; animation: agent-in .35s ease both; }
.agent-reply p  { font-size:1rem; line-height:1.78; color:#dcdcdc; margin:0 0 14px; }
.agent-reply p:last-child { margin-bottom:0; }
.agent-reply h1 { font-family:'Instrument Serif',serif; font-size:1.45rem; font-weight:400; font-style:italic; color:#f0f0f0; margin:6px 0 20px; padding-bottom:14px; border-bottom:1px solid rgba(255,255,255,0.08); letter-spacing:-0.3px; }
.agent-reply h2 { font-size:1.05rem; font-weight:700; color:#fbbf24; margin:26px 0 12px; display:flex; align-items:center; gap:9px; }
.agent-reply h3 { font-size:0.97rem; font-weight:600; color:#93c5fd; margin:20px 0 9px; }
.agent-reply h4 { font-size:0.92rem; font-weight:600; color:#a0a0a0; margin:14px 0 7px; }
.agent-reply ul,.agent-reply ol { padding-left:24px; margin:6px 0 16px; }
.agent-reply li { font-size:1rem; line-height:1.74; color:#dcdcdc; margin-bottom:7px; }
.agent-reply li::marker { color:#f5a623; }
.agent-reply strong { color:#f0f0f0; font-weight:700; }
.agent-reply em { color:#a0a0a0; font-style:italic; }
.agent-reply a  { color:#fbbf24; text-decoration:none; border-bottom:1px dashed rgba(245,166,35,.4); transition:border-color .15s; }
.agent-reply a:hover { border-bottom-color:#fbbf24; }
.agent-reply blockquote { border-left:3px solid #f59e0b; background:rgba(245,158,11,.06); padding:12px 18px; border-radius:0 8px 8px 0; margin:14px 0; color:#fcd34d; font-style:italic; font-size:0.97rem; }
.agent-reply hr { border:none; border-top:1px solid rgba(255,255,255,.07); margin:22px 0; }
.agent-reply table-wrap { overflow-x:auto; margin:16px 0; border-radius:9px; border:1px solid rgba(255,255,255,0.08); }
.agent-reply table { width:100%; border-collapse:collapse; font-size:0.9rem; }
.agent-reply th { background:#252525; color:#fbbf24; padding:10px 15px; text-align:left; font-size:0.73rem; font-weight:700; letter-spacing:.5px; text-transform:uppercase; border-bottom:1px solid rgba(255,255,255,.08); }
.agent-reply td { padding:9px 15px; color:#dcdcdc; border-bottom:1px solid rgba(255,255,255,.04); }
.agent-reply tr:last-child td { border-bottom:none; }
`;
let _inj=false;
function injectStyles(){if(_inj)return;_inj=true;const s=document.createElement('style');s.textContent=CSS;document.head.appendChild(s);}



/* ── Inline Thinking Panel ──────────────────────────────── */
const ThinkingPanel=({logs=[],isActive,elapsed})=>{
    const[open,setOpen]=useState(true);
    const btmRef=useRef(null);
    useEffect(()=>{if(isActive)setOpen(true);},[isActive]);
    useEffect(()=>{if(open&&isActive)btmRef.current?.scrollIntoView({behavior:'smooth',block:'nearest'});},[logs,open,isActive]);
    if(logs.length===0&&!isActive)return null;
    const label=isActive?`Thinking…${elapsed>0?` ${elapsed}s`:''}`:` Thought for ${elapsed}s`;
    return(
        <div style={{marginTop:'8px',marginLeft:'44px',animation:'fadein 0.3s ease both'}}>
            <button onClick={()=>setOpen(v=>!v)} style={{display:'flex',alignItems:'center',gap:'5px',background:'none',border:'none',cursor:'pointer',padding:'3px 0',color:T.text2,fontFamily:"'Outfit',sans-serif",fontSize:'0.72rem',fontWeight:500,userSelect:'none'}}>
                {isActive?(
                    <span style={{display:'inline-block',width:'12px',height:'12px',border:'1.5px solid rgba(245,166,35,0.22)',borderTopColor:T.gold,borderRadius:'50%',animation:'spin-slow 0.9s linear infinite',flexShrink:0}}/>
                ):(
                    <Clock size={12} style={{color:T.text2,flexShrink:0}}/>
                )}
                <span style={{color:isActive?T.goldTxt:T.text2}}>{label}</span>
                <ChevronRight size={12} style={{color:T.text2,transform:open?'rotate(90deg)':'rotate(0deg)',transition:'transform 0.2s'}}/>
            </button>
            {open&&(
                <div className="think-scroll" style={{marginTop:'6px',background:'rgba(255,255,255,0.018)',border:`1px solid ${T.border}`,borderLeft:'2px solid rgba(245,166,35,0.2)',borderRadius:'0 8px 8px 8px',padding:'8px 12px',maxHeight:'180px',overflowY:'auto',display:'flex',flexDirection:'column',gap:'3px'}}>
                    {logs.map((entry,i)=>{
                        const isLast=i===logs.length-1;
                        // Clean the leading whitespace + ↳ for display, keep the rest
                        const clean=entry.replace(/^ *↳ */,'');
                        return(
                            <div key={i} style={{display:'flex',alignItems:'flex-start',gap:'7px',animation:'think-in 0.18s ease both',animationDelay:`${i*0.012}s`}}>
                                <span style={{color:'rgba(245,166,35,0.5)',fontSize:'0.7rem',flexShrink:0,marginTop:'1px',fontFamily:"'Geist Mono',monospace"}}>↳</span>
                                <span style={{fontFamily:"'Outfit',sans-serif",fontSize:'0.72rem',color:isLast&&isActive?T.text1:T.text2,lineHeight:1.5,wordBreak:'break-word',flex:1}}>
                                    {clean}
                                    {isLast&&isActive&&(
                                        <span style={{display:'inline-block',width:'5px',height:'0.8em',background:T.gold,marginLeft:'3px',borderRadius:'1px',verticalAlign:'text-bottom',animation:'blink-cur 0.9s step-end infinite'}}/>
                                    )}
                                </span>
                            </div>
                        );
                    })}
                    <div ref={btmRef}/>
                </div>
            )}
        </div>
    );
};

/* ── Copy button (icon only) ─────────────────────────────── */
const CopyBtn=({text})=>{
    const[done,setDone]=useState(false);
    const go=async()=>{try{await navigator.clipboard.writeText(text);}catch{}setDone(true);setTimeout(()=>setDone(false),2400);};
    return(
        <button onClick={go} title={done?'Copied!':'Copy'} style={{display:'flex',alignItems:'center',justifyContent:'center',width:'28px',height:'28px',background:done?'rgba(34,197,94,.12)':'rgba(255,255,255,.06)',border:`1px solid ${done?'rgba(34,197,94,.3)':'rgba(255,255,255,.1)'}`,borderRadius:'6px',color:done?'#4ade80':T.text1,cursor:'pointer',transition:'all .18s',flexShrink:0}}>
            {done?<Check size={13}/>:<Copy size={13}/>}
        </button>
    );
};

/* ── Code block ──────────────────────────────────────────── */
const CodeBlock=({language,code,onRun})=>{
    const lang=(language||'text').toLowerCase().replace(/^language-/,'');
    const[running,setRunning]=useState(false);
    const runnable=['python','py','bash','sh','javascript','js','node','typescript','ts'].includes(lang);
    const handleRun=async()=>{
        if(running||!onRun)return;
        setRunning(true);
        try{await onRun(code,lang);}catch{}
        setTimeout(()=>setRunning(false),1500);
    };
    return(
        <div style={{margin:'16px 0',borderRadius:'10px',overflow:'hidden',border:'1px solid rgba(255,255,255,.1)',background:T.codeBg,boxShadow:'0 4px 24px rgba(0,0,0,.55)'}}>
            <div style={{display:'flex',alignItems:'center',justifyContent:'space-between',padding:'8px 14px',background:T.codeHead,borderBottom:'1px solid rgba(255,255,255,.08)',gap:'12px'}}>
                <div style={{display:'flex',gap:'5px',flexShrink:0}}>{['#ff5f57','#febc2e','#28c840'].map((c,i)=><span key={i} style={{width:'10px',height:'10px',background:c,borderRadius:'50%',display:'block'}}/>)}</div>
                <span style={{flex:1,textAlign:'center',fontFamily:"'Geist Mono',monospace",fontSize:'0.63rem',fontWeight:500,color:T.text2,letterSpacing:'1.1px',textTransform:'uppercase'}}>{lang}</span>
                <div style={{display:'flex',gap:'6px',alignItems:'center'}}>
                    <CopyBtn text={code}/>
                    {runnable&&(
                        <button onClick={handleRun} title="Run in Workspace Output" style={{display:'flex',alignItems:'center',justifyContent:'center',width:'28px',height:'28px',background:running?'rgba(34,197,94,.15)':'rgba(245,166,35,.1)',border:`1px solid ${running?'rgba(34,197,94,.3)':'rgba(245,166,35,.28)'}`,borderRadius:'6px',color:running?'#4ade80':'#f5a623',cursor:'pointer',transition:'all .18s',flexShrink:0}}>
                            {running?<Check size={13}/>:<Play size={13}/>}
                        </button>
                    )}
                </div>
            </div>
            <SyntaxHighlighter style={atomDark} language={lang} PreTag="div" showLineNumbers wrapLongLines={false} customStyle={{margin:0,padding:'16px 18px',background:T.codeBg,fontSize:'0.81rem',lineHeight:'1.68',maxHeight:'540px',overflowY:'auto',overflowX:'auto',borderRadius:0,fontFamily:"'Geist Mono','Fira Code',monospace"}} lineNumberStyle={{color:'#2a2a2a',minWidth:'2.4em',paddingRight:'14px',userSelect:'none',fontSize:'0.72rem'}}>{String(code).replace(/\n$/,'')}</SyntaxHighlighter>
        </div>
    );
};

const IC=({children})=>(<code style={{fontFamily:"'Geist Mono',monospace",fontSize:'0.78em',background:'rgba(245,166,35,.1)',border:'1px solid rgba(245,166,35,.18)',color:T.goldTxt,padding:'2px 6px',borderRadius:'4px',wordBreak:'break-word'}}>{children}</code>);

const mkComponents=(onRun)=>({
    code({node,inline,className,children}){const lang=/language-(\w+)/.exec(className||'')?.[1];const raw=String(children);if(!inline&&(lang||raw.includes('\n')))return<CodeBlock language={lang||'text'} code={raw.replace(/\n$/,'')} onRun={onRun}/>;return<IC>{children}</IC>;},
    pre({children}){return<>{children}</>;},
    h1:({children})=><h1>{children}</h1>,
    h2:({children})=><h2><span style={{width:'3px',height:'1em',background:T.gold,borderRadius:'2px',display:'inline-block',flexShrink:0,verticalAlign:'middle',marginRight:'4px'}}/>{children}</h2>,
    h3:({children})=><h3>{children}</h3>,
    h4:({children})=><h4>{children}</h4>,
    p:({children})=><p>{children}</p>,
    ul:({children})=><ul>{children}</ul>,
    ol:({children})=><ol>{children}</ol>,
    li:({children})=><li>{children}</li>,
    blockquote:({children})=><blockquote>{children}</blockquote>,
    hr:()=><hr/>,
    strong:({children})=><strong>{children}</strong>,
    em:({children})=><em>{children}</em>,
    a:({href,children})=><a href={href} target="_blank" rel="noopener noreferrer">{children}</a>,
    table:({children})=><div style={{overflowX:'auto',margin:'16px 0',borderRadius:'9px',border:`1px solid ${T.border}`}}><table style={{width:'100%',borderCollapse:'collapse'}}>{children}</table></div>,
    th:({children})=><th>{children}</th>,
    td:({children})=><td>{children}</td>,
    tr:({children})=><tr>{children}</tr>,
    thead:({children})=><thead>{children}</thead>,
    tbody:({children})=><tbody>{children}</tbody>,
});

/* ── Mention chip & dropdown ─────────────────────────────── */
const MentionChip=({filename,onRemove})=>(<span style={{display:'inline-flex',alignItems:'center',gap:'4px',padding:'2px 8px',background:'rgba(245,166,35,0.12)',border:'1px solid rgba(245,166,35,0.3)',borderRadius:'12px',color:'#fbbf24',fontSize:'0.72rem',fontWeight:600,fontFamily:"'Geist Mono',monospace",whiteSpace:'nowrap',flexShrink:0}}><AtSign size={10}/>{filename}<button onClick={onRemove} style={{background:'none',border:'none',color:'#fbbf24',cursor:'pointer',padding:'0 0 0 2px',display:'flex',alignItems:'center',opacity:0.7}}><X size={10}/></button></span>);

const MentionDropdown=({files,query,onSelect,onClose})=>{
    const filtered=files.filter(f=>f.name.toLowerCase().includes(query.toLowerCase()));
    if(!filtered.length)return null;
    return(<div className="mention-dd" style={{position:'absolute',bottom:'100%',left:0,right:0,marginBottom:'6px',background:'#161616',border:'1px solid rgba(245,166,35,0.3)',borderRadius:'10px',overflow:'hidden',boxShadow:'0 8px 32px rgba(0,0,0,0.65)',zIndex:50,animation:'mention-pop 0.18s ease both',maxHeight:'200px',overflowY:'auto'}}>
        <div style={{padding:'7px 12px',borderBottom:'1px solid rgba(255,255,255,0.07)',display:'flex',alignItems:'center',justifyContent:'space-between'}}>
            <span style={{fontSize:'0.62rem',fontWeight:700,letterSpacing:'0.8px',textTransform:'uppercase',color:'#606060'}}>Reference a file</span>
            <button onClick={onClose} style={{background:'none',border:'none',color:'#606060',cursor:'pointer',padding:0,display:'flex'}}><X size={12}/></button>
        </div>
        {filtered.map(f=>(<button key={f.name} onMouseDown={e=>{e.preventDefault();onSelect(f.name);}} style={{display:'flex',alignItems:'center',gap:'10px',width:'100%',padding:'9px 12px',background:'transparent',border:'none',cursor:'pointer',textAlign:'left',borderBottom:'1px solid rgba(255,255,255,0.04)',transition:'background 0.15s'}} onMouseEnter={e=>e.currentTarget.style.background='rgba(245,166,35,0.07)'} onMouseLeave={e=>e.currentTarget.style.background='transparent'}>
            <div style={{width:'28px',height:'28px',borderRadius:'6px',background:'rgba(245,166,35,0.1)',border:'1px solid rgba(245,166,35,0.2)',display:'flex',alignItems:'center',justifyContent:'center',color:'#f5a623',flexShrink:0}}><FileText size={13}/></div>
            <div style={{flex:1,minWidth:0}}>
                <div style={{fontSize:'0.78rem',fontWeight:600,color:'#d4d4d4',whiteSpace:'nowrap',overflow:'hidden',textOverflow:'ellipsis'}}>{f.name}</div>
                <div style={{fontSize:'0.6rem',color:'#4a4a4a',fontFamily:"'Geist Mono',monospace"}}>{f.ext?.toUpperCase()} · {f.size?(f.size/1024).toFixed(1)+' KB':'—'}</div>
            </div>
            <span style={{fontSize:'0.6rem',color:'#fbbf24',background:'rgba(245,166,35,0.08)',border:'1px solid rgba(245,166,35,0.15)',borderRadius:'4px',padding:'1px 5px',fontFamily:"'Geist Mono',monospace",flexShrink:0}}>@{f.name}</span>
        </button>))}
    </div>);
};

/* ── Message row ─────────────────────────────────────────── */
const MessageRow=React.memo(({msg,thinkLogs,thinkActive,thinkElapsed,onRunCode})=>{
    const comps=useMemo(()=>mkComponents(onRunCode),[onRunCode]);
    const isUser=msg.sender==='user';

    if(isUser) return(
        <div style={{display:'flex',flexDirection:'column',alignItems:'flex-end',padding:'10px 0 4px',animation:'fadein .22s ease both'}}>
            <div style={{maxWidth:'min(72%,640px)',background:'rgba(255,255,255,0.06)',border:'1px solid rgba(255,255,255,0.1)',borderRadius:'18px 4px 18px 18px',padding:'13px 19px',color:'#e8e8e8',fontSize:'1rem',lineHeight:1.65,fontFamily:"'Outfit',sans-serif",wordBreak:'break-word',letterSpacing:'0.01em'}}>
                {msg.text}
            </div>
            {(thinkLogs?.length>0||thinkActive)&&(
                <div style={{width:'100%',marginTop:'4px'}}>
                    <ThinkingPanel logs={thinkLogs||[]} isActive={thinkActive} elapsed={thinkElapsed||0}/>
                </div>
            )}
        </div>
    );

    return(
        <div style={{display:'flex',gap:'16px',alignItems:'flex-start',padding:'16px 0 18px',animation:'fadein .3s ease both',borderBottom:'1px solid rgba(255,255,255,0.04)'}}>
            <div style={{width:'34px',height:'34px',borderRadius:'10px',flexShrink:0,marginTop:'2px',background:'rgba(245,166,35,0.1)',border:'1px solid rgba(245,166,35,0.22)',display:'flex',alignItems:'center',justifyContent:'center',color:T.gold}}>
                <Bot size={16}/>
            </div>
            <div style={{flex:1,minWidth:0,paddingTop:'2px'}}>
                <div className="agent-reply">
                    <ReactMarkdown remarkPlugins={[remarkGfm]} components={comps}>{msg.text}</ReactMarkdown>
                </div>
            </div>
        </div>
    );
});

/* ── Empty state ─────────────────────────────────────────── */
const SUGG=[{label:'Write code',text:'Write a Python function to sort a list of dicts by a key'},{label:'Debug',text:'Why is my recursive function hitting a stack overflow?'},{label:'Analyze file',text:'Summarize the key points from @your-document.pdf'},{label:'Explain',text:'Explain async/await in JavaScript with examples'}];
const EmptyState=({onSuggestion})=>(<div style={{flex:1,display:'flex',flexDirection:'column',alignItems:'center',justifyContent:'center',textAlign:'center',padding:'40px 24px',animation:'fadein .5s ease both'}}><div style={{width:'72px',height:'72px',background:T.bg2,border:'1px solid rgba(245,166,35,.25)',borderRadius:'22px',display:'flex',alignItems:'center',justifyContent:'center',color:T.gold,marginBottom:'20px',boxShadow:`0 0 40px ${T.goldGlow}`}}><Sparkles size={30}/></div><h2 style={{fontFamily:"'Instrument Serif',serif",fontSize:'1.7rem',fontWeight:400,fontStyle:'italic',color:T.text0,margin:'0 0 10px',letterSpacing:'-0.3px'}}>How can I help you today?</h2><p style={{fontSize:'0.875rem',color:T.text1,margin:'0 0 28px',maxWidth:'360px',lineHeight:1.6}}>Ask a question, generate code, or type <strong style={{color:T.goldTxt}}>@filename</strong> to query a document.</p><div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:'8px',width:'100%',maxWidth:'560px'}}>{SUGG.map(s=>(<button key={s.label} className="sugg-btn" onClick={()=>onSuggestion(s.text)} style={{background:T.bg2,border:`1px solid ${T.border}`,borderRadius:'12px',padding:'12px 14px',textAlign:'left',cursor:'pointer',color:T.text1,fontSize:'0.8rem',lineHeight:1.45,fontFamily:"'Outfit',sans-serif",transition:'all .2s ease'}}><strong style={{display:'block',fontSize:'0.75rem',fontWeight:600,color:T.goldTxt,marginBottom:'3px'}}>{s.label}</strong>{s.text}</button>))}</div></div>);

/* ══════════════════════════════════════════════════════════
   MAIN CHAT
══════════════════════════════════════════════════════════ */
const Chat=({setAgentLog,setIsLogLoading,pendingMention,onWorkspaceEvent,onRunCode})=>{
    const[messages,setMessages]=useState([]);
    const[input,setInput]=useState('');
    const[isLoading,setIsLoading]=useState(false);
    const[mentionQuery,setMentionQuery]=useState('');
    const[showDropdown,setShowDropdown]=useState(false);
    const[mentionedFiles,setMentionedFiles]=useState([]);
    const[availableFiles,setAvailableFiles]=useState([]);
    // Inline thought state
    const[thinkLogs,setThinkLogs]=useState([]);
    const[thinkActive,setThinkActive]=useState(false);
    const[thinkElapsed,setThinkElapsed]=useState(0);
    const winRef=useRef(null);const taRef=useRef(null);
    const timerRef=useRef(null);const startRef=useRef(null);

    useEffect(()=>{injectStyles();},[]);
    useEffect(()=>{fetch('http://localhost:5000/api/files').then(r=>r.ok?r.json():[]).then(d=>setAvailableFiles(Array.isArray(d)?d:[])).catch(()=>{});},[]);
    useEffect(()=>{if(!pendingMention)return;const name=pendingMention.replace(/^@/,'');setMentionedFiles(prev=>prev.includes(name)?prev:[...prev,name]);},[pendingMention]);
    useEffect(()=>{winRef.current?.scrollTo({top:winRef.current.scrollHeight,behavior:'smooth'});},[messages,thinkLogs,isLoading]);
    useEffect(()=>{const ta=taRef.current;if(!ta)return;ta.style.height='auto';ta.style.height=Math.min(ta.scrollHeight,140)+'px';},[input]);

    const startTimer=()=>{startRef.current=Date.now();setThinkElapsed(0);timerRef.current=setInterval(()=>setThinkElapsed(Math.floor((Date.now()-startRef.current)/1000)),1000);};
    const stopTimer=()=>{clearInterval(timerRef.current);setThinkElapsed(Math.floor((Date.now()-(startRef.current||Date.now()))/1000));};

    const addChip=(f)=>{setMentionedFiles(prev=>prev.includes(f)?prev:[...prev,f]);setInput(prev=>prev.replace(/@[\w\-. ]*$/,''));setShowDropdown(false);};
    const removeChip=(f)=>setMentionedFiles(prev=>prev.filter(x=>x!==f));
    const handleInputChange=(e)=>{const val=e.target.value;setInput(val);const m=val.match(/@([\w\-. ]*)$/);if(m){setMentionQuery(m[1]);setShowDropdown(true);}else setShowDropdown(false);};
    const buildMsg=()=>{const chips=mentionedFiles.map(f=>`@${f}`).join(' ');return(chips?`${chips} `:'')+input.trim();};

    const send=useCallback(async(override)=>{
        const finalMsg=override??buildMsg();
        if(!finalMsg.trim()||isLoading)return;
        setMessages(p=>[...p,{text:finalMsg,sender:'user'}]);
        setInput('');setMentionedFiles([]);setShowDropdown(false);
        setIsLoading(true);setIsLogLoading(true);setAgentLog([]);
        setThinkLogs([]);setThinkActive(true);startTimer();
        const history=messages.slice(-6).map(m=>[m.sender==='user'?m.text:'',m.sender==='agent'?m.text:'']);
        try{
            const res=await fetch('http://localhost:5000/api/chat/stream',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:finalMsg,history})});
            if(!res.ok)throw new Error(`Server error ${res.status}`);
            const reader=res.body.getReader();const decoder=new TextDecoder();let buffer='';
            const processChunk=(chunk)=>{
                buffer+=chunk;const frames=buffer.split('\n\n');buffer=frames.pop();
                for(const frame of frames){
                    if(!frame.trim()||frame.startsWith(':'))continue;
                    let eventType='message',dataLine='';
                    for(const line of frame.split('\n')){if(line.startsWith('event: '))eventType=line.slice(7).trim();if(line.startsWith('data: '))dataLine=line.slice(6).trim();}
                    if(!dataLine)continue;
                    let payload;try{payload=JSON.parse(dataLine);}catch{continue;}
                    if(eventType==='log'){
                        setAgentLog(prev=>[...prev,payload.entry]);
                        if(/^ *↳/.test(payload.entry)){setThinkLogs(prev=>[...prev,payload.entry]);}
                    }else if(eventType==='workspace_event'){
                        if(typeof onWorkspaceEvent==='function')onWorkspaceEvent(payload);
                    }else if(eventType==='answer'){
                        stopTimer();setThinkActive(false);
                        setMessages(p=>[...p,{text:payload.text,sender:'agent'}]);
                        setIsLoading(false);setIsLogLoading(false);
                    }else if(eventType==='error'){
                        stopTimer();setThinkActive(false);
                        setMessages(p=>[...p,{text:`⚠️ **Agent error**\n\n\`\`\`\n${payload.message}\n\`\`\``,sender:'agent'}]);
                        setIsLoading(false);setIsLogLoading(false);
                    }else if(eventType==='done'){
                        stopTimer();setThinkActive(false);setIsLoading(false);setIsLogLoading(false);
                    }
                }
            };
            while(true){const{value,done}=await reader.read();if(done)break;processChunk(decoder.decode(value,{stream:true}));}
            if(buffer.trim())processChunk('');
        }catch(err){
            stopTimer();setThinkActive(false);
            setMessages(p=>[...p,{text:`⚠️ **Connection error**\n\n\`\`\`\n${err.message}\n\`\`\`\n\nMake sure Flask is running on **port 5000**.`,sender:'agent'}]);
            setIsLoading(false);setIsLogLoading(false);
        }finally{
            taRef.current?.focus();
            fetch('http://localhost:5000/api/files').then(r=>r.json()).then(d=>setAvailableFiles(Array.isArray(d)?d:[])).catch(()=>{});
        }
    },[input,mentionedFiles,isLoading,messages,setAgentLog,setIsLogLoading]);

    const onKey=(e)=>{if(e.key==='Escape'){setShowDropdown(false);return;}if(e.key==='Enter'&&!e.shiftKey&&!showDropdown){e.preventDefault();send();}};
    const hasContent=input.trim().length>0||mentionedFiles.length>0;

    // Which user-message index currently owns the live thought panel
    const pendingUserIdx=(isLoading||thinkActive)?messages.filter(m=>m.sender==='user').length-1:-1;
    let userCount=-1;

    return(
        <div style={{display:'flex',flexDirection:'column',height:'100%',background:T.bg0,fontFamily:"'Outfit',sans-serif"}}>
            {/* Header */}
            <div style={{display:'flex',alignItems:'center',justifyContent:'space-between',padding:'0 24px',height:'54px',flexShrink:0,background:'rgba(15,15,15,.9)',backdropFilter:'blur(12px)',borderBottom:`1px solid ${T.border}`}}>
                <div style={{display:'flex',alignItems:'center',gap:'10px'}}>
                    <div style={{width:'28px',height:'28px',background:T.goldDim,border:'1px solid rgba(245,166,35,.22)',borderRadius:'7px',display:'flex',alignItems:'center',justifyContent:'center',color:T.gold}}><Code2 size={13}/></div>
                    <span style={{fontSize:'0.875rem',fontWeight:600,color:T.text0}}>Conversation</span>
                    <span style={{fontSize:'0.62rem',fontWeight:600,padding:'2px 8px',background:T.goldDim,border:'1px solid rgba(245,166,35,.2)',borderRadius:'20px',color:T.goldTxt,letterSpacing:'0.4px',textTransform:'uppercase'}}>AI Agent</span>
                </div>
                <div style={{display:'flex',alignItems:'center',gap:'6px',opacity:isLoading?1:0,transition:'opacity .2s'}}>
                    <span style={{width:'6px',height:'6px',background:T.gold,borderRadius:'50%',animation:isLoading?'statpls 1.2s ease-in-out infinite':'none'}}/>
                    <span style={{fontSize:'0.72rem',color:T.text1}}>Thinking…</span>
                </div>
            </div>

            {/* Messages */}
            <div className="chat-scroll" ref={winRef} style={{flex:1,overflowY:'auto',overflowX:'hidden',padding:'28px 24px 20px',display:'flex',flexDirection:'column',scrollBehavior:'smooth'}}>
                {messages.length===0?<EmptyState onSuggestion={t=>send(t)}/>:(
                    <div style={{width:'100%',maxWidth:'780px',margin:'0 auto',display:'flex',flexDirection:'column',gap:'4px'}}>
                        {messages.map((m,i)=>{
                            if(m.sender==='user')userCount++;
                            const isLastUser=m.sender==='user'&&userCount===pendingUserIdx;
                            return(
                                <MessageRow key={i} msg={m}
                                    thinkLogs={isLastUser?thinkLogs:undefined}
                                    thinkActive={isLastUser?thinkActive:false}
                                    thinkElapsed={isLastUser?thinkElapsed:0}
                                />
                            );
                        })}
                    </div>
                )}
            </div>

            {/* Input */}
            <div style={{padding:'14px 24px 18px',flexShrink:0,background:'rgba(15,15,15,.92)',backdropFilter:'blur(12px)',borderTop:`1px solid ${T.border}`}}>
                <div style={{maxWidth:'780px',margin:'0 auto',position:'relative'}}>
                    {showDropdown&&<MentionDropdown files={availableFiles} query={mentionQuery} onSelect={addChip} onClose={()=>setShowDropdown(false)}/>}
                    <div style={{display:'flex',alignItems:'flex-end',gap:'10px',background:T.bg2,border:`1px solid ${hasContent?'rgba(245,166,35,.4)':T.border}`,borderRadius:'16px',padding:'10px 12px',boxShadow:hasContent?'0 0 0 3px rgba(245,166,35,.07)':'none',transition:'border-color .2s,box-shadow .2s',flexWrap:'wrap'}}>
                        {mentionedFiles.map(f=><MentionChip key={f} filename={f} onRemove={()=>removeChip(f)}/>)}
                        <textarea ref={taRef} value={input} onChange={handleInputChange} onKeyDown={onKey}
                            placeholder={mentionedFiles.length?'Ask something about these files…':'Message the agent… (@ to reference a file)'}
                            disabled={isLoading} rows={1}
                            style={{flex:1,background:'transparent',border:'none',outline:'none',resize:'none',color:T.text0,fontFamily:"'Outfit',sans-serif",fontSize:'0.9rem',lineHeight:1.5,padding:'4px',minHeight:'22px',maxHeight:'140px',overflowY:'auto',minWidth:'120px'}}
                        />
                        <button className={hasContent&&!isLoading?'send-active':''} onClick={()=>send()} disabled={isLoading||!hasContent}
                            style={{width:'38px',height:'38px',borderRadius:'10px',border:'none',background:hasContent&&!isLoading?T.gold:T.bg4,color:hasContent&&!isLoading?'#0f0f0f':T.text2,display:'flex',alignItems:'center',justifyContent:'center',cursor:hasContent&&!isLoading?'pointer':'not-allowed',flexShrink:0,transition:'all .2s',boxShadow:hasContent&&!isLoading?`0 2px 16px ${T.goldGlow}`:'none',alignSelf:'flex-end'}}>
                            <Send size={16}/>
                        </button>
                    </div>
                    <p style={{textAlign:'center',fontSize:'0.62rem',color:T.text2,margin:'8px 0 0'}}>
                        Type <strong style={{color:T.goldTxt}}>@filename</strong> to query a document · Enter to send
                    </p>
                </div>
            </div>
        </div>
    );
};

export default Chat;
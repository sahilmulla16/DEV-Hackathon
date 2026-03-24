import React, { useState, useRef, useEffect } from 'react';
import { Download, Maximize2, Minimize2, BarChart2, Box, Image as ImgIcon } from 'lucide-react';

/**
 * VisualizationPanel
 *
 * Renders a grid of visualization assets returned by the coding agent.
 * Each asset: { name, type: 'image' | 'html', data: string (base64 or raw HTML) }
 *
 * Matches the Noir Studio design system used throughout the project.
 */

/* ─── Type metadata ─────────────────────────────────────── */
const typeLabel = (type) => {
    if (type === 'html')  return { icon: <BarChart2 size={13}/>, label:'Interactive', color:'#34d399' };
    if (type === '3d')    return { icon: <Box size={13}/>,       label:'3D View',     color:'#a78bfa' };
    return                       { icon: <ImgIcon size={13}/>,  label:'2D Chart',    color:'#60a5fa' };
};

/* ─── Download helpers ──────────────────────────────────── */
const downloadBlob = (data, filename, mime) => {
    const blob = new Blob([data], { type: mime });
    const url  = URL.createObjectURL(blob);
    const a    = Object.assign(document.createElement('a'), { href: url, download: filename });
    a.click();
    URL.revokeObjectURL(url);
};

/* ─── Single visualization card ────────────────────────── */
const VisCard = ({ asset }) => {
    const [expanded, setExpanded]   = useState(false);
    const [loaded,   setLoaded]     = useState(false);
    const iframeRef                 = useRef(null);
    const meta                      = typeLabel(asset.type);

    // Auto-resize iframe height based on content
    useEffect(() => {
        if (asset.type !== 'html' || !iframeRef.current) return;
        const handler = (e) => {
            if (e.data?.type === 'viz-height' && iframeRef.current) {
                const h = Math.min(Math.max(e.data.height + 16, 260), 640);
                iframeRef.current.style.height = `${h}px`;
                setLoaded(true);
            }
        };
        window.addEventListener('message', handler);
        return () => window.removeEventListener('message', handler);
    }, [asset.type]);

    const handleDownload = () => {
        if (asset.type === 'html') {
            downloadBlob(asset.data, `${asset.name}.html`, 'text/html');
        } else {
            // base64 PNG
            const link = document.createElement('a');
            link.href     = `data:image/png;base64,${asset.data}`;
            link.download = `${asset.name}.png`;
            link.click();
        }
    };

    // Inject resize postMessage into HTML
    const srcDoc = asset.type === 'html'
        ? asset.data.replace(
            '</body>',
            `<script>
                function _sendH() { window.parent.postMessage({ type:'viz-height', height: document.body.scrollHeight }, '*'); }
                window.addEventListener('load', _sendH);
                window.addEventListener('resize', _sendH);
            </script></body>`
        )
        : '';

    return (
        <div style={{
            border:       '1px solid rgba(255,255,255,0.08)',
            borderRadius: '12px',
            overflow:     'hidden',
            background:   '#0e0e0e',
            boxShadow:    '0 4px 20px rgba(0,0,0,0.5)',
            ...(expanded ? {
                position:'fixed', inset:'28px', zIndex:1000,
                borderRadius:'16px',
                boxShadow:'0 24px 80px rgba(0,0,0,0.85)',
            } : {}),
        }}>
            {/* Header */}
            <div style={{ display:'flex', alignItems:'center', justifyContent:'space-between', padding:'9px 14px', background:'#141414', borderBottom:'1px solid rgba(255,255,255,0.07)', gap:'10px' }}>
                <div style={{ display:'flex', alignItems:'center', gap:'7px' }}>
                    <span style={{ color: meta.color }}>{meta.icon}</span>
                    <span style={{ fontSize:'0.72rem', fontWeight:600, color:meta.color, letterSpacing:'0.3px', textTransform:'uppercase' }}>{meta.label}</span>
                    <span style={{ fontSize:'0.72rem', color:'#606060' }}>—</span>
                    <span style={{ fontSize:'0.72rem', color:'#a0a0a0', fontFamily:"'Geist Mono',monospace" }}>{asset.name}</span>
                    {!loaded && asset.type === 'html' && (
                        <span style={{ fontSize:'0.62rem', color:'#606060', fontStyle:'italic' }}>Rendering…</span>
                    )}
                    {(loaded || asset.type !== 'html') && (
                        <span style={{ fontSize:'0.62rem', color:'#34d399', background:'rgba(34,197,94,0.08)', border:'1px solid rgba(34,197,94,0.18)', borderRadius:'10px', padding:'1px 6px' }}>✓ Ready</span>
                    )}
                </div>
                <div style={{ display:'flex', gap:'6px' }}>
                    <button onClick={handleDownload} style={{ display:'flex',alignItems:'center',gap:'4px',padding:'4px 9px',background:'rgba(255,255,255,0.05)',border:'1px solid rgba(255,255,255,0.1)',borderRadius:'5px',color:'#a0a0a0',fontSize:'0.67rem',cursor:'pointer',fontFamily:"'Outfit',sans-serif",transition:'all .2s' }}
                        onMouseEnter={e => { e.currentTarget.style.color='#ececec'; e.currentTarget.style.background='rgba(255,255,255,.09)'; }}
                        onMouseLeave={e => { e.currentTarget.style.color='#a0a0a0'; e.currentTarget.style.background='rgba(255,255,255,.05)'; }}
                    >
                        <Download size={11}/> <span>Save</span>
                    </button>
                    <button onClick={() => setExpanded(v => !v)} style={{ display:'flex',alignItems:'center',gap:'4px',padding:'4px 9px',background:'rgba(255,255,255,0.05)',border:'1px solid rgba(255,255,255,0.1)',borderRadius:'5px',color:'#a0a0a0',fontSize:'0.67rem',cursor:'pointer',fontFamily:"'Outfit',sans-serif",transition:'all .2s' }}
                        onMouseEnter={e => { e.currentTarget.style.color='#ececec'; e.currentTarget.style.background='rgba(255,255,255,.09)'; }}
                        onMouseLeave={e => { e.currentTarget.style.color='#a0a0a0'; e.currentTarget.style.background='rgba(255,255,255,.05)'; }}
                    >
                        {expanded ? <Minimize2 size={11}/> : <Maximize2 size={11}/>}
                        <span>{expanded ? 'Collapse' : 'Expand'}</span>
                    </button>
                </div>
            </div>

            {/* Body */}
            <div style={{ background:'rgba(0,0,0,0.3)', minHeight:'120px', display:'flex', alignItems:'center', justifyContent:'center' }}>
                {asset.type === 'image' ? (
                    <div style={{ padding:'16px', width:'100%', display:'flex', justifyContent:'center' }}>
                        <img
                            src={`data:image/png;base64,${asset.data}`}
                            alt={asset.name}
                            onLoad={() => setLoaded(true)}
                            style={{ maxWidth:'100%', maxHeight: expanded ? 'calc(100vh - 120px)' : '560px', borderRadius:'6px', objectFit:'contain', boxShadow:'0 2px 16px rgba(0,0,0,0.5)' }}
                        />
                    </div>
                ) : (
                    <iframe
                        ref={iframeRef}
                        srcDoc={srcDoc}
                        title={asset.name}
                        sandbox="allow-scripts allow-same-origin"
                        style={{ width:'100%', height: expanded ? 'calc(100vh - 80px)' : '460px', border:'none', display:'block', background:'#fff', transition:'height .3s ease' }}
                    />
                )}
            </div>
        </div>
    );
};

/* ─── Main panel ────────────────────────────────────────── */
const VisualizationPanel = ({ vizData }) => {
    if (!vizData || vizData.length === 0) return null;

    return (
        <div style={{ marginTop:'20px', borderTop:'1px solid rgba(255,255,255,0.07)', paddingTop:'20px' }}>
            {/* Section header */}
            <div style={{ display:'flex', alignItems:'center', gap:'10px', marginBottom:'14px' }}>
                <div style={{ width:'3px', height:'1em', background:'#f5a623', borderRadius:'2px' }} />
                <span style={{ fontSize:'0.75rem', fontWeight:700, color:'#fbbf24', letterSpacing:'0.5px', textTransform:'uppercase' }}>
                    Visualization Output
                </span>
                <span style={{ fontSize:'0.65rem', color:'#606060', background:'rgba(255,255,255,0.04)', border:'1px solid rgba(255,255,255,0.07)', borderRadius:'10px', padding:'1px 7px' }}>
                    {vizData.length} chart{vizData.length !== 1 ? 's' : ''}
                </span>
            </div>

            {/* Cards grid */}
            <div style={{ display:'flex', flexDirection:'column', gap:'16px' }}>
                {vizData.map((asset, i) => <VisCard key={i} asset={asset} />)}
            </div>
        </div>
    );
};

export default VisualizationPanel;
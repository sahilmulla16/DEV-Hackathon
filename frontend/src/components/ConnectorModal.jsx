import React, { useState, useEffect, useCallback } from 'react';
import {
    X, Check, ChevronRight, Key, Eye, EyeOff,
    Zap, Trash2, AlertCircle, ExternalLink,
} from 'lucide-react';

import { testConnector } from '../services/api';
// ── Design tokens ──────────────────────────────────────────────
const C = {
    bg0: '#080809',
    bg1: '#0f0f11',
    bg2: '#151518',
    bg3: '#1c1c21',
    bg4: '#242429',
    border: 'rgba(255,255,255,0.07)',
    borderHov: 'rgba(255,255,255,0.13)',
    gold: '#f5a623',
    goldDim: 'rgba(245,166,35,0.1)',
    goldGlow: 'rgba(245,166,35,0.18)',
    text0: '#ececec',
    text1: '#909090',
    text2: '#444444',
    green: '#22c55e',
    red: '#ef4444',
    blue: '#60a5fa',
};

// ── Connector definitions ──────────────────────────────────────
const CONNECTORS = [
    {
        id: 'github',
        name: 'GitHub',
        description: 'Manage repos, issues, PRs & code',
        category: 'Development',
        color: '#e8e8e8',
        bg: '#161b22',
        fields: [
            { key: 'GITHUB_PERSONAL_ACCESS_TOKEN', label: 'Personal Access Token', placeholder: 'ghp_xxxxxxxxxxxxxxxxxxxx', help: 'github.com/settings/tokens' },
        ],
        logo: (
            <svg viewBox="0 0 24 24" width="22" height="22" fill="currentColor">
                <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0 0 24 12c0-6.63-5.37-12-12-12z"/>
            </svg>
        ),
        mcpServer: 'npx -y @modelcontextprotocol/server-github',
        capabilities: ['Read repos', 'Create issues', 'Merge PRs', 'Search code'],
    },
    {
        id: 'gmail',
        name: 'Gmail',
        description: 'Read, compose & send emails',
        category: 'Productivity',
        color: '#ea4335',
        bg: '#1f1208',
        fields: [
            { key: 'GMAIL_CLIENT_ID', label: 'OAuth Client ID', placeholder: 'xxxxxxxx.apps.googleusercontent.com' },
            { key: 'GMAIL_CLIENT_SECRET', label: 'Client Secret', placeholder: 'GOCSPX-xxxxxxxxxxxx', secret: true },
            { key: 'GMAIL_REFRESH_TOKEN', label: 'Refresh Token', placeholder: 'Obtained via OAuth flow', secret: true },
        ],
        logo: (
            <svg viewBox="0 0 24 24" width="22" height="22" fill="none">
                <path d="M24 5.457v13.909c0 .904-.732 1.636-1.636 1.636h-3.819V11.73L12 16.64l-6.545-4.91v9.273H1.636A1.636 1.636 0 0 1 0 19.366V5.457c0-2.023 2.309-3.178 3.927-1.964L5.455 4.64 12 9.548l6.545-4.907 1.528-1.147C21.69 2.28 24 3.434 24 5.457z" fill="#ea4335"/>
            </svg>
        ),
        mcpServer: 'npx @gongrzhe/server-gmail-autoauth-mcp',
        capabilities: ['Read emails', 'Send emails', 'Search inbox', 'Manage labels'],
    },
    {
        id: 'google-calendar',
        name: 'Google Calendar',
        description: 'Schedule & manage events',
        category: 'Productivity',
        color: '#4285f4',
        bg: '#0a1628',
        fields: [
            { key: 'GCAL_CLIENT_ID', label: 'OAuth Client ID', placeholder: 'xxxxxxxx.apps.googleusercontent.com' },
            { key: 'GCAL_CLIENT_SECRET', label: 'Client Secret', placeholder: 'GOCSPX-xxxxxxxxxxxx', secret: true },
            { key: 'GCAL_REFRESH_TOKEN', label: 'Refresh Token', placeholder: 'Obtained via OAuth flow', secret: true },
        ],
        logo: (
            <svg viewBox="0 0 24 24" width="22" height="22" fill="none">
                <rect x="1" y="3" width="22" height="20" rx="2" fill="#4285f4"/>
                <rect x="1" y="8" width="22" height="2" fill="#e8f0fe"/>
                <rect x="1" y="3" width="22" height="5" fill="#1a73e8"/>
                <text x="12" y="19" textAnchor="middle" fill="white" fontSize="8" fontWeight="bold">31</text>
            </svg>
        ),
        mcpServer: 'npx @gongrzhe/server-calendar-autoauth-mcp',
        capabilities: ['Create events', 'View schedule', 'Set reminders', 'Check availability'],
    },
    {
        id: 'perplexity',
        name: 'Perplexity',
        description: 'Real-time web search & research',
        category: 'Research',
        color: '#20b2aa',
        bg: '#061414',
        fields: [
            { key: 'PERPLEXITY_API_KEY', label: 'API Key', placeholder: 'pplx-xxxxxxxxxxxxxxxxxxxx', secret: true, help: 'perplexity.ai/settings/api' },
        ],
        logo: (
            <svg viewBox="0 0 24 24" width="22" height="22" fill="currentColor" style={{color:'#20b2aa'}}>
                <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
            </svg>
        ),
        mcpServer: 'npx -y @chatmcp/server-perplexity-ask',
        capabilities: ['Web search', 'Current events', 'Research papers', 'Fact checking'],
    },
    {
        id: 'google-drive',
        name: 'Google Drive',
        description: 'Upload, read & manage Drive files',
        category: 'Productivity',
        color: '#34a853',
        bg: '#061409',
        fields: [
            { key: 'GDRIVE_CLIENT_ID', label: 'OAuth Client ID', placeholder: 'xxxxxxxx.apps.googleusercontent.com' },
            { key: 'GDRIVE_CLIENT_SECRET', label: 'Client Secret', placeholder: 'GOCSPX-xxxxxxxxxxxx', secret: true },
            { key: 'GDRIVE_REFRESH_TOKEN', label: 'Refresh Token', placeholder: 'Obtained via OAuth flow', secret: true },
        ],
        logo: (
            <svg viewBox="0 0 87.3 78" width="22" height="22" fill="none">
                <path d="M6.6 66.85l3.85 6.65c.8 1.4 1.95 2.5 3.3 3.3L27.5 53H0c0 1.55.4 3.1 1.2 4.5z" fill="#0066da"/>
                <path d="M43.65 25L29.9 1.2c-1.35.8-2.5 1.9-3.3 3.3L1.2 48.5c-.8 1.4-1.2 2.95-1.2 4.5h27.5z" fill="#00ac47"/>
                <path d="M73.55 76.8c1.35-.8 2.5-1.9 3.3-3.3l1.6-2.75L86.1 57c.8-1.4 1.2-2.95 1.2-4.5H59.8L73.55 76.8z" fill="#ea4335"/>
                <path d="M43.65 25L57.4 1.2C56.05.4 54.5 0 52.95 0H34.35c-1.55 0-3.1.4-4.45 1.2z" fill="#00832d"/>
                <path d="M59.8 53H27.5l-13.75 23.8c1.35.8 2.9 1.2 4.45 1.2h50.9c1.55 0 3.1-.4 4.45-1.2z" fill="#2684fc"/>
                <path d="M73.4 26.5L59.65 3.5c-.8-1.4-1.95-2.5-3.3-3.3L43.6 25l16.2 28h27.45c0-1.55-.4-3.1-1.2-4.5z" fill="#ffba00"/>
            </svg>
        ),
        mcpServer: 'npx -y @modelcontextprotocol/server-gdrive',
        capabilities: ['Read files', 'Upload files', 'Search Drive', 'Manage folders'],
    },
    {
        id: 'slack',
        name: 'Slack',
        description: 'Send messages & manage channels',
        category: 'Communication',
        color: '#4a154b',
        bg: '#0f0510',
        fields: [
            { key: 'SLACK_BOT_TOKEN', label: 'Bot Token', placeholder: 'xoxb-xxxxxxxxxxxx', secret: true, help: 'api.slack.com/apps' },
            { key: 'SLACK_TEAM_ID', label: 'Team / Workspace ID', placeholder: 'T0XXXXXXX' },
        ],
        logo: (
            <svg viewBox="0 0 24 24" width="22" height="22" fill="none">
                <path d="M5.042 15.165a2.528 2.528 0 0 1-2.52 2.523A2.528 2.528 0 0 1 0 15.165a2.527 2.527 0 0 1 2.522-2.52h2.52v2.52zm1.271 0a2.527 2.527 0 0 1 2.521-2.52 2.527 2.527 0 0 1 2.521 2.52v6.313A2.528 2.528 0 0 1 8.834 24a2.528 2.528 0 0 1-2.521-2.522v-6.313zM8.834 5.042a2.528 2.528 0 0 1-2.521-2.52A2.528 2.528 0 0 1 8.834 0a2.528 2.528 0 0 1 2.521 2.522v2.52H8.834zm0 1.271a2.528 2.528 0 0 1 2.521 2.521 2.528 2.528 0 0 1-2.521 2.521H2.522A2.528 2.528 0 0 1 0 8.834a2.528 2.528 0 0 1 2.522-2.521h6.312zm10.122 2.521a2.528 2.528 0 0 1 2.522-2.521A2.528 2.528 0 0 1 24 8.834a2.528 2.528 0 0 1-2.522 2.521h-2.522V8.834zm-1.268 0a2.528 2.528 0 0 1-2.523 2.521 2.527 2.527 0 0 1-2.52-2.521V2.522A2.527 2.527 0 0 1 15.165 0a2.528 2.528 0 0 1 2.523 2.522v6.312zm-2.523 10.122a2.528 2.528 0 0 1 2.523 2.522A2.528 2.528 0 0 1 15.165 24a2.527 2.527 0 0 1-2.52-2.522v-2.522h2.52zm0-1.268a2.527 2.527 0 0 1-2.52-2.523 2.526 2.526 0 0 1 2.52-2.52h6.313A2.527 2.527 0 0 1 24 15.165a2.528 2.528 0 0 1-2.522 2.523h-6.313z" fill="#E01E5A"/>
            </svg>
        ),
        mcpServer: 'npx -y @modelcontextprotocol/server-slack',
        capabilities: ['Send messages', 'Read channels', 'Search messages', 'List users'],
    },
    {
        id: 'notion',
        name: 'Notion',
        description: 'Read & write Notion pages/databases',
        category: 'Productivity',
        color: '#ffffff',
        bg: '#111110',
        fields: [
            { key: 'NOTION_API_KEY', label: 'Integration Token', placeholder: 'secret_xxxxxxxxxxxxxxxxxxxx', secret: true, help: 'notion.so/my-integrations' },
        ],
        logo: (
            <svg viewBox="0 0 24 24" width="22" height="22" fill="currentColor">
                <path d="M4.459 4.208c.746.606 1.026.56 2.428.466l13.215-.793c.28 0 .047-.28-.046-.326L17.86 1.968c-.42-.326-.981-.7-2.055-.607L3.01 2.295c-.466.046-.56.28-.374.466zm.793 3.08v13.904c0 .747.373 1.027 1.214.98l14.523-.84c.841-.046.935-.56.935-1.167V6.354c0-.606-.233-.933-.748-.887l-15.177.887c-.56.047-.747.327-.747.933zm14.337.745c.093.42 0 .84-.42.888l-.7.14v10.264c-.608.327-1.168.514-1.635.514-.748 0-.935-.234-1.495-.933l-4.577-7.186v6.952L12.21 19s0 .84-1.168.84l-3.222.186c-.093-.186 0-.653.327-.746l.84-.233V9.854L7.822 9.76c-.094-.42.14-1.026.793-1.073l3.456-.233 4.764 7.279v-6.44l-1.215-.139c-.093-.514.28-.887.747-.933zM1.936 1.035l13.31-.98c1.634-.14 2.055-.047 3.082.7l4.249 2.986c.7.513.934.653.934 1.213v16.378c0 1.026-.373 1.634-1.68 1.726l-15.458.934c-.98.047-1.448-.093-1.962-.747l-3.129-4.06c-.56-.747-.793-1.306-.793-1.96V2.667c0-.839.374-1.54 1.447-1.632z"/>
            </svg>
        ),
        mcpServer: 'npx -y @modelcontextprotocol/server-notion',
        capabilities: ['Read pages', 'Create pages', 'Query databases', 'Update content'],
    },
    {
        id: 'postgres',
        name: 'PostgreSQL',
        description: 'Query & manage database tables',
        category: 'Database',
        color: '#336791',
        bg: '#080f18',
        fields: [
            { key: 'POSTGRES_CONNECTION_STRING', label: 'Connection String', placeholder: 'postgresql://user:pass@host:5432/db', secret: true },
        ],
        logo: (
            <svg viewBox="0 0 24 24" width="22" height="22" fill="#336791">
                <path d="M23.5 11.5c-.3-1.5-1.4-2.8-2.8-3.4.5-.8.7-1.7.6-2.6-.3-2.4-2.8-3.4-4.9-3.5-1.3 0-2.6.4-3.6 1.1C12 2.1 11 1.6 10 1.6 7.1 1.5 4.8 3.4 4.5 6.3c-.1.8 0 1.5.3 2.2C3.4 9 2.1 10.2 1.7 11.8c-.5 2.1.4 4.2 2.1 5.4-.1.5-.1 1 0 1.5.4 2.1 2.3 3.7 4.5 3.7 1.3 0 2.5-.5 3.4-1.3.9.8 2.1 1.3 3.4 1.3 2.3 0 4.3-1.6 4.6-3.8.1-.5.1-1 0-1.5 1.7-1.2 2.6-3.3 1.8-5.6z"/>
            </svg>
        ),
        mcpServer: 'npx -y @modelcontextprotocol/server-postgres',
        capabilities: ['Run queries', 'Read tables', 'Insert data', 'Schema inspection'],
    },
];

const CATEGORIES = ['All', ...Array.from(new Set(CONNECTORS.map(c => c.category)))];

// ── Helpers ────────────────────────────────────────────────────
const STORAGE_KEY = 'agent_connector_configs';
const loadConfigs = () => { try { return JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}'); } catch { return {}; } };
const saveConfigs = (c) => localStorage.setItem(STORAGE_KEY, JSON.stringify(c));

// ── Individual connector card ──────────────────────────────────
const ConnectorCard = ({ connector, isConnected, onClick }) => (
    <button
        onClick={() => onClick(connector)}
        style={{
            display: 'flex', alignItems: 'center', gap: '14px',
            padding: '14px 16px', background: C.bg3,
            border: `1px solid ${isConnected ? 'rgba(34,197,94,0.3)' : C.border}`,
            borderRadius: '12px', cursor: 'pointer', width: '100%', textAlign: 'left',
            transition: 'all 0.18s', position: 'relative', overflow: 'hidden',
        }}
        onMouseEnter={e => { e.currentTarget.style.background = C.bg4; e.currentTarget.style.borderColor = isConnected ? 'rgba(34,197,94,0.5)' : C.borderHov; }}
        onMouseLeave={e => { e.currentTarget.style.background = C.bg3; e.currentTarget.style.borderColor = isConnected ? 'rgba(34,197,94,0.3)' : C.border; }}
    >
        {/* color accent strip */}
        <div style={{ position: 'absolute', left: 0, top: 0, bottom: 0, width: '3px', background: isConnected ? C.green : connector.color, borderRadius: '12px 0 0 12px', opacity: 0.7 }}/>

        {/* logo */}
        <div style={{
            width: '42px', height: '42px', borderRadius: '10px',
            background: connector.bg, border: `1px solid ${C.border}`,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            flexShrink: 0, color: connector.color, marginLeft: '6px',
        }}>
            {connector.logo}
        </div>

        {/* info */}
        <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '2px' }}>
                <span style={{ fontSize: '0.875rem', fontWeight: 600, color: C.text0 }}>{connector.name}</span>
                {isConnected && (
                    <span style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.6rem', fontWeight: 700, color: C.green, background: 'rgba(34,197,94,0.1)', border: '1px solid rgba(34,197,94,0.2)', borderRadius: '20px', padding: '1px 6px', letterSpacing: '0.5px', textTransform: 'uppercase' }}>
                        <span style={{ width: '5px', height: '5px', background: C.green, borderRadius: '50%', animation: 'conn-pulse 2s ease infinite' }}/>
                        Active
                    </span>
                )}
            </div>
            <div style={{ fontSize: '0.72rem', color: C.text1 }}>{connector.description}</div>
        </div>

        <ChevronRight size={14} style={{ color: C.text2, flexShrink: 0 }}/>
    </button>
);

// ── Config detail panel ────────────────────────────────────────
const ConnectorDetail = ({ connector, onBack, onSave, savedConfig }) => {
    const [values, setValues] = useState(() => {
        const init = {};
        connector.fields.forEach(f => { init[f.key] = savedConfig?.[f.key] || ''; });
        return init;
    });
    const [show, setShow] = useState({});
    const [saved, setSaved] = useState(false);
    const [testResult, setTestResult] = useState(null);
    const [isTesting, setIsTesting] = useState(false);

    const allFilled = connector.fields.every(f => values[f.key]?.trim());

    const handleSave = () => {
        onSave(connector.id, values);
        setSaved(true);
        setTimeout(() => setSaved(false), 2000);
    };

    const handleTest = async () => {
        setIsTesting(true);
        setTestResult({ stdout: [], stderr: [] });
        let output = { stdout: [], stderr: [] };
        try {
            // The command for a test is just the server command itself.
            // Most MCP servers will print a help/status message and exit if no input is piped.
            const reader = await testConnector(connector.mcpServer, values);
            const decoder = new TextDecoder();

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value, { stream: true });
                const lines = chunk.split('\n\n').filter(Boolean);

                for (const line of lines) {
                    if (line.startsWith('event: ')) {
                        const event = line.split('\n')[0].substring(7).trim();
                        const dataLine = line.split('\n')[1]?.substring(6).trim();
                        if (dataLine) {
                            try {
                                const data = JSON.parse(dataLine);
                                if (event === 'stdout' && data.line) output.stdout.push(data.line);
                                else if (event === 'stderr' && data.line) output.stderr.push(data.line);
                            } catch {}
                        }
                    }
                }
            }
            setTestResult(output);
        } catch (error) {
            setTestResult({ ...output, stderr: [...output.stderr, error.message] });
        } finally {
            setIsTesting(false);
        }
    };

    return (
        <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
            {/* Back header */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '24px' }}>
                <button onClick={onBack} style={{ display: 'flex', alignItems: 'center', gap: '6px', background: C.bg3, border: `1px solid ${C.border}`, borderRadius: '8px', padding: '6px 12px', color: C.text1, cursor: 'pointer', fontSize: '0.75rem', fontFamily: "'Outfit',sans-serif" }}>
                    ← Back
                </button>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flex: 1 }}>
                    <div style={{ width: '36px', height: '36px', borderRadius: '9px', background: connector.bg, border: `1px solid ${C.border}`, display: 'flex', alignItems: 'center', justifyContent: 'center', color: connector.color }}>
                        {connector.logo}
                    </div>
                    <div>
                        <div style={{ fontSize: '0.9rem', fontWeight: 700, color: C.text0 }}>{connector.name}</div>
                        <div style={{ fontSize: '0.65rem', color: C.text1 }}>{connector.category}</div>
                    </div>
                </div>
            </div>

            {/* Capabilities */}
            <div style={{ marginBottom: '20px' }}>
                <div style={{ fontSize: '0.62rem', fontWeight: 700, letterSpacing: '1px', textTransform: 'uppercase', color: C.text2, marginBottom: '8px' }}>Capabilities</div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                    {connector.capabilities.map(cap => (
                        <span key={cap} style={{ fontSize: '0.67rem', padding: '3px 8px', background: C.goldDim, border: '1px solid rgba(245,166,35,0.2)', borderRadius: '20px', color: '#fbbf24' }}>{cap}</span>
                    ))}
                </div>
            </div>

            {/* MCP Server */}
            <div style={{ padding: '10px 12px', background: C.bg2, borderRadius: '8px', marginBottom: '20px', border: `1px solid ${C.border}` }}>
                <div style={{ fontSize: '0.6rem', color: C.text2, marginBottom: '4px', textTransform: 'uppercase', letterSpacing: '0.8px' }}>MCP Server</div>
                <code style={{ fontSize: '0.7rem', color: '#60a5fa', fontFamily: "'Geist Mono',monospace" }}>{connector.mcpServer}</code>
            </div>

            {/* Fields */}
            <div style={{ fontSize: '0.62rem', fontWeight: 700, letterSpacing: '1px', textTransform: 'uppercase', color: C.text2, marginBottom: '12px' }}>Configuration</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', flex: 1, overflowY: 'auto' }}>
                {connector.fields.map(field => (
                    <div key={field.key}>
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
                            <label style={{ fontSize: '0.75rem', fontWeight: 600, color: C.text0, fontFamily: "'Outfit',sans-serif" }}>{field.label}</label>
                            {field.help && (
                                <a href={`https://${field.help}`} target="_blank" rel="noopener noreferrer" style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.62rem', color: C.blue, textDecoration: 'none' }}>
                                    Get key <ExternalLink size={10}/>
                                </a>
                            )}
                        </div>
                        <div style={{ position: 'relative' }}>
                            <input
                                type={field.secret && !show[field.key] ? 'password' : 'text'}
                                value={values[field.key] || ''}
                                onChange={e => setValues(v => ({ ...v, [field.key]: e.target.value }))}
                                placeholder={field.placeholder}
                                style={{
                                    width: '100%', padding: '10px 36px 10px 12px',
                                    background: C.bg2, border: `1px solid ${C.border}`,
                                    borderRadius: '8px', color: C.text0,
                                    fontSize: '0.78rem', fontFamily: "'Geist Mono',monospace",
                                    outline: 'none', boxSizing: 'border-box',
                                    transition: 'border-color 0.15s',
                                }}
                                onFocus={e => e.target.style.borderColor = 'rgba(245,166,35,0.4)'}
                                onBlur={e => e.target.style.borderColor = C.border}
                            />
                            {field.secret && (
                                <button onClick={() => setShow(s => ({ ...s, [field.key]: !s[field.key] }))}
                                    style={{ position: 'absolute', right: '10px', top: '50%', transform: 'translateY(-50%)', background: 'none', border: 'none', color: C.text2, cursor: 'pointer', display: 'flex', padding: 0 }}>
                                    {show[field.key] ? <EyeOff size={14}/> : <Eye size={14}/>}
                                </button>
                            )}
                        </div>
                    </div>
                ))}
            </div>

            {/* Action Buttons */}
            <div style={{ display: 'flex', gap: '10px', marginTop: '20px' }}>
                <button
                    onClick={handleTest}
                    disabled={!allFilled || isTesting}
                    style={{
                        flex: 1, padding: '12px', background: C.bg3,
                        border: `1px solid ${C.border}`, borderRadius: '10px',
                        color: allFilled ? C.text0 : C.text2, fontSize: '0.82rem', fontWeight: 700,
                        cursor: allFilled && !isTesting ? 'pointer' : 'not-allowed',
                        fontFamily: "'Outfit',sans-serif", display: 'flex', alignItems: 'center',
                        justifyContent: 'center', gap: '8px', transition: 'all 0.2s',
                    }}
                >
                    {isTesting ? 'Testing...' : 'Test Connection'}
                </button>
                <button
                    onClick={handleSave}
                    disabled={!allFilled}
                    style={{
                        flex: 2, padding: '12px',
                        background: saved ? 'rgba(34,197,94,0.15)' : allFilled ? C.gold : C.bg3,
                        border: `1px solid ${saved ? 'rgba(34,197,94,0.4)' : allFilled ? 'transparent' : C.border}`,
                        borderRadius: '10px', color: saved ? C.green : allFilled ? '#0f0f0f' : C.text2,
                        fontSize: '0.82rem', fontWeight: 700, cursor: allFilled ? 'pointer' : 'not-allowed',
                        fontFamily: "'Outfit',sans-serif", display: 'flex', alignItems: 'center',
                        justifyContent: 'center', gap: '8px', transition: 'all 0.2s',
                        boxShadow: allFilled && !saved ? '0 2px 16px rgba(245,166,35,0.25)' : 'none',
                    }}
                >
                    {saved ? <><Check size={15}/> Saved!</> : <><Key size={14}/> Save Configuration</>}
                </button>
            </div>
            {!allFilled && <p style={{ textAlign: 'center', fontSize: '0.65rem', color: C.text2, margin: '6px 0 0' }}>Fill all fields to activate this connector</p>}

            {/* Test Result Display */}
            {testResult && (
                <div style={{ marginTop: '16px', background: C.bg2, borderRadius: '8px', padding: '12px', border: `1px solid ${C.border}` }}>
                    <div style={{ fontSize: '0.62rem', fontWeight: 700, letterSpacing: '1px', textTransform: 'uppercase', color: C.text2, marginBottom: '8px' }}>Test Result</div>
                    <pre style={{ margin: 0, whiteSpace: 'pre-wrap', wordWrap: 'break-word', fontSize: '0.7rem', color: C.text1, fontFamily: "'Geist Mono',monospace", maxHeight: '150px', overflowY: 'auto' }}>
                        {testResult.stderr?.length > 0 && <code style={{color: C.red}}>{testResult.stderr.join('\n')}</code>}
                        {testResult.stdout?.length > 0 && <code>{testResult.stdout.join('\n')}</code>}
                        {testResult.stdout?.length === 0 && testResult.stderr?.length === 0 && <code>Connection test sent. No output received, which may be normal. Check for errors above.</code>}
                    </pre>
                </div>
            )}
        </div>
    );
};

// ═══════════════════════════════════════════════════════════════
// MAIN MODAL
// ═══════════════════════════════════════════════════════════════
const ConnectorModal = ({ isOpen, onClose, onConnectorsChange }) => {
    const [configs, setConfigs] = useState(loadConfigs);
    const [selected, setSelected] = useState(null);
    const [category, setCategory] = useState('All');
    const [search, setSearch] = useState('');

    useEffect(() => { if (!isOpen) { setSelected(null); setSearch(''); } }, [isOpen]);

    const handleSave = useCallback((connectorId, values) => {
        const next = { ...configs, [connectorId]: values };
        setConfigs(next);
        saveConfigs(next);
        if (onConnectorsChange) onConnectorsChange(next);
    }, [configs, onConnectorsChange]);

    const handleDelete = useCallback((connectorId) => {
        const next = { ...configs };
        delete next[connectorId];
        setConfigs(next);
        saveConfigs(next);
        if (onConnectorsChange) onConnectorsChange(next);
    }, [configs, onConnectorsChange]);

    const isConnected = (id) => {
        const cfg = configs[id];
        if (!cfg) return false;
        const conn = CONNECTORS.find(c => c.id === id);
        return conn?.fields.every(f => cfg[f.key]?.trim());
    };

    const filtered = CONNECTORS.filter(c =>
        (category === 'All' || c.category === category) &&
        (c.name.toLowerCase().includes(search.toLowerCase()) || c.description.toLowerCase().includes(search.toLowerCase()))
    );

    const connectedCount = CONNECTORS.filter(c => isConnected(c.id)).length;

    if (!isOpen) return null;

    return (
        <div
            onClick={onClose}
            style={{
                position: 'fixed', inset: 0, zIndex: 1000,
                background: 'rgba(0,0,0,0.75)',
                backdropFilter: 'blur(8px)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                animation: 'conn-fade 0.2s ease',
            }}
        >
            <style>{`
                @keyframes conn-fade { from{opacity:0} to{opacity:1} }
                @keyframes conn-slide { from{opacity:0;transform:scale(0.96) translateY(8px)} to{opacity:1;transform:scale(1) translateY(0)} }
                @keyframes conn-pulse { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:0.4;transform:scale(0.6)} }
            `}</style>
            <div
                onClick={e => e.stopPropagation()}
                style={{
                    width: '560px', maxWidth: '95vw',
                    maxHeight: '85vh',
                    background: C.bg1,
                    border: `1px solid ${C.borderHov}`,
                    borderRadius: '20px',
                    display: 'flex', flexDirection: 'column',
                    overflow: 'hidden',
                    animation: 'conn-slide 0.22s ease',
                    boxShadow: '0 32px 80px rgba(0,0,0,0.8)',
                }}
            >
                {selected ? (
                    /* ── Detail view ── */
                    <div style={{ padding: '24px', flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0' }}>
                            <div/>
                            <div style={{ display: 'flex', gap: '8px' }}>
                                {isConnected(selected.id) && (
                                    <button onClick={() => { handleDelete(selected.id); setSelected(null); }}
                                        style={{ display: 'flex', alignItems: 'center', gap: '4px', padding: '5px 10px', background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.2)', borderRadius: '7px', color: C.red, cursor: 'pointer', fontSize: '0.7rem', fontFamily: "'Outfit',sans-serif" }}>
                                        <Trash2 size={12}/> Disconnect
                                    </button>
                                )}
                                <button onClick={onClose} style={{ background: C.bg3, border: `1px solid ${C.border}`, borderRadius: '8px', padding: '6px', color: C.text1, cursor: 'pointer', display: 'flex' }}>
                                    <X size={16}/>
                                </button>
                            </div>
                        </div>
                        <ConnectorDetail
                            connector={selected}
                            onBack={() => setSelected(null)}
                            onSave={handleSave}
                            savedConfig={configs[selected.id]}
                        />
                    </div>
                ) : (
                    /* ── List view ── */
                    <>
                        {/* Header */}
                        <div style={{ padding: '20px 24px 0', flexShrink: 0 }}>
                            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
                                <div>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                                        <div style={{ width: '32px', height: '32px', background: C.goldDim, border: '1px solid rgba(245,166,35,0.2)', borderRadius: '9px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                                            <Zap size={15} style={{ color: C.gold }}/>
                                        </div>
                                        <h2 style={{ margin: 0, fontSize: '1rem', fontWeight: 700, color: C.text0, fontFamily: "'Outfit',sans-serif" }}>Connectors</h2>
                                        {connectedCount > 0 && (
                                            <span style={{ fontSize: '0.6rem', fontWeight: 700, padding: '2px 7px', background: 'rgba(34,197,94,0.1)', border: '1px solid rgba(34,197,94,0.2)', borderRadius: '20px', color: C.green }}>
                                                {connectedCount} active
                                            </span>
                                        )}
                                    </div>
                                    <p style={{ margin: '4px 0 0 42px', fontSize: '0.72rem', color: C.text1 }}>Connect external tools to your agent</p>
                                </div>
                                <button onClick={onClose} style={{ background: C.bg3, border: `1px solid ${C.border}`, borderRadius: '8px', padding: '7px', color: C.text1, cursor: 'pointer', display: 'flex' }}>
                                    <X size={16}/>
                                </button>
                            </div>

                            {/* Search */}
                            <input
                                value={search}
                                onChange={e => setSearch(e.target.value)}
                                placeholder="Search connectors…"
                                style={{
                                    width: '100%', padding: '9px 14px', background: C.bg2,
                                    border: `1px solid ${C.border}`, borderRadius: '10px',
                                    color: C.text0, fontSize: '0.82rem', outline: 'none',
                                    fontFamily: "'Outfit',sans-serif", boxSizing: 'border-box',
                                    marginBottom: '12px',
                                }}
                                onFocus={e => e.target.style.borderColor = 'rgba(245,166,35,0.35)'}
                                onBlur={e => e.target.style.borderColor = C.border}
                            />

                            {/* Category tabs */}
                            <div style={{ display: 'flex', gap: '6px', overflowX: 'auto', paddingBottom: '12px' }}>
                                {CATEGORIES.map(cat => (
                                    <button key={cat} onClick={() => setCategory(cat)}
                                        style={{
                                            padding: '4px 12px', borderRadius: '20px', fontSize: '0.7rem', fontWeight: 600,
                                            border: `1px solid ${category === cat ? 'rgba(245,166,35,0.35)' : C.border}`,
                                            background: category === cat ? C.goldDim : C.bg2,
                                            color: category === cat ? '#fbbf24' : C.text1,
                                            cursor: 'pointer', whiteSpace: 'nowrap', fontFamily: "'Outfit',sans-serif",
                                            transition: 'all 0.15s',
                                        }}>
                                        {cat}
                                    </button>
                                ))}
                            </div>
                        </div>

                        {/* Connector list */}
                        <div style={{ flex: 1, overflowY: 'auto', padding: '0 24px 24px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                            {filtered.length === 0 ? (
                                <div style={{ textAlign: 'center', padding: '40px 0', color: C.text2, fontSize: '0.82rem' }}>
                                    No connectors match your search
                                </div>
                            ) : filtered.map(connector => (
                                <ConnectorCard
                                    key={connector.id}
                                    connector={connector}
                                    isConnected={isConnected(connector.id)}
                                    onClick={setSelected}
                                />
                            ))}
                        </div>

                        {/* Footer hint */}
                        {connectedCount > 0 && (
                            <div style={{ padding: '12px 24px', borderTop: `1px solid ${C.border}`, display: 'flex', alignItems: 'center', gap: '8px', flexShrink: 0 }}>
                                <AlertCircle size={13} style={{ color: C.gold, flexShrink: 0 }}/>
                                <p style={{ margin: 0, fontSize: '0.65rem', color: C.text1 }}>
                                    Active connectors are injected into the agent on every message. Restart if you add new ones.
                                </p>
                            </div>
                        )}
                    </>
                )}
            </div>
        </div>
    );
};

export { ConnectorModal, CONNECTORS, loadConfigs };
export default ConnectorModal;
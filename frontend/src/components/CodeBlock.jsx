import React, { useState } from 'react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { atomDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { Copy, Check } from 'lucide-react';

/**
 * CodeBlock
 * Reusable macOS-style code window with syntax highlighting and copy button.
 *
 * Props:
 *   code     {string}  - Source code string
 *   language {string}  - Language identifier (e.g. "python", "bash", "javascript")
 *   filename {string}  - Optional filename to show instead of language
 *   maxHeight{number}  - Max px height of scrollable code area (default 520)
 */
const CodeBlock = ({ code = '', language = 'text', filename, maxHeight = 520 }) => {
    const [copied, setCopied] = useState(false);

    const handleCopy = async () => {
        try { await navigator.clipboard.writeText(code); }
        catch {
            const el = document.createElement('textarea');
            el.value = code;
            document.body.appendChild(el);
            el.select();
            document.execCommand('copy');
            document.body.removeChild(el);
        }
        setCopied(true);
        setTimeout(() => setCopied(false), 2200);
    };

    const displayLabel = filename || language;

    return (
        <div className="code-block-outer" style={{ '--cb-max-h': `${maxHeight}px` }}>
            {/* ── Window chrome ── */}
            <div className="code-block-header">
                <div className="cb-dots">
                    <span className="cb-dot cb-dot-r" />
                    <span className="cb-dot cb-dot-y" />
                    <span className="cb-dot cb-dot-g" />
                </div>
                <span className="cb-lang">{displayLabel}</span>
                <button
                    className={`cb-copy-btn ${copied ? 'copied' : ''}`}
                    onClick={handleCopy}
                    title="Copy to clipboard"
                >
                    {copied ? <Check size={12} /> : <Copy size={12} />}
                    <span>{copied ? 'Copied!' : 'Copy'}</span>
                </button>
            </div>

            {/* ── Code body ── */}
            <div className="code-block-body">
                <SyntaxHighlighter
                    style={atomDark}
                    language={language}
                    PreTag="div"
                    showLineNumbers
                    customStyle={{
                        margin: 0,
                        padding: '16px 18px',
                        background: '#0d0d0d',
                        fontSize: '0.82rem',
                        lineHeight: '1.65',
                        maxHeight: `${maxHeight}px`,
                        overflowY: 'auto',
                        borderRadius: 0,
                    }}
                    lineNumberStyle={{
                        color: '#2e2e2e',
                        minWidth: '2.2em',
                        paddingRight: '12px',
                        userSelect: 'none',
                    }}
                >
                    {code}
                </SyntaxHighlighter>
            </div>
        </div>
    );
};

export default CodeBlock;

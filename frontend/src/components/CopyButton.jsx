import React, { useState } from 'react';
import { Copy, Check } from 'lucide-react';

/**
 * CopyButton — standalone clipboard copy with animated feedback.
 * Matches the Noir Studio design system.
 *
 * Props:
 *   textToCopy  {string}  text to write to clipboard
 *   size        {string}  'sm' | 'md' (default 'md')
 *   label       {string}  override button label (default 'Copy')
 */
const CopyButton = ({ textToCopy = '', size = 'md', label = 'Copy' }) => {
    const [copied, setCopied] = useState(false);

    const handleCopy = async () => {
        try {
            await navigator.clipboard.writeText(textToCopy);
        } catch {
            // Fallback for older browsers
            const el = document.createElement('textarea');
            el.value = textToCopy;
            el.style.position = 'fixed';
            el.style.opacity  = '0';
            document.body.appendChild(el);
            el.focus();
            el.select();
            document.execCommand('copy');
            document.body.removeChild(el);
        }
        setCopied(true);
        setTimeout(() => setCopied(false), 2400);
    };

    const isSm = size === 'sm';

    return (
        <button
            onClick={handleCopy}
            title={copied ? 'Copied!' : 'Copy to clipboard'}
            style={{
                display:      'inline-flex',
                alignItems:   'center',
                gap:          '5px',
                padding:      isSm ? '3px 8px' : '4px 10px',
                background:   copied
                    ? 'rgba(34,197,94,0.10)'
                    : 'rgba(255,255,255,0.05)',
                border:       `1px solid ${copied
                    ? 'rgba(34,197,94,0.30)'
                    : 'rgba(255,255,255,0.10)'}`,
                borderRadius: '5px',
                color:        copied ? '#4ade80' : '#a0a0a0',
                fontFamily:   "'Outfit', system-ui, sans-serif",
                fontSize:     isSm ? '0.64rem' : '0.68rem',
                fontWeight:   500,
                cursor:       'pointer',
                transition:   'all 0.2s ease',
                whiteSpace:   'nowrap',
                userSelect:   'none',
                lineHeight:   1,
            }}
            onMouseEnter={e => {
                if (!copied) {
                    e.currentTarget.style.background    = 'rgba(255,255,255,0.09)';
                    e.currentTarget.style.borderColor   = 'rgba(255,255,255,0.18)';
                    e.currentTarget.style.color         = '#ececec';
                }
            }}
            onMouseLeave={e => {
                if (!copied) {
                    e.currentTarget.style.background    = 'rgba(255,255,255,0.05)';
                    e.currentTarget.style.borderColor   = 'rgba(255,255,255,0.10)';
                    e.currentTarget.style.color         = '#a0a0a0';
                }
            }}
        >
            {copied
                ? <Check  size={isSm ? 10 : 11} />
                : <Copy   size={isSm ? 10 : 11} />
            }
            <span>{copied ? 'Copied!' : label}</span>
        </button>
    );
};

export default CopyButton;
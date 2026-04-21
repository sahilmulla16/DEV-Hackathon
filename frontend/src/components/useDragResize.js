import { useState, useCallback, useEffect, useRef } from 'react';

export function useDragResize({ direction, minSize, maxSize, defaultSize, storageKey }) {
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
        document.body.style.cursor     = direction === 'x' ? 'col-resize' : 'row-resize';
        document.body.style.userSelect = 'none';
    }, [size, direction]);

    useEffect(() => {
        const onMove = (e) => {
            if (!dragging.current) return;
            const delta = (direction === 'x' ? e.clientX : e.clientY) - startPos.current;
            const raw   = startSize.current + (direction === 'x' ? delta : -delta);
            const newSize = Math.min(maxSize, Math.max(minSize, raw));
            setSize(newSize);
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
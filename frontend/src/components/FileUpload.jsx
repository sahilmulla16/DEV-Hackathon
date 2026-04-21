import React, { useState, useRef } from 'react';
import { UploadCloud } from 'lucide-react';

const FileUpload = ({ onUploadSuccess, onUploadError, setIsUploading }) => {
    const [progress, setProgress] = useState(0);
    const [isDragging, setIsDragging] = useState(false);
    const fileInputRef = useRef(null);

    const handleFiles = async (files) => {
        if (!files || files.length === 0) return;

        setIsUploading(true);
        setProgress(1);

        const fd = new FormData();
        for (const file of files) {
            fd.append('file', file);
        }

        const xhr = new XMLHttpRequest();
        xhr.open('POST', 'http://localhost:5000/api/upload', true);

        xhr.upload.onprogress = (event) => {
            if (event.lengthComputable) {
                const percentComplete = Math.round((event.loaded / event.total) * 100);
                setProgress(percentComplete);
            }
        };

        xhr.onload = () => {
            setIsUploading(false);
            setProgress(0);
            if (xhr.status >= 200 && xhr.status < 300) {
                try {
                    const d = JSON.parse(xhr.responseText);
                    onUploadSuccess(d.status || 'Upload successful');
                } catch (e) {
                    onUploadError('Failed to parse server response.');
                }
            } else {
                try {
                    const d = JSON.parse(xhr.responseText);
                    onUploadError(d.error || `Upload failed with status ${xhr.status}`);
                } catch (e) {
                    onUploadError(`Upload failed with status ${xhr.status}`);
                }
            }
        };

        xhr.onerror = () => {
            setIsUploading(false);
            setProgress(0);
            onUploadError('Network error during upload.');
        };
        
        xhr.send(fd);
    };

    const handleClick = () => fileInputRef.current?.click();
    const handleInputChange = (e) => handleFiles(e.target.files);
    const handleDragOver = (e) => { e.preventDefault(); setIsDragging(true); };
    const handleDragLeave = (e) => { e.preventDefault(); setIsDragging(false); };
    const handleDrop = (e) => {
        e.preventDefault();
        setIsDragging(false);
        handleFiles(e.dataTransfer.files);
    };

    return (
        <div
            onClick={handleClick}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            style={{
                padding: '16px',
                border: `2px dashed ${isDragging ? '#f5a623' : 'rgba(255,255,255,0.1)'}`,
                borderRadius: '12px',
                textAlign: 'center',
                cursor: 'pointer',
                transition: 'border-color 0.2s, background-color 0.2s',
                backgroundColor: isDragging ? 'rgba(245,166,35,0.05)' : 'transparent',
                position: 'relative',
                overflow: 'hidden',
            }}
        >
            <input
                ref={fileInputRef}
                type="file"
                multiple
                onChange={handleInputChange}
                style={{ display: 'none' }}
                accept=".pdf,.doc,.docx,.txt,.csv,.xlsx,.xls,.ppt,.pptx"
            />
            {progress > 0 && <div style={{ position: 'absolute', top: 0, left: 0, height: '100%', width: `${progress}%`, background: 'rgba(245,166,35,0.2)', transition: 'width 0.3s ease', zIndex: 1 }} />}
            <div style={{ position: 'relative', zIndex: 2, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px' }}>
                <UploadCloud size={20} style={{ color: '#f5a623' }} />
                <span style={{ fontSize: '0.8rem', fontWeight: 600, color: '#ececec' }}>{progress > 0 ? `Uploading... ${progress}%` : 'Upload Documents'}</span>
                <span style={{ fontSize: '0.7rem', color: '#a0a0a0' }}>Drag & drop or click to select files</span>
            </div>
        </div>
    );
};

export default FileUpload;
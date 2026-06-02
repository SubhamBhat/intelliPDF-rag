import { useState, useRef, useCallback } from 'react';
import { uploadDocument } from '../services/api';

export default function UploadPanel({ onUploadSuccess }) {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [toast, setToast] = useState(null);
  const fileInputRef = useRef(null);
  const dragCounter = useRef(0);

  const showToast = useCallback((type, message) => {
    setToast({ type, message });
    setTimeout(() => setToast(null), 4000);
  }, []);

  const handleFile = useCallback(async (file) => {
    if (!file) return;

    if (file.type !== 'application/pdf') {
      showToast('error', 'Only PDF files are accepted');
      return;
    }

    if (file.size > 50 * 1024 * 1024) {
      showToast('error', 'File size must be under 50 MB');
      return;
    }

    setIsUploading(true);
    setProgress(0);

    try {
      const data = await uploadDocument(file, (pct) => setProgress(pct));
      showToast('success', `"${file.name}" uploaded successfully`);
      if (onUploadSuccess) onUploadSuccess(data);
    } catch (err) {
      const msg = err.response?.data?.detail || err.message || 'Upload failed';
      showToast('error', msg);
    } finally {
      setIsUploading(false);
      setProgress(0);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  }, [onUploadSuccess, showToast]);

  const handleDragEnter = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    dragCounter.current += 1;
    if (dragCounter.current === 1) setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    dragCounter.current -= 1;
    if (dragCounter.current === 0) setIsDragging(false);
  }, []);

  const handleDragOver = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    dragCounter.current = 0;

    const files = e.dataTransfer.files;
    if (files.length > 0) handleFile(files[0]);
  }, [handleFile]);

  const handleClick = useCallback(() => {
    if (!isUploading) fileInputRef.current?.click();
  }, [isUploading]);

  const handleInputChange = useCallback((e) => {
    const file = e.target.files?.[0];
    if (file) handleFile(file);
  }, [handleFile]);

  const dzClasses = [
    'upload-dropzone',
    isDragging ? 'drag-over' : '',
    isUploading ? 'uploading' : '',
  ].filter(Boolean).join(' ');

  return (
    <div className="upload-panel">
      <div
        className={dzClasses}
        onDragEnter={handleDragEnter}
        onDragLeave={handleDragLeave}
        onDragOver={handleDragOver}
        onDrop={handleDrop}
        onClick={handleClick}
        role="button"
        tabIndex={0}
        aria-label="Upload PDF file"
      >
        <span className="upload-icon">
          {isDragging ? '📥' : '📄'}
        </span>
        <p className="upload-title">
          {isDragging ? 'Drop your PDF here' : 'Drop PDF here'}
        </p>
        <p className="upload-subtitle">
          or click to browse — max 50 MB
        </p>

        {!isUploading && (
          <span className="upload-browse">
            Browse Files
          </span>
        )}

        {isUploading && (
          <div className="upload-progress-wrap">
            <div className="upload-progress-bar">
              <div
                className="upload-progress-fill"
                style={{ width: `${progress}%` }}
              />
            </div>
            <p className="upload-progress-text">
              Uploading… {progress}%
            </p>
          </div>
        )}

        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,application/pdf"
          className="upload-hidden"
          onChange={handleInputChange}
        />
      </div>

      {toast && (
        <div className={`toast toast-${toast.type}`}>
          <span>{toast.type === 'success' ? '✓' : '✕'}</span>
          <span>{toast.message}</span>
        </div>
      )}
    </div>
  );
}

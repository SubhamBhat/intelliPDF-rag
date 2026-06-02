import { useState, useCallback } from 'react';

export default function DocumentList({ documents, activeDocId, onSelect, onDelete }) {
  const [deleteTarget, setDeleteTarget] = useState(null);

  const handleDeleteClick = useCallback((e, doc) => {
    e.stopPropagation();
    setDeleteTarget(doc);
  }, []);

  const confirmDelete = useCallback(() => {
    if (deleteTarget && onDelete) {
      onDelete(deleteTarget.id);
    }
    setDeleteTarget(null);
  }, [deleteTarget, onDelete]);

  const cancelDelete = useCallback(() => {
    setDeleteTarget(null);
  }, []);

  if (!documents || documents.length === 0) {
    return (
      <div className="doc-list">
        <div className="doc-empty">
          <span className="doc-empty-icon">📁</span>
          <p className="doc-empty-text">No documents uploaded yet</p>
          <p className="doc-empty-sub">Upload a PDF to get started</p>
        </div>
      </div>
    );
  }

  return (
    <div className="doc-list">
      {documents.map((doc) => (
        <div
          key={doc.id}
          className={`doc-card ${activeDocId === doc.id ? 'active' : ''}`}
          onClick={() => onSelect(doc.id)}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => e.key === 'Enter' && onSelect(doc.id)}
        >
          <div className="doc-card-icon">📕</div>
          <div className="doc-card-info">
            <p className="doc-card-name" title={doc.filename}>
              {doc.filename}
            </p>
            <div className="doc-card-meta">
              {doc.page_count != null && (
                <span>{doc.page_count} pages</span>
              )}
              {doc.chunk_count != null && (
                <span>{doc.chunk_count} chunks</span>
              )}
              {doc.page_count == null && doc.chunk_count == null && (
                <span>PDF document</span>
              )}
            </div>
          </div>
          <button
            className="doc-card-delete"
            onClick={(e) => handleDeleteClick(e, doc)}
            title="Delete document"
            aria-label={`Delete ${doc.filename}`}
          >
            🗑️
          </button>
        </div>
      ))}

      {deleteTarget && (
        <div className="confirm-overlay" onClick={cancelDelete}>
          <div
            className="confirm-dialog"
            onClick={(e) => e.stopPropagation()}
          >
            <h3 className="confirm-title">Delete Document</h3>
            <p className="confirm-text">
              Are you sure you want to delete <strong>"{deleteTarget.filename}"</strong>?
              This action cannot be undone.
            </p>
            <div className="confirm-actions">
              <button className="btn btn-ghost" onClick={cancelDelete}>
                Cancel
              </button>
              <button className="btn btn-danger" onClick={confirmDelete}>
                🗑️ Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

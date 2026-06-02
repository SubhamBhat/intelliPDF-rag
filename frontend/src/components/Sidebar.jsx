import UploadPanel from './UploadPanel';
import DocumentList from './DocumentList';

export default function Sidebar({
  documents,
  activeDocId,
  onSelectDoc,
  onDeleteDoc,
  onUploadSuccess,
}) {
  return (
    <aside className="sidebar">
      {/* ── Header ── */}
      <div className="sidebar-header">
        <div className="sidebar-logo">📑</div>
        <div>
          <div className="sidebar-title">IntelliPDF</div>
          <div className="sidebar-subtitle">RAG Platform</div>
        </div>
      </div>

      {/* ── Upload ── */}
      <UploadPanel onUploadSuccess={onUploadSuccess} />

      <div className="sidebar-divider" />

      {/* ── Documents ── */}
      <div className="sidebar-section-title">
        Your Documents {documents.length > 0 && `(${documents.length})`}
      </div>

      <div className="sidebar-content">
        <DocumentList
          documents={documents}
          activeDocId={activeDocId}
          onSelect={onSelectDoc}
          onDelete={onDeleteDoc}
        />
      </div>

      {/* ── Footer ── */}
      <div className="sidebar-footer">
        <div className="tech-badges">
          <span className="tech-badge">⚛ React</span>
          <span className="tech-badge">⚡ Vite</span>
          <span className="tech-badge">🐍 FastAPI</span>
          <span className="tech-badge">🧠 LangChain</span>
          <span className="tech-badge">📊 ChromaDB</span>
        </div>
      </div>
    </aside>
  );
}

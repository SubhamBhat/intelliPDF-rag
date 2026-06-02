import { useState, useCallback } from 'react';

export default function SourceChunks({ sources }) {
  const [isExpanded, setIsExpanded] = useState(false);

  const toggle = useCallback(() => {
    setIsExpanded((prev) => !prev);
  }, []);

  if (!sources || sources.length === 0) return null;

  return (
    <div className="sources-panel">
      <button className="sources-toggle" onClick={toggle}>
        <span>📎</span>
        <span>{sources.length} source{sources.length !== 1 ? 's' : ''}</span>
        <span className={`sources-chevron ${isExpanded ? 'open' : ''}`}>
          ▾
        </span>
      </button>

      <div className={`sources-content ${isExpanded ? 'expanded' : ''}`}>
        <div className="sources-list">
          {sources.map((src, idx) => {
            const score = src.relevance_score != null
              ? Math.round(src.relevance_score * 100)
              : null;

            return (
              <div key={idx} className="source-chunk">
                <div className="source-chunk-header">
                  <span className="source-page-badge">
                    Page {src.page_number ?? '?'}
                  </span>
                  {score != null && (
                    <div className="source-score">
                      <span>{score}%</span>
                      <div className="source-score-bar">
                        <div
                          className="source-score-fill"
                          style={{ width: `${score}%` }}
                        />
                      </div>
                    </div>
                  )}
                </div>
                <p className="source-text">{src.text}</p>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

import { useState, useRef, useEffect, useCallback } from 'react';
import ReactMarkdown from 'react-markdown';
import SourceChunks from './SourceChunks';

const SUGGESTIONS = [
  'Summarize this document',
  'What are the key findings?',
  'List the main topics covered',
  'What conclusions are drawn?',
];

export default function ChatInterface({
  messages,
  onSendMessage,
  isLoading,
  activeDocId,
  activeDocName,
}) {
  const [input, setInput] = useState('');
  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);

  const isDisabled = !activeDocId;
  const canSend = input.trim().length > 0 && !isLoading && !isDisabled;

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  // Auto-resize textarea
  useEffect(() => {
    const ta = textareaRef.current;
    if (ta) {
      ta.style.height = 'auto';
      ta.style.height = Math.min(ta.scrollHeight, 140) + 'px';
    }
  }, [input]);

  const handleSend = useCallback(() => {
    const text = input.trim();
    if (!text || isLoading || isDisabled) return;
    onSendMessage(text);
    setInput('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  }, [input, isLoading, isDisabled, onSendMessage]);

  const handleKeyDown = useCallback((e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }, [handleSend]);

  const handleSuggestionClick = useCallback((text) => {
    if (!isDisabled && !isLoading) {
      onSendMessage(text);
    }
  }, [isDisabled, isLoading, onSendMessage]);

  return (
    <div className="chat-container">
      {/* ── Header ── */}
      <div className="chat-header">
        <h2 className="chat-header-title">
          {activeDocId ? `Chat — ${activeDocName || 'Document'}` : 'IntelliPDF Chat'}
        </h2>
        {activeDocId && (
          <span className="chat-header-badge">🟢 Connected</span>
        )}
      </div>

      {/* ── Messages / Empty ── */}
      {messages.length === 0 && !isLoading ? (
        <div className="chat-empty">
          <span className="chat-empty-icon">💬</span>
          <h3 className="chat-empty-title">
            {isDisabled ? 'Select a document' : 'Start a conversation'}
          </h3>
          <p className="chat-empty-text">
            {isDisabled
              ? 'Upload and select a PDF from the sidebar to start chatting with your document.'
              : 'Ask any question about your document. The AI will find relevant passages and answer.'}
          </p>
          {!isDisabled && (
            <div className="chat-suggestions">
              {SUGGESTIONS.map((s) => (
                <button
                  key={s}
                  className="chat-suggestion"
                  onClick={() => handleSuggestionClick(s)}
                >
                  {s}
                </button>
              ))}
            </div>
          )}
        </div>
      ) : (
        <div className="chat-messages">
          {messages.map((msg, idx) => (
            <div key={idx} className={`message-row ${msg.role}`}>
              <div className="message-avatar">
                {msg.role === 'user' ? '👤' : '🤖'}
              </div>
              <div>
                <div className="message-label">
                  {msg.role === 'user' ? 'You' : 'IntelliPDF'}
                </div>
                <div className="message-bubble">
                  {msg.role === 'assistant' ? (
                    <ReactMarkdown>{msg.content}</ReactMarkdown>
                  ) : (
                    msg.content
                  )}
                </div>
                {msg.role === 'assistant' && msg.sources && (
                  <SourceChunks sources={msg.sources} />
                )}
              </div>
            </div>
          ))}

          {isLoading && (
            <div className="message-row assistant">
              <div className="message-avatar">🤖</div>
              <div className="typing-indicator">
                <div className="typing-bubble">
                  <div className="typing-dot" />
                  <div className="typing-dot" />
                  <div className="typing-dot" />
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      )}

      {/* ── Input Area ── */}
      <div className="chat-input-area">
        <div className={`chat-input-wrap ${isDisabled ? 'disabled' : ''}`}>
          <textarea
            ref={textareaRef}
            className="chat-textarea"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={
              isDisabled
                ? 'Select a document to start chatting…'
                : 'Ask a question about your document…'
            }
            disabled={isDisabled}
            rows={1}
          />
          <button
            className="chat-send-btn"
            onClick={handleSend}
            disabled={!canSend}
            title="Send message"
            aria-label="Send message"
          >
            ➤
          </button>
        </div>
        <p className="chat-input-hint">
          {isDisabled
            ? '← Upload & select a document to begin'
            : 'Press Enter to send · Shift + Enter for new line'}
        </p>
      </div>
    </div>
  );
}

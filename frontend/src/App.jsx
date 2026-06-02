import { useState, useEffect, useCallback } from 'react';
import Sidebar from './components/Sidebar';
import ChatInterface from './components/ChatInterface';
import {
  getDocuments,
  deleteDocument as apiDeleteDocument,
  sendMessage as apiSendMessage,
} from './services/api';

export default function App() {
  const [documents, setDocuments] = useState([]);
  const [activeDocId, setActiveDocId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [chatHistory, setChatHistory] = useState({}); // keyed by docId

  // ── Fetch documents on mount ──
  useEffect(() => {
    fetchDocuments();
  }, []);

  const fetchDocuments = useCallback(async () => {
    try {
      const data = await getDocuments();
      // Normalize: the API might return an array or { documents: [] }
      const docs = Array.isArray(data) ? data : data.documents ?? [];
      setDocuments(docs);
    } catch (err) {
      console.error('Failed to fetch documents:', err);
    }
  }, []);

  // ── Upload success ──
  const handleUploadSuccess = useCallback((data) => {
    fetchDocuments();
    // Auto-select the uploaded document if returned
    const newDocId = data?.doc_id || data?.id;
    if (newDocId) {
      setActiveDocId(newDocId);
      setMessages([]);
    }
  }, [fetchDocuments]);

  // ── Select document ──
  const handleSelectDoc = useCallback((docId) => {
    if (docId === activeDocId) return;

    // Save current chat
    if (activeDocId) {
      setChatHistory((prev) => ({
        ...prev,
        [activeDocId]: messages,
      }));
    }

    setActiveDocId(docId);

    // Restore or clear chat for selected doc
    setChatHistory((prev) => {
      const restored = prev[docId] || [];
      setMessages(restored);
      return prev;
    });
  }, [activeDocId, messages]);

  // ── Delete document ──
  const handleDeleteDoc = useCallback(async (docId) => {
    try {
      await apiDeleteDocument(docId);
      setDocuments((prev) => prev.filter((d) => d.id !== docId));

      if (activeDocId === docId) {
        setActiveDocId(null);
        setMessages([]);
      }

      // Clean up saved chat
      setChatHistory((prev) => {
        const updated = { ...prev };
        delete updated[docId];
        return updated;
      });
    } catch (err) {
      console.error('Failed to delete document:', err);
    }
  }, [activeDocId]);

  // ── Send message ──
  const handleSendMessage = useCallback(async (text) => {
    if (!activeDocId || !text.trim()) return;

    const userMsg = { role: 'user', content: text };
    setMessages((prev) => [...prev, userMsg]);
    setIsLoading(true);

    try {
      const data = await apiSendMessage(text, activeDocId);

      const assistantMsg = {
        role: 'assistant',
        content: data.answer || data.response || data.content || 'No response received.',
        sources: data.sources || data.source_documents || [],
      };

      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err) {
      const errorMsg = err.response?.data?.detail || err.message || 'Something went wrong.';
      const assistantMsg = {
        role: 'assistant',
        content: `⚠️ Error: ${errorMsg}`,
        sources: [],
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } finally {
      setIsLoading(false);
    }
  }, [activeDocId]);

  // Find the active doc name
  const activeDoc = documents.find((d) => d.id === activeDocId);

  return (
    <div className="app-layout">
      <Sidebar
        documents={documents}
        activeDocId={activeDocId}
        onSelectDoc={handleSelectDoc}
        onDeleteDoc={handleDeleteDoc}
        onUploadSuccess={handleUploadSuccess}
      />
      <ChatInterface
        messages={messages}
        onSendMessage={handleSendMessage}
        isLoading={isLoading}
        activeDocId={activeDocId}
        activeDocName={activeDoc?.filename}
      />
    </div>
  );
}

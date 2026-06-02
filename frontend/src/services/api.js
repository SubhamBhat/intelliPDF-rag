import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Accept': 'application/json',
  },
});

// ── Documents ──

export async function uploadDocument(file, onProgress) {
  const formData = new FormData();
  formData.append('file', file);

  const response = await api.post('/documents/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: (event) => {
      if (onProgress && event.total) {
        const pct = Math.round((event.loaded * 100) / event.total);
        onProgress(pct);
      }
    },
  });

  return response.data;
}

export async function getDocuments() {
  const response = await api.get('/documents');
  return response.data;
}

export async function deleteDocument(docId) {
  const response = await api.delete(`/documents/${docId}`);
  return response.data;
}

export async function getChunks(docId) {
  const response = await api.get(`/documents/${docId}/chunks`);
  return response.data;
}

// ── Chat ──

export async function sendMessage(question, docId) {
  const response = await api.post('/chat', {
    question,
    doc_id: docId,
  });

  return response.data;
}

export default api;

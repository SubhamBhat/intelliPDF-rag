# 📚 IntelliPDF RAG Platform

An advanced AI-powered Document Analysis and Retrieval-Augmented Generation (RAG) Platform that allows you to chat with your PDF documents using state-of-the-art language models.

---

## ✨ Key Features

- **Upload PDF Documents**: Easily upload and manage your PDF files
- **Semantic Search**: Leverage vector embeddings for intelligent search over document content
- **Retrieval-Augmented Generation (RAG)**: Get accurate answers from your PDFs with context
- **Beautiful Chat Interface**: Modern, clean, and responsive UI for seamless conversations
- **Source Chunk Citations**: View which parts of the document the AI used to generate answers
- **Fast Inference**: Powered by Groq API for lightning-fast responses
- **Multi-Document Support**: Manage and chat with multiple documents

---

## 🛠️ Tech Stack

### Backend
- **FastAPI**: Modern, high-performance web framework for building APIs
- **ChromaDB**: Open-source vector database for storing and retrieving embeddings
- **Sentence Transformers**: State-of-the-art text embedding models
- **Groq API**: High-speed inference for large language models (LLaMA, Mixtral)
- **PyPDF**: PDF document processing library

### Frontend
- **React 19**: Modern UI library for building user interfaces
- **Vite**: Lightning-fast build tool for modern web applications
- **Axios**: Promise-based HTTP client for API calls
- **React Markdown**: Beautiful markdown rendering for AI answers

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+
- npm or yarn
- Groq API Key: [Get it here](https://console.groq.com/keys)
- OpenAI API Key (optional, for embeddings): [Get it here](https://platform.openai.com/api-keys)

### Installation

#### 1. Clone the repository
```bash
git clone https://github.com/SubhamBhat/intelliPDF-rag.git
cd intelliPDF-rag
```

#### 2. Backend Setup
```bash
cd backend
pip install -r requirements.txt
```

#### 3. Environment Configuration
Create a `.env` file in the `backend` directory:
```env
# .env
GROQ_API_KEY=your_groq_api_key_here
OPENAI_API_KEY=your_openai_api_key_here  # Optional
```

#### 4. Frontend Setup
```bash
cd ../frontend
npm install
```

---

## 📖 Usage

### Running the Backend
From the project root directory:
```bash
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```
The backend API will be available at `http://localhost:8000`

### Running the Frontend
From the project root directory (new terminal):
```bash
cd frontend
npm run dev
```
The frontend will be available at `http://localhost:5173`

### Using the Application
1. Open your browser and go to `http://localhost:5173`
2. Upload your PDF document using the sidebar
3. Wait for the document to be processed (indexed in vector store)
4. Start asking questions in the chat interface!
5. View source citations by expanding the "Sources" section below each AI answer

---

## 📁 Project Structure
```
intelliPDF-rag/
├── backend/               # FastAPI backend
│   ├── models/            # Pydantic schemas
│   ├── routers/           # API routes
│   ├── services/          # Core services (LLM, embedding, PDF processing)
│   ├── config.py          # Configuration settings
│   ├── main.py            # FastAPI entry point
│   └── requirements.txt   # Backend dependencies
├── frontend/              # React frontend
│   ├── public/            # Static assets
│   ├── src/               # Source code
│   │   ├── components/    # React components
│   │   ├── services/      # API service calls
│   │   ├── App.jsx        # Main App component
│   │   ├── main.jsx       # Entry point
│   │   └── index.css      # Global styles
│   └── package.json       # Frontend dependencies
├── src/                   # Streamlit alternative UI (optional)
└── README.md              # This file
```

---

## 📝 License
MIT License - feel free to use this project for personal or commercial purposes!

---

## 🤝 Contributing
Contributions, issues, and feature requests are welcome! Feel free to check the [issues page](https://github.com/SubhamBhat/intelliPDF-rag/issues).

---

## 👨‍💻 Author
Created with ❤️ by Subham Bhat

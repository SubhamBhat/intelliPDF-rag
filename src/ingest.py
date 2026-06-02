# src/ingest.py
import os
from dotenv import load_dotenv
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma

load_dotenv()

def process_pdf(file_path: str, db_directory: str = "./vector_store") -> bool:
    """
    Parses a PDF, segments it into structured semantic chunks with metadata tracking,
    converts chunks to vectors, and persists them into ChromaDB.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Target document not found at: {file_path}")

    # 1. Document Extraction using PyMuPDFLoader
    loader = PyMuPDFLoader(file_path)
    documents = loader.load()
    
    # 2. Strategic Structural Chunking
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=750,
        chunk_overlap=150,
        length_function=len,
        separators=["\n\n", "\n", " ", ""]
    )
    chunks = text_splitter.split_documents(documents)
    
    # Inject extra safety bounds: Ensure metadata contains source and page references
    for chunk in chunks:
        chunk.metadata["source_file"] = os.path.basename(file_path)

    # 3. Vector Embeddings Generation using OpenAI
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        raise ValueError("OPENAI_API_KEY not found in environment variables!")
    
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small", openai_api_key=openai_api_key)
    
    # 4. Storage & Persistence
    vector_db = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=db_directory
    )
    
    return True

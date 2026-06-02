# src/app.py
import os
import streamlit as st
from ingest import process_pdf
from query import execute_high_accuracy_query

# Set page configuration
st.set_page_config(
    page_title="IntelliPDF RAG Platform",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main {
        background-color: #0f1117;
    }
    .stApp {
        background-color: #0f1117;
    }
    .css-1d391kg {
        padding-top: 1rem;
    }
    .sidebar .sidebar-content {
        background-color: #1a1d29;
    }
    .stButton>button {
        background-color: #6366f1;
        color: white;
        border-radius: 8px;
        border: none;
        padding: 0.5rem 1rem;
        font-weight: 500;
    }
    .stButton>button:hover {
        background-color: #4f46e5;
    }
    .stChatMessage {
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 0.75rem;
    }
    .stChatMessage.user {
        background-color: #1e293b;
    }
    .stChatMessage.assistant {
        background-color: #1a1d29;
    }
    h1 {
        background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    .stFileUploader>div>div>div>button {
        background-color: #374151;
    }
    .stSuccess {
        background-color: #065f46;
        color: white;
        border-radius: 8px;
    }
    .stError {
        background-color: #7f1d1d;
        color: white;
        border-radius: 8px;
    }
    .stInfo {
        background-color: #1e3a5f;
        color: white;
        border-radius: 8px;
    }
    .stSpinner>div>div {
        border-top-color: #6366f1;
    }
    </style>
    """, unsafe_allow_html=True)

# App header layout
col1, col2 = st.columns([3, 1])
with col1:
    st.title("📚 IntelliPDF RAG Platform")
    st.markdown("""
    <p style="color: #94a3b8; font-size: 1.1rem;">
        Advanced AI-powered document analysis using Groq and OpenAI!
    </p>
    """, unsafe_allow_html=True)
with col2:
    st.image("https://img.icons8.com/color/96/pdf.png", width=80)

st.divider()

# Workspace Initialization
os.makedirs("data", exist_ok=True)
DB_PATH = "./vector_store"

# Sidebar Control Center
with st.sidebar:
    st.markdown("""
    <div style="text-align: center; margin-bottom: 1.5rem;">
        <h2 style="color: #e2e8f0; margin-bottom: 0.5rem;">🎯 Control Center</h2>
    </div>
    """, unsafe_allow_html=True)
    
    # API Keys Section
    st.markdown("### 🔑 API Configuration")
    openai_api_key = st.text_input("OpenAI API Key", type="password", 
                                 help="Get your key from https://platform.openai.com/api-keys")
    groq_api_key = st.text_input("Groq API Key", type="password", 
                               help="Get your key from https://console.groq.com/keys")
    
    # Set environment variables
    if openai_api_key:
        os.environ["OPENAI_API_KEY"] = openai_api_key
    if groq_api_key:
        os.environ["GROQ_API_KEY"] = groq_api_key
    
    if not openai_api_key or not groq_api_key:
        st.warning("⚠️ Please enter both API keys to use the app!")
    
    st.divider()
    
    uploaded_file = st.file_uploader(
        "📤 Upload PDF Document",
        type=["pdf"],
        help="Upload a typed PDF document"
    )
    
    if uploaded_file:
        file_path = os.path.join("data", uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        st.success(f"✅ File saved: {uploaded_file.name}")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Build Index", use_container_width=True):
                if not openai_api_key or not groq_api_key:
                    st.error("⚠️ Please enter both API keys first!")
                else:
                    with st.spinner("📄 Parsing PDF, extracting text, and building knowledge base..."):
                        try:
                            process_pdf(file_path, db_directory=DB_PATH)
                            st.success("✅ Knowledge base built successfully!")
                        except Exception as e:
                            st.error(f"❌ Error: {str(e)}")
        with col2:
            if st.button("📖 Explain PDF", use_container_width=True):
                if not openai_api_key or not groq_api_key:
                    st.error("⚠️ Please enter both API keys first!")
                else:
                    with st.spinner("🤔 Analyzing document and generating summary..."):
                        try:
                            explanation_query = "Please provide a comprehensive summary and explanation of the entire document, including key topics, main points, and important details."
                            output = execute_high_accuracy_query(explanation_query, db_directory=DB_PATH)
                            st.session_state.chat_history.append({"role": "assistant", "content": f"📋 **Document Summary & Explanation:**\n\n{output['answer']}"})
                            if output["citations"]:
                                st.session_state.chat_history[-1]["content"] += f"\n\n*Sources: {', '.join(output['citations'])}*"
                            st.success("✅ Summary generated!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error: {str(e)}")
    
    st.divider()
    st.markdown("""
    <div style="color: #64748b; font-size: 0.85rem;">
        <p><strong>Features:</strong></p>
        <ul style="margin-left: 1rem;">
            <li>✅ Supports typed PDFs</li>
            <li>✅ Fast Groq API inference</li>
            <li>✅ Smart citations & sources</li>
            <li>✅ One-click document explanation</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

# Main content area
st.subheader("💬 Chat with your Document")

# Application Runtime Session Initialization
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Stream Current Messages
for chat in st.session_state.chat_history:
    role = chat["role"]
    with st.chat_message(role, avatar="👤" if role == "user" else "🤖"):
        st.markdown(chat["content"])

# Process New Queries
if query_input := st.chat_input("Ask anything about your document..."):
    if not openai_api_key or not groq_api_key:
        st.error("⚠️ Please enter both API keys in the sidebar first!")
    else:
        # Append user question
        st.session_state.chat_history.append({"role": "user", "content": query_input})
        with st.chat_message("user", avatar="👤"):
            st.markdown(query_input)
        
        # Execute Model Pipeline Response
        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("🔍 Searching knowledge base and generating answer..."):
                try:
                    output = execute_high_accuracy_query(query_input, db_directory=DB_PATH)
                    
                    # Display structural output
                    st.markdown(output["answer"])
                    if output["citations"] and "I cannot find" not in output["answer"]:
                        st.markdown(f"""
                        <div style="color: #64748b; font-size: 0.85rem; margin-top: 0.75rem; padding-top: 0.75rem; border-top: 1px solid #334155;">
                            📝 Sources: {', '.join(output['citations'])}
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # Record to Session Memory
                    full_response = output["answer"]
                    if output["citations"] and "I cannot find" not in output["answer"]:
                        full_response += f"\n\n---\n*Sources: {', '.join(output['citations'])}*"
                    st.session_state.chat_history.append({"role": "assistant", "content": full_response})
                except Exception as e:
                    error_msg = f"❌ Error: {str(e)}"
                    st.error(error_msg)
                    st.session_state.chat_history.append({"role": "assistant", "content": error_msg})

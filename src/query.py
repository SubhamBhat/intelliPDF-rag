# src/query.py
import os
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_groq import ChatGroq
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA

load_dotenv()

def execute_high_accuracy_query(user_question: str, db_directory: str = "./vector_store") -> dict:
    """
    Executes a two-stage hybrid search (Vector Retrieval),
    builds a prompt, and queries Groq LLM.
    """
    # 1. Check API keys
    openai_api_key = os.getenv("OPENAI_API_KEY")
    groq_api_key = os.getenv("GROQ_API_KEY")
    
    if not openai_api_key:
        raise ValueError("OPENAI_API_KEY not found!")
    if not groq_api_key:
        raise ValueError("GROQ_API_KEY not found!")
    
    # 2. Access Vector Index Repository
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small", openai_api_key=openai_api_key)
    vector_db = Chroma(persist_directory=db_directory, embedding_function=embeddings)
    
    # 3. Set up retriever
    retriever = vector_db.as_retriever(search_kwargs={"k": 3})
    
    # 4. Set up Groq LLM
    llm = ChatGroq(
        model="llama-3.1-8b-instant",
        temperature=0.1,
        groq_api_key=groq_api_key
    )
    
    # 5. Create prompt template
    template = """You are a precise, analytical AI designed to answer questions based strictly on the provided context.

CONTEXT:
{context}

USER QUESTION:
{question}

Instructions:
- Answer the user's question with absolute factual accuracy using only the provided context.
- If the context doesn't contain the answer, reply: "I cannot find a definitive answer within the provided document."
- Keep your answer concise, relevant, and well-structured.
- If possible, mention which page(s) the information came from.
"""
    
    prompt = PromptTemplate(
        template=template,
        input_variables=["context", "question"]
    )
    
    # 6. Create retrieval QA chain
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=True,
        chain_type_kwargs={"prompt": prompt}
    )
    
    # 7. Execute query
    result = qa_chain.invoke({"query": user_question})
    
    # 8. Process citations
    citations = []
    for doc in result["source_documents"]:
        page_num = doc.metadata.get("page", 0) + 1  # Adjust to 1-indexed
        if page_num not in citations:
            citations.append(page_num)
    
    return {
        "answer": result["result"],
        "citations": [str(p) for p in citations]
    }

"""
Handles:
- Text chunking
- Embedding generation
- Vector storage (Chroma)
- Document retrieval
- Question answering using Groq LLM
"""

import os
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from groq import Groq

from dotenv import load_dotenv
load_dotenv()

VECTOR_DIR = "vector_db"


# Embedding model
def load_embeddings():
    """
    Load sentence transformer embeddings
    """
    return HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )


# Chunking
def split_text(text):
    """
    Break document text into chunks for vector search
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=100
    )

    return splitter.split_text(text)


# Vector store
def index_document(text, filename, page, doc_type="general"):
    """
    Convert document text into vector embeddings and store them in ChromaDB
    """

    chunks = split_text(text)
    embeddings = load_embeddings()

    metadatas = [
        {
            "filename": filename,
            "page": page,
            "doc_type": doc_type
        }
        for _ in chunks
    ]

    Chroma.from_texts(
        texts=chunks,
        embedding=embeddings,
        metadatas=metadatas,
        persist_directory=VECTOR_DIR
    )


def load_vector_store():
    """
    Load persisted vector database
    """

    embeddings = load_embeddings()

    return Chroma(
        persist_directory=VECTOR_DIR,
        embedding_function=embeddings
    )


# Retrieval
def retrieve_context(question, doc_type=None, k=20):

    vectordb = load_vector_store()

    retriever = vectordb.as_retriever(
        search_type="mmr",
        search_kwargs={
            "k": k,
            "fetch_k": 30
        }
    )

    docs = retriever.invoke(question)

    context = []
    sources = []

    for doc in docs:

        meta = doc.metadata

        context.append(
            f"""
SOURCE DOCUMENT: {meta['filename']}
PAGE: {meta['page']}

{doc.page_content}
"""
        )

        sources.append(f"{meta['filename']} (page {meta['page']})")

    return "\n".join(context), list(set(sources))



# Groq LLM
def ask_llm(question, context, doc_type="document"):

    client = Groq(api_key=os.getenv("GROQ_API_KEY") or st.secrets["GROQ_API_KEY"])

    prompt = f"""
You are an AI assistant analyzing multiple {doc_type} documents.

You may receive information from several documents.

Instructions:
- Review ALL provided context.
- If multiple documents contain relevant information, summarize them.
- If documents disagree, mention the differences.
- Always mention the document names when relevant.

Context:
{context}

Question:
{question}

Answer clearly and concisely.
"""

    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    return completion.choices[0].message.content
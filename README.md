# Document AI System  
### Document Processing & RAG-Powered Q&A

An AI-powered system that processes documents (invoices, resumes, etc.), extracts structured fields, stores them for retrieval, and allows users to ask questions using a Large Language Model (LLM) with RAG (Retrieval-Augmented Generation).

The system integrates **OCR, Regex extraction, SQLite, ChromaDB, Groq LLM (Llama-3.3-70B-Versatile), and Streamlit**.

---

# Project Overview

Processing invoices manually is tedious and error-prone. This system automates:

1. Converting PDFs/images into machine-readable text (OCR).
2. Extracting structured fields via regex or configurable rules for any document type.
3. Storing data in SQLite for easy retrieval.
4. Exporting structured data to Excel for reporting.
5. Indexing documents into ChromaDB embeddings for semantic search.
6. Answering user questions with RAG + Groq LLM.
7. Providing an interactive Streamlit dashboard to view and query documents.


---

# Technology Stack

| Component | Technology |
|-----------|------------|
| Programming Language | Python |
| OCR | Tesseract via pytesseract |
| LLM | Groq API – Llama-3.3-70B-Versatile |
| LLM Orchestration | LangChain |
| Vector Database | ChromaDB |
| Data Processing | Pandas, OpenCV |
| Excel Export | XlsxWriter |
| UI | Streamlit |

---

# Core Concepts

- OCR (Optical Character Recognition): Converts images/PDFs into machine-readable text.

- Regex Extraction: Patterns for each document type allow structured field extraction.

- SQLite Database: Stores document metadata, extracted fields, and full text for RAG.

- RAG (Retrieval-Augmented Generation):

  - Full text is split into chunks.

  - Chunks are embedded into vector space using HuggingFace embeddings.

  - Queries retrieve the most relevant chunks to provide context to the LLM.


---

## Scripts & Workflow Overview

The system is designed as a modular pipeline:

---

1. db_storage.py – SQLite persistence layer
Stores documents, extracted fields, and full text for RAG.

2. extraction.py – Regex-based field extraction
Configurable JSON patterns for any document type.

3. mlops.py – Logging & monitoring
Tracks OCR and extraction quality.

4. ocr_layout.py – OCR & token processing
Converts PDFs/images into tokens and bounding boxes.

5. pipeline.py – End-to-end document processing
Workflow: OCR → Regex extraction → SQLite → Excel → RAG indexing → logging.

6. rag_engine.py – RAG embedding & retrieval engine
Handles text chunking, embeddings, and LLM question answering.

7. query_engine.py – High-level RAG interface for dashboards or APIs.

8. run_pipeline.py – Batch processor

 - Detects document types by folder (e.g., data/raw/invoices, data/raw/resumes).
 - Processes all documents and saves outputs to type-specific folders.

9. reset_db.py – Clears SQLite tables for fresh processing.

---

### Script Flow Diagram

```text
data/raw/<doc_type>/ → run_pipeline.py → pipeline.py
pipeline.py → ocr_layout.py → OCR tokens
pipeline.py → extraction.py → extracted fields
pipeline.py → db_storage.py → SQLite storage
pipeline.py → mlops.py → logging
pipeline.py → rag_engine.py → vector embeddings / RAG index
run_pipeline.py → outputs Excel in processed/<doc_type>/
query_engine.py → uses rag_engine.py → answers questions (Streamlit)
```

---

# Running the Application

### Clone the repository

```bash
git clone https://github.com/yourusername/Document-AI-System.git
cd Document-AI-System
```

### Create a virtual environment and activate it

```bash
python -m venv venv
venv\Scripts\activate      # Windows
source venv/bin/activate   # Mac/Linux
```

### Install dependencies

```bash
pip install -r requirements.txt
```

### Environment Variables

Create a .env file in the root directory:

Groq Link: [https://console.groq.com]

Hugging Face Tokens: [https://huggingface.co/settings/tokens]

```bash
GROQ_API_KEY=your_groq_api_key_here # for accessing the Groq LLM.

HF_TOKEN=your_huggingface_token_here # for downloading sentence-transformers embeddings.
```

### Prepare Documents

Place your files (PDF or images) in:

```bash
data/raw/
```
Supported formats: .pdf, .png, .jpg, .jpeg, .tiff

### Run the Pipeline

Processes all files, extracts fields, saves to SQLite and Excel, and indexes text for RAG:

```bash
python scripts/run_pipeline.py
```

- Output Excel: data/processed/
- Pickle file with all results: data/processed/all_results.pkl
- Vector store for RAG: vector_db/

### Start the Streamlit Dashboard

```bash
streamlit run dashboard.py
```

- Browse fields.
- Highlight low-confidence fields.
- Ask questions about any invoice and get AI-generated answers with sources.

### Future Improvements

- Support more document types via JSON patterns.
- Multi-page documents with attachments.
- User feedback loop to improve low-confidence extraction.
- Summarize data across multiple documents.
- Upload documents via Streamlit UI.
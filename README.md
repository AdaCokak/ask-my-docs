# Ask My Docs — RAG System on AWS Bedrock

A retrieval-augmented generation (RAG) system built on AWS Bedrock that answers 
questions about documents using semantic search and Claude.

## Architecture

- **Ingestion:** PyPDFLoader → RecursiveCharacterTextSplitter (chunk_size=1000, 
  overlap=150) → Amazon Titan Text Embeddings V2 → FAISS vector store
- **Query:** FAISS similarity search (k=6) → Claude Sonnet on Bedrock → answer

## Files

- `ingest.py` — builds the vector index from PDFs (run once)
- `ask.py` — terminal Q&A interface
- `app.py` — Gradio browser chat interface
- `evaluate.py` — evaluation suite

## Phase C Evaluation Results

Eval set: 9 questions across 5 programming language documents.

| k value | Score | Notes |
|---------|-------|-------|
| k=3 | 7/9 (78%) | baseline |
| k=6 | 8/9 (89%) | optimal |
| k=10 | 8/9 (89%) | no further improvement |

**Final setting: k=6**

### Known limitation
Cross-document comparison questions (e.g. "differences between Python and Java 
typing") reliably fail because single-vector similarity search retrieves chunks 
closest to the query semantically, which tends to pull from one document rather 
than both. Fix requires query decomposition or hybrid search — planned for 
advanced RAG phase.

## Current test corpus
5 Wikipedia articles: Go, JavaScript, Java, Python, Rust
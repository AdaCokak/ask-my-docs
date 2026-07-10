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

## Phase D — Bedrock Knowledge Base Version

The local FAISS RAG pipeline was rebuilt using Amazon Bedrock Knowledge Bases.

New AWS-managed architecture:

PDFs in S3 → Bedrock Knowledge Base → managed parser/chunking → Titan Text Embeddings V2 → managed vector store → Bedrock retrieval API → Claude answer generation

### New files

- `bedrock_kb_retrieve.py` — retrieves raw chunks from the Bedrock Knowledge Base and prints source documents.
- `bedrock_kb_answer.py` — retrieves chunks, sends them to Claude, and answers with strict grounding.
- `bedrock_kb_ask.py` — terminal chatbot version using the Bedrock Knowledge Base.
- `evaluate_bedrock_kb.py` — evaluation script for the Bedrock KB version.

### Evaluation result

The Bedrock KB version passed 9/9 questions on the current evaluation set.

| System | Score | Notes |
|---|---:|---|
| Local FAISS RAG | 8/9 | Failed on cross-document comparison |
| Bedrock Knowledge Base | 9/9 | Correctly handled multi-document comparison |

### Key learning

Bedrock Knowledge Bases replaced the local FAISS vector store with a managed AWS vector store. Bedrock now handles parsing, chunking, embedding, indexing, and retrieval.

However, retrieval alone is not enough. For out-of-scope questions, the Knowledge Base can still return irrelevant chunks. The application layer must use a strict prompt so Claude only answers from retrieved context and refuses unsupported questions.
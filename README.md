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

## Phase D — Migration to Amazon Bedrock Knowledge Base

Migrated the RAG system from a hand-built local pipeline to a fully-managed AWS Bedrock Knowledge Base.

### Architecture change

**Before (Phase B — local):**
PDFs → PyPDFLoader → text splitter → Titan embeddings → FAISS → Claude

**After (Phase D — managed):**
PDFs in S3 → Bedrock Knowledge Base (managed parsing, chunking, embeddings, vector store) → Retrieve API → Claude

### Setup
- **S3 bucket:** `ask-my-docs-kb-863760760863` (5 programming-language PDFs)
- **Knowledge Base:** `ask-my-docs-bedrock-kb` (type: MANAGED, fully-managed vector store)
- **Embeddings:** `amazon.titan-embed-text-v2:0`, 1024 dimensions
- **IAM:** service role scoped to read-only access on the single KB bucket, account-conditioned (least privilege, verified)

### Phase D files
- `bedrock_kb_retrieve.py` — retrieves raw chunks from the KB, prints source documents
- `bedrock_kb_answer.py` — retrieves chunks → Claude answers only from retrieved context
- `bedrock_kb_ask.py` — interactive terminal chatbot on the Bedrock KB
- `evaluate_bedrock_kb.py` — evaluation suite for the KB version

### Results — Bedrock KB vs local FAISS

| System | Score | Cross-document comparison |
|--------|-------|---------------------------|
| Local FAISS (Phase C) | 8/9 (89%) | ❌ failed |
| Bedrock KB (Phase D) | 9/9 (100%) | ✅ passed |

The managed Knowledge Base handled the cross-document comparison question that the hand-built FAISS system failed — a meaningful improvement.

### Technical notes
- Managed KBs require `managedSearchConfiguration` in the Retrieve API — `vectorSearchConfiguration` is not supported and returns an error.
- Grounding is not automatic: strict prompt instructions ("answer only from retrieved documents; otherwise say you don't know") were required to stop the model answering out-of-scope questions from its own knowledge.
- Fully-managed KB = no standalone vector database (OpenSearch/Aurora) in the account, so no idle hourly cost — only pay-per-use embeddings, retrieval, and generation.
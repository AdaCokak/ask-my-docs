# Regulatory Intelligence System (Ask-My-Docs → RegIntel)

An AI-powered regulatory-change intelligence system built on AWS Bedrock. It ingests real UK legislation from official government APIs, answers questions grounded in that legislation, detects which laws have changed recently, and uses an autonomous agent to reason across tools and deliver business-focused regulatory analysis.

Built as a learning project by a recent CS graduate, evolving from a basic RAG chatbot into a full agentic system on AWS.

## What it does

- **Ingests real UK legislation** (Data Protection Act 2018, Equality Act 2010, Modern Slavery Act 2015, Bribery Act 2010, Health and Safety at Work Act 1974) from the legislation.gov.uk API, automatically on a daily schedule.
- **Answers legal questions** grounded in the legislation, with source citations, via retrieval-augmented generation (RAG).
- **Extracts structured intelligence** — what each law regulates, who it affects, key obligations — as machine-readable JSON.
- **Detects recent changes** using each act's official modified date.
- **Runs an autonomous agent** that reasons over a knowledge base and custom tools to answer questions like "which laws changed recently and how do they affect my business?"

## Architecture

legislation.gov.uk API
│
▼
Lambda (scheduled daily via EventBridge)
├─ fetch acts → parse CLML XML → extract text + metadata
├─ upload to S3
└─ trigger Knowledge Base sync
│
▼
S3 bucket ──► Bedrock Knowledge Base (managed vector store, Titan V2 embeddings)
│
▼
Bedrock Agent (Claude Sonnet 4.6)
├─ Knowledge Base (RAG over legislation)
└─ Action group: detect-changes tool (Lambda reads S3, filters by modified date)

## Build phases

- **Phase A** — Bedrock foundation: prompt engineering (system prompts, few-shot, JSON output, temperature).
- **Phase B** — Local RAG pipeline: PyPDFLoader → text splitter → Titan embeddings → FAISS → Claude, with a Gradio UI. Ingestion separated from query.
- **Phase C** — Evaluation & tuning: keyword-scored eval suite; tuned retrieval (k=6 optimal); documented cross-document-comparison limitation.
- **Phase D** — Migrated to a fully-managed Amazon Bedrock Knowledge Base. Scored 9/9 vs local FAISS 8/9 (managed KB handled cross-document comparison FAISS failed). IAM verified least-privilege.
- **Phase E** — Real UK legislation: fetch from government API → parse CLML XML (content under `Primary`, not `Body`) → S3 → KB. Structured intelligence extraction to JSON. Automated ingestion via Lambda + EventBridge (daily), with graceful handling of timeouts and concurrent-sync race conditions.
- **Phase F** — Agentic layer: a Bedrock Agent (Agents Classic) with the legislation KB attached and a custom `detect-changes` action group (Lambda-backed tool). The agent autonomously decides to call the tool, reads the result, and delivers business-focused analysis.

## Key files

| File | Purpose |
|------|---------|
| `first_call.py` | Prompt engineering experiments (Phase A) |
| `ingest.py` / `ask.py` / `app.py` | Local FAISS RAG pipeline + Gradio UI (Phase B) |
| `evaluate.py` | Evaluation suite (Phase C) |
| `bedrock_kb_*.py` | Bedrock Knowledge Base scripts (Phase D) |
| `extract_legislation.py` / `fetch_acts.py` | Legislation fetch + CLML XML extraction (Phase E) |
| `extract_intelligence.py` | Structured intelligence extraction to `intelligence.json` (Phase E) |
| `lambda_ingest/lambda_function.py` | Scheduled ingestion Lambda (Phase E) |
| `lambda_ingest/detect_changes.py` | Agent tool: detect recently-changed acts (Phase F) |

## Tech stack

AWS Bedrock (Knowledge Bases, Agents, Claude Sonnet 4.6, Titan embeddings), AWS Lambda, EventBridge, S3, IAM, LangChain, FAISS, Gradio, Python.

## Engineering notes & lessons

- **Corpus hygiene matters** — mixed/duplicate documents pollute retrieval and confuse tools; deterministic filenames prevent debris accumulation.
- **Grounding is a design choice** — the agent will blend retrieved content with model knowledge unless instructed to stay strictly grounded; critical for regulatory accuracy.
- **Real production debugging** — solved Lambda deploy verification (SHA-256), timeouts, concurrent-ingestion race conditions (ConflictException handling), and Bedrock→Lambda resource-based permissions.
- **Least privilege** — IAM roles and resource policies scoped to specific buckets/agents, not blanket access.

## Known limitations (deliberate scope)

- Ingests the `/introduction` section of each act (metadata-rich, content-light) to prove the multi-act pipeline. Full-provision ingestion and large-scale handling (streaming parsers, parallel processing, incremental change-detection) are documented as the scaling path.
- Cross-document comparison via single-vector retrieval is limited (resolved by the managed KB; further improvable with query decomposition / reranking).

## Roadmap

- Additional agent tools (full intelligence extraction per act) for multi-tool orchestration.
- Production hardening: API Gateway front-end, Bedrock Guardrails, CloudWatch dashboards, pytest, CI/CD.
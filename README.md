# DocuMind AI

> Multi-modal RAG system with hybrid retrieval, cross-encoder reranking, and production observability.

[Python](https://python.org)
[FastAPI](https://fastapi.tiangolo.com)
[React](https://react.dev)
[Weaviate](https://weaviate.io)
[Claude](https://anthropic.com)
[Langfuse](https://langfuse.com)

DocuMind AI Demo

**Live demo:** [documind-ai-inky.vercel.app](https://documind-ai-inky.vercel.app) |
**API docs:** [/docs](http://localhost:8000/docs) |
**Observability:** [Langfuse Dashboard](https://cloud.langfuse.com)

---

## What it does

Upload any PDF → ask questions in natural language → get grounded answers with exact page citations.

Built to demonstrate production-grade RAG engineering:

| Capability          | Implementation                                  |
| ------------------- | ----------------------------------------------- |
| Multi-modal parsing | Unstructured.io — text, tables, embedded images |
| Hybrid retrieval    | BM25 + dense vector search with RRF fusion      |
| Reranking           | BAAI/bge-reranker-v2-m3 cross-encoder           |
| Generation          | Claude Sonnet 4.6 with grounded prompting       |
| Observability       | Langfuse — traces, cost, latency per query      |
| Storage             | Weaviate (self-hosted on AWS EC2) + S3          |

---

## Architecture

```
User uploads PDF
      │
      ▼
┌─────────────────────────────────────────────────┐
│  Ingestion Pipeline                             │
│                                                 │
│  S3 ← original PDF (safe, retrievable)          │
│                                                 │
│  Unstructured.io → text chunks                  │
│                  → table chunks (HTML)          │
│                  → image captions (Claude vision│
│                                                 │
│  sentence-transformers → 384-dim vectors        │
│                                                 │
│  Weaviate ← chunks + vectors stored             │
└─────────────────────────────────────────────────┘
      │
      │  User asks question
      ▼
┌─────────────────────────────────────────────────┐
│  Retrieval Pipeline                             │
│                                                 │
│  Query → embed → dense search (Weaviate)        │
│       → tokenise → BM25 keyword search          │
│                                                 │
│  RRF fusion → top-20 candidates                 │
│                                                 │
│  BGE cross-encoder → rerank → top-5             │
└─────────────────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────────────────┐
│  Generation                                     │
│                                                 │
│  Claude Sonnet 4.6 + context chunks             │
│  → grounded answer with page citations          │
│  → cost tracked ($0.002–0.007 per query)        │
│                                                 │
│  Langfuse traces every step end-to-end          │
└─────────────────────────────────────────────────┘
```

---

## Tech stack

**Backend**

- FastAPI — REST API with automatic OpenAPI docs
- Weaviate 1.27.2 — self-hosted vector database on AWS EC2 (Mumbai)
- AWS S3 — original PDF storage
- Unstructured.io — multi-modal PDF parsing (hi_res strategy)
- sentence-transformers/all-MiniLM-L6-v2 — local embeddings (384-dim)
- BAAI/bge-reranker-v2-m3 — cross-encoder reranker
- rank-bm25 — keyword search
- Anthropic Claude Sonnet 4.6 — answer generation
- Langfuse — LLM observability (traces, cost, latency)

**Frontend**

- React 18 + Vite
- Space Grotesk + Inter + JetBrains Mono
- Drag-and-drop PDF upload (react-dropzone)
- Real-time pipeline stage visualization
- Per-query cost and source citation display

**Infrastructure**

- AWS EC2 t3.small (ap-south-1 Mumbai) — Weaviate + FastAPI
- AWS S3 — document storage
- Docker + Docker Compose — Weaviate containerisation
- Vercel — React frontend deployment

---

## Evaluation results

Evaluated using [Ragas 0.2.15](https://github.com/vibrantlabsai/ragas) with Claude Sonnet 4.6
as the eval LLM and sentence-transformers/all-MiniLM-L6-v2 for embeddings.
Dataset: 25-question golden set covering factual extraction, table lookups, multi-hop reasoning,
and out-of-scope queries. Full methodology: [`evals/ragas_eval.ipynb`](evals/ragas_eval.ipynb)

| Metric              | Score | Interpretation                                                  |
| ------------------- | ----- | --------------------------------------------------------------- |
| Answer correctness  | 0.93  | Answers factually match ground truth across 25 diverse Q&A pairs |
| Context recall      | 0.96  | Retrieval surfaces required information 96% of the time         |
| Answer relevancy    | 0.85  | Answers address the questions asked                             |
| Context precision   | 0.84  | Low noise in retrieved chunks — RRF fusion working as intended  |

**Dataset design:** 25 questions across 6 categories — factual extraction (Q1-8), table lookups
(Q9-13), inference/reasoning (Q14-18), multi-hop (Q19-21), product/tech (Q22-23), and
out-of-scope queries (Q24-25) where the system should decline rather than hallucinate.

**Note on faithfulness metric:** Excluded due to a known parsing incompatibility between
Ragas 0.2.15 and Claude Sonnet 4.6 (silent zero verdicts on correctly grounded answers).
`answer_correctness` used instead — measures factual accuracy against verified ground truth,
which is more meaningful for document Q&A evaluation.

**Key findings:**

- Context recall (0.96): Hybrid BM25 + dense search with RRF reliably surfaces required
  information — strongest result across the eval suite
- Answer correctness (0.93): Claude generates factually accurate answers across diverse
  question types including multi-hop reasoning over financial tables
- Context precision (0.84): Multi-hop questions pull in slightly more chunks than needed —
  identified as the primary retrieval optimization target
- Out-of-scope handling: System correctly declines on questions with no answer in the document
  (employee headcount, profit margin) without hallucinating responses

---

## Observability

Every query is fully traced in Langfuse:

```
documind-ai:POST:/api/v1/query        23.07s  $0.006984
  └── api-query-endpoint              23.07s  $0.006984
        └── documind-generation        5.75s  $0.006984
              └── anthropic.chat        5.74s  808→304 tokens
```

Metrics tracked per query:

- Token usage (input / output)
- Cost in USD and INR
- End-to-end latency
- Retrieval stage breakdown

---

## Project structure

```
documind-ai/
├── ingestion/
│   ├── parser.py           # Unstructured.io PDF parsing
│   ├── embedder.py         # sentence-transformers embeddings
│   ├── weaviate_store.py   # Weaviate CRUD + search
│   └── s3_handler.py       # AWS S3 upload/download
├── retrieval/
│   ├── hybrid_search.py    # BM25 + dense + RRF fusion
│   └── reranker.py         # BGE cross-encoder reranking
├── generation/
│   └── claude_generator.py # Grounded answer generation
├── observability/
│   ├── langfuse_setup.py   # Langfuse initialisation
│   ├── middleware.py       # HTTP request tracing
│   ├── tracer.py           # Custom span helpers
│   └── cost_calculator.py  # Per-query cost tracking
├── api/
│   ├── ingest.py           # POST /api/v1/ingest
│   └── query.py            # POST /api/v1/query
├── evals/
│   ├── ragas_eval.ipynb    # Ragas evaluation notebook
│   └── golden_dataset.py   # 25-question golden eval dataset
├── frontend/               # React + Vite UI
├── main.py                 # FastAPI app entry point
└── test_connections.py     # Service health check
```

---

## Local setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker Desktop
- AWS account (free tier)
- Anthropic API key
- Langfuse account (free)

### 1. Clone and install

```bash
git clone https://github.com/yashumz/documind-ai.git
cd documind-ai
uv sync
```

### 2. Configure environment

```bash
cp .env.example .env
# Fill in your API keys
```

### 3. Start Weaviate

```bash
# SSH into your EC2 instance
ssh -i your-key.pem ubuntu@YOUR_EC2_IP
cd ~/documind-ai && docker compose up -d
```

### 4. Run backend

```bash
uv run uvicorn main:app --reload --port 8000
```

### 5. Run frontend

```bash
cd frontend && npm install && npm run dev
# Open http://localhost:3000
```

### 6. Verify all connections

```bash
uv run python test_connections.py
# ✅ Weaviate · ✅ S3 · ✅ Anthropic · ✅ Langfuse
```

### 7. Run evals

```bash
cd evals
jupyter notebook ragas_eval.ipynb
```

---

## API reference

### POST `/api/v1/ingest`

Upload a PDF for processing.

```bash
curl -X POST http://localhost:8000/api/v1/ingest \
  -F "file=@document.pdf"
```

Response:

```json
{
  "filename": "document.pdf",
  "s3_key": "uploads/2026/06/28/abc123_document.pdf",
  "total_chunks": 47,
  "text_chunks": 38,
  "table_chunks": 7,
  "image_chunks": 2,
  "message": "Successfully ingested document.pdf — 47 chunks ready"
}
```

### POST `/api/v1/query`

Ask a question about ingested documents.

```bash
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What was Q3 revenue?", "source": "document.pdf"}'
```

Response:

```json
{
  "answer": "According to page 3 of document.pdf, Q3 revenue was $18.6M...",
  "sources_used": [["document.pdf", 3], ["document.pdf", 1]],
  "chunks_used": 5,
  "model": "claude-sonnet-4-6",
  "cost_usd": 0.006624,
  "cost_inr": 0.5531
}
```

---

## Resume bullets

```
- Built DocuMind AI — production multi-modal RAG system ingesting PDFs
  (text + tables + images) using Unstructured.io and Claude Vision,
  deployed on AWS EC2 with Weaviate vector database

- Implemented hybrid BM25 + dense retrieval with RRF fusion and BGE
  cross-encoder reranking; evaluated with Ragas across 25-question golden
  dataset — answer correctness 0.93, context recall 0.96

- Designed structured eval framework with 6 question categories (factual,
  table lookup, multi-hop, inference, out-of-scope); identified context
  precision gap in multi-hop queries as primary optimization target

- Instrumented full pipeline with Langfuse observability — tracking token
  cost, latency, and retrieval metrics per query; average $0.006/query
  with full trace visibility

- Deployed React frontend (Neural Terminal design) with real-time pipeline
  stage visualization, drag-drop upload, and per-query cost and citation display
```

---

## Built by

**Yashaswini V** — Senior Software Engineer pivoting to AI/ML Engineering

[GitHub](https://github.com/yashumz) · [LinkedIn](https://linkedin.com/in/yourprofile)

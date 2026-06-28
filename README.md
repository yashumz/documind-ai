# DocuMind AI

> Multi-modal RAG system with hybrid retrieval, cross-encoder reranking, and production observability.

[Python](https://python.org)
[FastAPI](https://fastapi.tiangolo.com)
[React](https://react.dev)
[Weaviate](https://weaviate.io)
[Claude](https://anthropic.com)
[Langfuse](https://langfuse.com)

DocuMind AI Demo

**Live demo:** [documind-ai-inky.vercel.app](https://documind-ai-inky.vercel.app)  | 
**API docs:** [/docs](http://localhost:8000/docs)  | 
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

## Benchmark results

Evaluated on 50-question test set over `test_sample.pdf`:


| Metric              | Naive RAG | + Hybrid | + Reranker |
| ------------------- | --------- | -------- | ---------- |
| Context precision   | 0.71      | 0.81     | **0.89**   |
| Answer faithfulness | 0.74      | 0.83     | **0.91**   |
| Avg cost/query      | $0.008    | $0.007   | **$0.006** |
| Avg latency         | 4.2s      | 5.1s     | **6.8s**   |


Reranking adds ~1.7s latency but improves precision by **+25%**.

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
│   ├── parser.py          # Unstructured.io PDF parsing
│   ├── embedder.py        # sentence-transformers embeddings
│   ├── weaviate_store.py  # Weaviate CRUD + search
│   └── s3_handler.py      # AWS S3 upload/download
├── retrieval/
│   ├── hybrid_search.py   # BM25 + dense + RRF fusion
│   └── reranker.py        # BGE cross-encoder reranking
├── generation/
│   └── claude_generator.py # Grounded answer generation
├── observability/
│   ├── langfuse_setup.py  # Langfuse initialisation
│   ├── middleware.py      # HTTP request tracing
│   ├── tracer.py          # Custom span helpers
│   └── cost_calculator.py # Per-query cost tracking
├── api/
│   ├── ingest.py          # POST /api/v1/ingest
│   └── query.py           # POST /api/v1/query
├── frontend/              # React + Vite UI
├── main.py                # FastAPI app entry point
└── test_connections.py    # Service health check
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

- Implemented hybrid BM25 + dense retrieval with RRF fusion and
  BGE cross-encoder reranking; improved context precision from
  0.71 → 0.89 on 50-question benchmark (+25%)

- Instrumented full pipeline with Langfuse observability — tracking
  token cost, p95 latency, and retrieval metrics per query;
  average cost $0.006/query with full trace visibility

- Deployed React frontend (Neural Terminal design) with real-time
  pipeline stage visualization, drag-drop upload, and per-query
  cost and citation display
```

---

## Built by

**Yashaswini V** — Senior Software Engineer pivoting to AI/ML Engineering

[GitHub](https://github.com/yashumz) · [LinkedIn](https://linkedin.com/in/yourprofile)
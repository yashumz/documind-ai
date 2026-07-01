# main.py
# ─────────────────────────────────────────────────────────────
# DocuMind AI — FastAPI application entry point
#
# Wires together:
#   → Langfuse observability (auto-traces all LLM calls)
#   → API routes (ingest + query)
#   → Middleware (request tracing)
#
# Run with:
#   uv run uvicorn main:app --reload --port 8000
# ─────────────────────────────────────────────────────────────

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# ── Import API routers ────────────────────────────────────────
from api.ingest import router as ingest_router
from api.query  import router as query_router

from observability.langfuse_setup import setup_langfuse, flush_langfuse
from observability.middleware import LangfuseTracingMiddleware


# ── Lifespan: runs at startup and shutdown ────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):

    # ── STARTUP ───────────────────────────────────────────────
    print("\n" + "=" * 55)
    print("  DocuMind AI — Starting up")
    print("=" * 55)

    # NEW: Setup Langfuse first — before anything else
    setup_langfuse()

    # Verify Weaviate is reachable
    try:
        from ingestion.weaviate_store import get_client, ensure_collection
        client = get_client()
        ensure_collection(client)
        client.close()
        print("✅ Weaviate connected")
    except Exception as e:
        print(f"⚠️  Weaviate connection failed: {e}")
        print("   Make sure EC2 instance is running")

    # Verify embedding model loads
    try:
        from ingestion.embedder import embed_query
        embed_query("test")
        print("✅ Embedding model ready")
    except Exception as e:
        print(f"⚠️  Embedding model failed: {e}")

    print("=" * 55)
    print("  DocuMind AI — Ready to serve requests")
    print("=" * 55 + "\n")

    yield  # App runs here

    # ── SHUTDOWN ──────────────────────────────────────────────
    print("\n[DocuMind] Shutting down...")
    flush_langfuse()    # NEW: flush pending traces
    print("[DocuMind] ✅ Goodbye!")

# Verify embedding model loads
    try:
        from ingestion.embedder import embed_query
        embed_query("test")
        print("✅ Embedding model ready")
    except Exception as e:
        print(f"⚠️  Embedding model failed: {e}")

    print("=" * 55)
    print("  DocuMind AI — Ready to serve requests")
    print("=" * 55 + "\n")

    yield  # App runs here

    # ── SHUTDOWN ──────────────────────────────────────────────
    print("\n[DocuMind] Shutting down...")
    print("[DocuMind] ✅ Goodbye!")


# ── Create FastAPI app ────────────────────────────────────────
app = FastAPI(
    title="DocuMind AI",
    description=(
        "Multi-modal RAG system with hybrid retrieval, "
        "cross-encoder reranking, and LLM observability"
    ),
    version="1.0.0",
    lifespan=lifespan,
)
app.add_middleware(LangfuseTracingMiddleware)

# ── CORS middleware ───────────────────────────────────────────
# CORS = Cross-Origin Resource Sharing
# Allows our React frontend (different port) to call the API
#
# Real life: Like a security policy that says
#            "only these websites can call our API"
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # Allow all origins for now
    allow_credentials=True,
    allow_methods=["*"],        # Allow GET, POST, etc.
    allow_headers=["*"],
)

# ── Register routes ───────────────────────────────────────────
# prefix="/api/v1" means all routes start with /api/v1/
# e.g. POST /api/v1/ingest
#      POST /api/v1/query
app.include_router(ingest_router, prefix="/api/v1")
app.include_router(query_router,  prefix="/api/v1")


# ── Health check endpoint ─────────────────────────────────────
@app.get("/health")
async def health_check():
    """
    WHAT:  Simple endpoint to verify the app is running
    WHY:   Used by monitoring tools and load balancers
           to check if the service is alive

    Real life: Like a "are you there?" ping
               Returns immediately with status OK
    """
    return {
        "status":  "healthy",
        "service": "DocuMind AI",
        "version": "1.0.0",
    }


# ── Root endpoint ─────────────────────────────────────────────
@app.get("/")
async def root():
    """Welcome message with available endpoints."""
    return {
        "service":   "DocuMind AI",
        "version":   "1.0.0",
        "endpoints": {
            "ingest": "POST /api/v1/ingest",
            "query":  "POST /api/v1/query",
            "health": "GET  /health",
            "docs":   "GET  /docs",
        },
    }
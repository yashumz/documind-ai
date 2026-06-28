# api/query.py
# ─────────────────────────────────────────────────────────────
# POST /query endpoint
#
# Accepts a question and runs the full retrieval pipeline:
#   1. Hybrid search (BM25 + dense) in Weaviate
#   2. Rerank top-20 with cross-encoder
#   3. Generate grounded answer with Claude
#
# Returns the answer with sources and cost.
# ─────────────────────────────────────────────────────────────

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ingestion.weaviate_store    import get_client
from retrieval.hybrid_search     import hybrid_search
from retrieval.reranker          import rerank
from generation.claude_generator import generate_answer

router = APIRouter()


# ── Request model ─────────────────────────────────────────────
class QueryRequest(BaseModel):
    """
    WHAT:  Defines what the user must send to /query
    WHY:   FastAPI validates the request body against this

    Real life: Like a query form at the library desk —
               required fields must be filled in

    Fields:
        question: The user's question (required)
        source:   Filter to one document (optional)
                  None = search all documents
        top_k:    How many chunks to retrieve (optional)
                  Default 20 — enough for good coverage
    """
    question: str
    source:   str | None = None
    top_k:    int        = 20


# ── Response model ────────────────────────────────────────────
class QueryResponse(BaseModel):
    """
    WHAT:  Defines the shape of the API response
    WHY:   Consistent format for frontend to parse

    Fields:
        answer:       Claude's generated answer
        sources_used: List of (filename, page) tuples
        chunks_used:  How many chunks Claude saw
        model:        Which Claude model was used
        cost_usd:     Cost of this query in USD
        cost_inr:     Cost of this query in INR
    """
    answer:       str
    sources_used: list
    chunks_used:  int
    model:        str
    cost_usd:     float
    cost_inr:     float


@router.post("/query", response_model=QueryResponse)
async def query_documents(request: QueryRequest):
    """
    WHAT:  Accepts a question and returns a grounded answer
    WHY:   This is the main user-facing endpoint
           Users ask questions, get answers with citations

    Args:
        request: QueryRequest with question and optional filters

    Returns:
        QueryResponse with answer, sources, and cost

    Raises:
        HTTPException 400: If question is empty
        HTTPException 404: If no documents ingested yet
        HTTPException 500: If pipeline fails
    """

    # ── Validate request ──────────────────────────────────────
    if not request.question.strip():
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty"
        )

    print(f"\n[Query] Question: '{request.question}'")
    if request.source:
        print(f"[Query] Filter:   {request.source}")

    weaviate_client = get_client()

    try:
        # ── Step 1: Hybrid search ─────────────────────────────
        print(f"[Query] Step 1/3: Hybrid search...")
        hybrid_results = hybrid_search(
            weaviate_client,
            query=request.question,
            top_k=request.top_k,
            source=request.source,
        )

        if not hybrid_results:
            raise HTTPException(
                status_code=404,
                detail="No documents found. Please ingest documents first."
            )

        # ── Step 2: Rerank ────────────────────────────────────
        print(f"[Query] Step 2/3: Reranking {len(hybrid_results)} results...")
        reranked = rerank(
            query=request.question,
            chunks=hybrid_results,
            top_k=5,            # send top 5 to Claude
        )

        # ── Step 3: Generate answer ───────────────────────────
        print(f"[Query] Step 3/3: Generating answer with Claude...")
        result = generate_answer(
            query=request.question,
            reranked_chunks=reranked,
        )

        print(f"[Query] ✅ Done — cost: ${result['cost']['cost_usd']}")

        return QueryResponse(
            answer=result["answer"],
            sources_used=result["sources_used"],
            chunks_used=result["chunks_used"],
            model=result["model"],
            cost_usd=result["cost"]["cost_usd"],
            cost_inr=result["cost"]["cost_inr"],
        )

    except HTTPException:
        raise

    except Exception as e:
        print(f"[Query] ❌ Pipeline failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Query pipeline failed: {str(e)}"
        )

    finally:
        weaviate_client.close()
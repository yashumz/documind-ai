# retrieval/hybrid_search.py
# ─────────────────────────────────────────────────────────────
# Combines BM25 keyword search + dense vector search
# using Reciprocal Rank Fusion (RRF) to merge results.
#
# Why hybrid?
#   Dense: finds semantically similar chunks
#   BM25:  finds exact keyword matches
#   RRF:   merges both → better than either alone
# ─────────────────────────────────────────────────────────────

from rank_bm25 import BM25Okapi
from ingestion.embedder import embed_query
from ingestion.weaviate_store import dense_search, get_all_chunks


def _tokenise(text: str) -> list[str]:
    """
    WHAT:  Splits text into individual words (tokens)
    WHY:   BM25 works on word lists, not raw strings

    Real life: Like breaking a sentence into
               individual index cards — one per word
               "Revenue grew in Q3" →
               ["revenue", "grew", "in", "q3"]

    Args:
        text: Any string

    Returns:
        List of lowercase words
    """
    return text.lower().split()


def _reciprocal_rank_fusion(
    dense_results: list[dict],
    bm25_results:  list[dict],
    k: int = 60,
) -> list[dict]:
    """
    WHAT:  Merges two ranked lists into one combined list
    WHY:   Each search method has strengths and weaknesses
           RRF rewards documents that rank high in BOTH

    HOW RRF works:
        For each document in each list:
            score += 1 / (k + rank_position)

        k=60 is the standard constant (smooths out
        the difference between rank 1 and rank 2)

        Documents appearing in BOTH lists get scores
        from BOTH calculations added together
        → Higher combined score = more relevant

    Real life: Like two judges scoring contestants.
               A contestant who scores well with BOTH
               judges wins, even if they're not #1
               with either judge individually.

    Args:
        dense_results: Top chunks from vector search
        bm25_results:  Top chunks from BM25 search
        k:             RRF smoothing constant (default 60)

    Returns:
        Merged and re-ranked list of chunks
    """
    # scores dict: text_key → accumulated RRF score
    scores:  dict[str, float] = {}
    # sources dict: text_key → the chunk dict itself
    sources: dict[str, dict]  = {}

    # Score documents from dense search list
    # rank starts at 1 (not 0) — position matters
    for rank, doc in enumerate(dense_results, start=1):
        # Use first 100 chars as unique key
        # (avoids storing full text as key)
        key = doc["text"][:100]
        scores[key]  = scores.get(key, 0) + 1 / (k + rank)
        sources[key] = doc

    # Score documents from BM25 list
    # If a doc appeared in dense too → scores ADD UP
    for rank, doc in enumerate(bm25_results, start=1):
        key = doc["text"][:100]
        scores[key]  = scores.get(key, 0) + 1 / (k + rank)
        if key not in sources:
            sources[key] = doc

    # Sort by descending RRF score
    # Higher score = appeared high in more lists
    sorted_keys = sorted(
        scores,
        key=lambda k: scores[k],
        reverse=True,
    )

    return [
        {
            **sources[key],              # all original chunk fields
            "rrf_score": round(scores[key], 6),  # add RRF score
        }
        for key in sorted_keys
    ]


def hybrid_search(
    weaviate_client,
    query:  str,
    top_k:  int = 20,
    source: str | None = None,
) -> list[dict]:
    """
    WHAT:  Main function — runs hybrid search and returns
           the best matching chunks for a query

    WHY:   Better retrieval = better answers from Claude
           This is the core of what makes DocuMind AI
           better than a basic RAG system

    HOW:
        1. Embed the query → vector
        2. Dense search in Weaviate (semantic)
        3. BM25 search over all chunks (keyword)
        4. RRF fusion → merged ranked list
        5. Return top_k results

    Args:
        weaviate_client: Open Weaviate connection
        query:           User's natural language question
        top_k:           How many results to return
        source:          Filter to one document (None = all)

    Returns:
        List of top_k chunk dicts with rrf_score field
        Sorted by relevance (most relevant first)
    """

    # ── STEP 1: Dense search ──────────────────────────────────
    # Convert query to vector then find similar chunks
    print(f"[Hybrid] Query: '{query[:50]}...' " if len(query) > 50
          else f"[Hybrid] Query: '{query}'")

    query_vector  = embed_query(query)
    dense_results = dense_search(
        weaviate_client,
        query_vector,
        top_k=top_k,
        source_filter=source,
    )
    print(f"[Hybrid] Dense results:  {len(dense_results)}")

    # ── STEP 2: BM25 keyword search ───────────────────────────
    # Get all chunks from Weaviate to build BM25 index
    # BM25 needs the full corpus to calculate word frequencies
    corpus_chunks = get_all_chunks(weaviate_client, source=source)

    if not corpus_chunks:
        print("[Hybrid] ⚠️  No chunks in Weaviate — skipping BM25")
        return dense_results[:top_k]

    # Build BM25 index from corpus
    # Each chunk's text is tokenised into a word list
    tokenised_corpus = [_tokenise(c["text"]) for c in corpus_chunks]
    bm25             = BM25Okapi(tokenised_corpus)

    # Score all corpus chunks against the query
    query_tokens = _tokenise(query)
    bm25_scores  = bm25.get_scores(query_tokens)

    # Get top_k BM25 results (sorted by score)
    top_indices = sorted(
        range(len(bm25_scores)),
        key=lambda i: bm25_scores[i],
        reverse=True,
    )[:top_k]

    # Build BM25 results list (only include non-zero scores)
    bm25_results = [
        {
            **corpus_chunks[i],
            "score":     float(bm25_scores[i]),
            "retrieval": "bm25",
        }
        for i in top_indices
        if bm25_scores[i] > 0
    ]
    print(f"[Hybrid] BM25 results:   {len(bm25_results)}")

    # ── STEP 3: RRF fusion ────────────────────────────────────
    fused = _reciprocal_rank_fusion(dense_results, bm25_results)
    print(f"[Hybrid] Fused results:  {len(fused)} → returning top {top_k}")

    return fused[:top_k]
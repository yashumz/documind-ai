# retrieval/reranker.py
# ─────────────────────────────────────────────────────────────
# Cross-encoder reranker using transformers directly
# Avoids FlagEmbedding tokenizer compatibility issue
#
# Model: BAAI/bge-reranker-v2-m3
# Already downloaded — no re-download needed
# ─────────────────────────────────────────────────────────────

import os
import torch
import torch.nn.functional as F
from transformers import AutoModelForSequenceClassification, AutoTokenizer
from dotenv import load_dotenv

load_dotenv()

_RERANKER_MODEL = os.getenv("RERANKER_MODEL", "BAAI/bge-reranker-v2-m3")
_tokenizer = None
_model     = None


def _get_reranker():
    """
    WHAT:  Loads reranker tokenizer + model (only once)
    WHY:   2.27GB model — load once, reuse always

    Real life: Like hiring a senior expert who stays
               on staff permanently
    """
    global _tokenizer, _model

    if _model is None:
        print(f"[Reranker] Loading: {_RERANKER_MODEL}")
        print(f"[Reranker] (already downloaded — loading from cache)")

        _tokenizer = AutoTokenizer.from_pretrained(_RERANKER_MODEL)
        _model     = AutoModelForSequenceClassification.from_pretrained(
            _RERANKER_MODEL
        )
        _model.eval()  # inference mode — not training
        print(f"[Reranker] ✅ Ready")

    return _tokenizer, _model


def rerank(
    query:  str,
    chunks: list[dict],
    top_k:  int = 5,
) -> list[dict]:
    """
    WHAT:  Re-scores chunks against query using cross-encoder
    WHY:   More accurate than embedding similarity

    HOW:
        1. Build pairs: [[query, chunk1], [query, chunk2]...]
        2. Feed each pair through the model together
        3. Model outputs a relevance score for each pair
        4. Sort by score → return top_k

    Args:
        query:  User's question
        chunks: List of chunk dicts (top-20 from hybrid search)
        top_k:  How many to return after reranking

    Returns:
        top_k chunks sorted by reranker score (highest first)
    """
    if not chunks:
        print("[Reranker] ⚠️  No chunks to rerank")
        return []

    tokenizer, model = _get_reranker()

    # Build pairs: [[query, chunk_text], ...]
    pairs = [[query, chunk["text"]] for chunk in chunks]

    print(f"[Reranker] Reranking {len(pairs)} chunks → top {top_k}...")

    # Tokenize all pairs at once
    # padding=True    → same length for batch processing
    # truncation=True → cut if too long
    # max_length=512  → model's max input size
    encoded = tokenizer(
        pairs,
        padding=True,
        truncation=True,
        max_length=512,
        return_tensors="pt",
    )

    # Run model — no gradient needed (inference only)
    with torch.no_grad():
        output = model(**encoded)

    # output.logits shape: [num_pairs, 1] or [num_pairs, 2]
    # For reranker models: single score per pair
    logits = output.logits

    # Handle both single-score and two-class output
    if logits.shape[-1] == 1:
        # Single relevance score
        raw_scores = logits.squeeze(-1)
    else:
        # Two-class (relevant/not-relevant) → take positive class
        raw_scores = logits[:, 1]

    # Sigmoid converts raw scores to [0, 1] range
    # 1.0 = perfectly relevant, 0.0 = not relevant
    scores = torch.sigmoid(raw_scores).tolist()

    # Attach score to each chunk
    for chunk, score in zip(chunks, scores):
        chunk["reranker_score"] = round(float(score), 4)

    # Sort by score — highest first
    ranked = sorted(
        chunks,
        key=lambda c: c["reranker_score"],
        reverse=True,
    )

    # Log results
    if ranked:
        best  = ranked[0]["reranker_score"]
        worst = ranked[min(top_k - 1, len(ranked) - 1)]["reranker_score"]
        print(f"[Reranker] ✅ Done")
        print(f"[Reranker] Best score:  {best}")
        print(f"[Reranker] Worst kept:  {worst}")

    return ranked[:top_k]
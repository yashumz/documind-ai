# observability/tracer.py
# ─────────────────────────────────────────────────────────────
# Manual tracing helpers for adding custom spans
# to the Langfuse trace tree.
#
# Use these to trace non-LLM steps like:
#   → hybrid_search() duration
#   → reranker() duration
#   → parse_document() duration
# ─────────────────────────────────────────────────────────────

import time
from functools import wraps
from typing import Any


def trace_span(name: str, metadata: dict | None = None):
    """
    WHAT:  Decorator that wraps a function in a Langfuse span
    WHY:   Lets us see timing for non-LLM steps in the dashboard

    Real life: Like adding a timestamp card to each
               step in a manufacturing process so you
               can see where time is being spent

    Usage:
        @trace_span("hybrid-search")
        def hybrid_search(client, query, top_k):
            ...

        @trace_span("reranker", {"model": "bge-reranker-v2-m3"})
        def rerank(query, chunks, top_k):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                from langfuse import get_client
                langfuse = get_client()

                with langfuse.start_as_current_observation(
                    as_type="span",
                    name=name,
                ) as span:
                    if metadata:
                        span.update(metadata=metadata)

                    start = time.time()
                    result = func(*args, **kwargs)
                    elapsed = round((time.time() - start) * 1000, 2)

                    span.update(output={"latency_ms": elapsed})
                    return result

            except Exception:
                # Tracing failure must never break the function
                return func(*args, **kwargs)

        return wrapper
    return decorator


def log_retrieval_metrics(
    query:          str,
    dense_count:    int,
    bm25_count:     int,
    reranked_count: int,
    latency_ms:     float,
) -> None:
    """
    WHAT:  Logs retrieval pipeline metrics to Langfuse
    WHY:   Helps us understand retrieval quality over time:
           → Are we finding enough results?
           → Is reranking filtering too aggressively?
           → How does latency vary by query type?

    Real life: Like a factory quality log that records
               how many items passed each inspection stage
    """
    try:
        from langfuse import get_client
        langfuse = get_client()

        langfuse.create_score(
            name="retrieval-dense-count",
            value=dense_count,
        )
        langfuse.create_score(
            name="retrieval-bm25-count",
            value=bm25_count,
        )
        langfuse.create_score(
            name="retrieval-reranked-count",
            value=reranked_count,
        )
        langfuse.create_score(
            name="retrieval-latency-ms",
            value=latency_ms,
        )

    except Exception:
        pass  # never crash on observability failure


def log_cost(cost_usd: float, model: str) -> None:
    """
    WHAT:  Logs per-query cost to Langfuse as a score
    WHY:   Lets us track cost trends in the dashboard
           → Which queries are most expensive?
           → Is cost increasing over time?
           → Which documents need more chunks?

    Real life: Like a till receipt that records
               the cost of every customer transaction
    """
    try:
        from langfuse import get_client
        langfuse = get_client()

        langfuse.create_score(
            name="cost-usd",
            value=cost_usd,
            comment=f"model={model}",
        )

    except Exception:
        pass
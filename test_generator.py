# test_generator.py
# Tests the full generation pipeline:
# query → hybrid search → rerank → Claude answer

from ingestion.weaviate_store import (
    get_client,
    ensure_collection,
    store_chunks,
    delete_document_chunks,
)
from ingestion.embedder      import embed_chunks
from retrieval.hybrid_search import hybrid_search
from retrieval.reranker      import rerank
from generation.claude_generator import generate_answer

print("=" * 55)
print("  DocuMind AI — Generator Test")
print("=" * 55)

# Rich sample chunks with real content
sample_chunks = [
    {
        "text":     "DocuMind AI delivered exceptional performance in Q3 2026. Revenue grew 23% year-over-year to reach $18.6M driven by strong enterprise adoption.",
        "type":     "text",
        "page":     1,
        "source":   "annual_report_2026.pdf",
        "metadata": {},
    },
    {
        "text":     "The company expanded operations to Singapore, Dubai, and London in fiscal year 2026, bringing total market presence to 12 countries.",
        "type":     "text",
        "page":     2,
        "source":   "annual_report_2026.pdf",
        "metadata": {},
    },
    {
        "text":     "<table><tr><th>Quarter</th><th>Revenue</th><th>Growth</th><th>Clients</th></tr><tr><td>Q1</td><td>$12.4M</td><td>+15%</td><td>218</td></tr><tr><td>Q2</td><td>$15.1M</td><td>+22%</td><td>251</td></tr><tr><td>Q3</td><td>$18.6M</td><td>+23%</td><td>289</td></tr><tr><td>Q4</td><td>$22.3M</td><td>+20%</td><td>312</td></tr></table>",
        "type":     "table",
        "page":     3,
        "source":   "annual_report_2026.pdf",
        "metadata": {},
    },
    {
        "text":     "Customer retention rate remained strong at 94% reflecting high satisfaction with our document intelligence platform.",
        "type":     "text",
        "page":     4,
        "source":   "annual_report_2026.pdf",
        "metadata": {},
    },
    {
        "text":     "Management expects 2027 revenue of $95M representing 39% year-over-year growth driven by LangGraph multi-agent platform expansion.",
        "type":     "text",
        "page":     5,
        "source":   "annual_report_2026.pdf",
        "metadata": {},
    },
]

client = get_client()

try:
    # ── Setup ─────────────────────────────────────────────────
    print("\n[Setup] Storing chunks in Weaviate...")
    ensure_collection(client)
    vectors  = embed_chunks(sample_chunks)
    inserted = store_chunks(client, sample_chunks, vectors)
    print(f"[Setup] ✅ {inserted} chunks stored")

    # ── Run full pipeline for 3 queries ───────────────────────
    queries = [
        "What was the revenue in Q3 2026?",
        "Which new markets did the company enter?",
        "What is the revenue forecast for 2027?",
    ]

    for i, query in enumerate(queries, 1):
        print(f"\n{'=' * 55}")
        print(f"Query {i}: {query}")
        print("=" * 55)

        # Step 1: Hybrid search
        print("\n[Step 1] Hybrid search...")
        hybrid_results = hybrid_search(
            client,
            query=query,
            top_k=5,
            source="annual_report_2026.pdf",
        )

        # Step 2: Rerank
        print("\n[Step 2] Reranking...")
        reranked = rerank(query, hybrid_results, top_k=3)

        # Step 3: Generate answer
        print("\n[Step 3] Generating answer...")
        result = generate_answer(query, reranked)

        # Display result
        print(f"\n{'─' * 55}")
        print("ANSWER:")
        print(result["answer"])
        print(f"\nCost: ${result['cost']['cost_usd']} "
              f"(₹{result['cost']['cost_inr']})")
        print(f"Sources: {result['sources_used']}")

finally:
    # Cleanup
    print(f"\n\n[Cleanup] Removing test chunks...")
    delete_document_chunks(client, "annual_report_2026.pdf")
    client.close()
    print("[Cleanup] ✅ Done")

print("\n" + "=" * 55)
print("✅ Generator test complete!")
print("=" * 55)
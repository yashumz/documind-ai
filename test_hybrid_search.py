# test_hybrid_search.py
# Tests the full hybrid search pipeline
# Requires chunks to be stored in Weaviate first

from ingestion.weaviate_store import (
    get_client,
    ensure_collection,
    store_chunks,
    delete_document_chunks,
)
from ingestion.embedder   import embed_chunks
from retrieval.hybrid_search import hybrid_search

print("=" * 55)
print("  DocuMind AI — Hybrid Search Test")
print("=" * 55)

# Sample chunks to search through
sample_chunks = [
    {
        "text":     "Revenue grew 23% in Q3 2026 driven by strong enterprise adoption of our RAG platform",
        "type":     "text",
        "page":     1,
        "source":   "test_hybrid.pdf",
        "metadata": {},
    },
    {
        "text":     "The company expanded operations to Singapore, Dubai, and London in fiscal year 2026",
        "type":     "text",
        "page":     1,
        "source":   "test_hybrid.pdf",
        "metadata": {},
    },
    {
        "text":     "Customer retention rate remained strong at 94% reflecting high satisfaction",
        "type":     "text",
        "page":     2,
        "source":   "test_hybrid.pdf",
        "metadata": {},
    },
    {
        "text":     "<table><tr><th>Quarter</th><th>Revenue</th><th>Growth</th></tr><tr><td>Q3</td><td>$18.6M</td><td>+23%</td></tr></table>",
        "type":     "table",
        "page":     2,
        "source":   "test_hybrid.pdf",
        "metadata": {},
    },
    {
        "text":     "Management expects 2027 revenue of $95M representing 39% year-over-year growth",
        "type":     "text",
        "page":     3,
        "source":   "test_hybrid.pdf",
        "metadata": {},
    },
]

client = get_client()

try:
    # Setup — store test chunks
    print("\n[Setup] Storing test chunks in Weaviate...")
    ensure_collection(client)
    vectors  = embed_chunks(sample_chunks)
    inserted = store_chunks(client, sample_chunks, vectors)
    print(f"[Setup] ✅ {inserted} chunks stored")

    # ── Test 1: Semantic query ────────────────────────────────
    print("\n[1/3] Semantic query: 'What were the Q3 earnings?'")
    results = hybrid_search(
        client,
        query="What were the Q3 earnings?",
        top_k=3,
        source="test_hybrid.pdf",
    )
    print(f"\n  Top {len(results)} results:")
    for i, r in enumerate(results, 1):
        print(f"  {i}. score={r['rrf_score']} | [{r['type']}] {r['text'][:70]}...")

    # ── Test 2: Keyword query ─────────────────────────────────
    print("\n[2/3] Keyword query: 'Singapore Dubai London'")
    results = hybrid_search(
        client,
        query="Singapore Dubai London",
        top_k=3,
        source="test_hybrid.pdf",
    )
    print(f"\n  Top {len(results)} results:")
    for i, r in enumerate(results, 1):
        print(f"  {i}. score={r['rrf_score']} | [{r['type']}] {r['text'][:70]}...")

    # ── Test 3: Mixed query ───────────────────────────────────
    print("\n[3/3] Mixed query: 'What is the revenue growth forecast?'")
    results = hybrid_search(
        client,
        query="What is the revenue growth forecast?",
        top_k=3,
        source="test_hybrid.pdf",
    )
    print(f"\n  Top {len(results)} results:")
    for i, r in enumerate(results, 1):
        print(f"  {i}. score={r['rrf_score']} | [{r['type']}] {r['text'][:70]}...")

finally:
    # Cleanup test data
    print("\n[Cleanup] Removing test chunks...")
    delete_document_chunks(client, "test_hybrid.pdf")
    client.close()
    print("[Cleanup] ✅ Done")

print("\n" + "=" * 55)
print("✅ Hybrid search test complete!")
print("=" * 55)
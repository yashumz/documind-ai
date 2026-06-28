# test_weaviate_store.py
from ingestion.weaviate_store import (
    get_client,
    ensure_collection,
    store_chunks,
    dense_search,
    get_all_chunks,
    delete_document_chunks,
)
from ingestion.embedder import embed_chunks, embed_query

print("=" * 55)
print("  DocuMind AI — Weaviate Store Test")
print("=" * 55)

# Sample chunks to test with
sample_chunks = [
    {
        "text":     "Revenue grew 23% in Q3 2026 driven by enterprise adoption",
        "type":     "text",
        "page":     1,
        "source":   "test_report.pdf",
        "metadata": {"element_id": "001"},
    },
    {
        "text":     "The company expanded to Singapore, Dubai, and London",
        "type":     "text",
        "page":     1,
        "source":   "test_report.pdf",
        "metadata": {"element_id": "002"},
    },
    {
        "text":     "<table><tr><th>Quarter</th><th>Revenue</th></tr><tr><td>Q3</td><td>$18.6M</td></tr></table>",
        "type":     "table",
        "page":     2,
        "source":   "test_report.pdf",
        "metadata": {"element_id": "003"},
    },
]

client = get_client()

try:
    # ── Test 1: Create collection ─────────────────────────────
    print("\n[1/5] Creating collection...")
    ensure_collection(client)

    # ── Test 2: Store chunks ──────────────────────────────────
    print("\n[2/5] Storing chunks...")
    vectors  = embed_chunks(sample_chunks)
    inserted = store_chunks(client, sample_chunks, vectors)
    print(f"  ✅ Inserted: {inserted} chunks")

    # ── Test 3: Dense search ──────────────────────────────────
    print("\n[3/5] Testing dense search...")
    query_vector = embed_query("What was the Q3 revenue?")
    results      = dense_search(client, query_vector, top_k=3)

    print(f"  ✅ Found {len(results)} results:")
    for i, r in enumerate(results, 1):
        print(f"  {i}. [{r['type']}] score={r['score']} | {r['text'][:60]}...")

    # ── Test 4: Get all chunks ────────────────────────────────
    print("\n[4/5] Testing get_all_chunks...")
    all_chunks = get_all_chunks(client)
    print(f"  ✅ Total chunks in Weaviate: {len(all_chunks)}")

    # ── Test 5: Delete test chunks ────────────────────────────
    print("\n[5/5] Cleaning up test chunks...")
    deleted = delete_document_chunks(client, "test_report.pdf")
    print(f"  ✅ Deleted: {deleted} chunks")

finally:
    # Always close the connection
    client.close()
    print("\n[Weaviate] Connection closed")

print("\n" + "=" * 55)
print("✅ Weaviate store test complete!")
print("=" * 55)
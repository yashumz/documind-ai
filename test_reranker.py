# test_reranker.py
# NOTE: First run downloads ~300MB model — be patient!

from retrieval.reranker import rerank

print("=" * 55)
print("  DocuMind AI — Reranker Test")
print("=" * 55)

query = "What was the revenue growth in Q3?"

# Simulate chunks from hybrid search
# Mix of relevant and irrelevant chunks
chunks = [
    {
        "text":      "Revenue grew 23% in Q3 2026 driven by enterprise adoption",
        "type":      "text",
        "page":      1,
        "source":    "report.pdf",
        "rrf_score": 0.032,
    },
    {
        "text":      "The company expanded to Singapore, Dubai, and London",
        "type":      "text",
        "page":      1,
        "source":    "report.pdf",
        "rrf_score": 0.028,
    },
    {
        "text":      "<table><tr><th>Quarter</th><th>Revenue</th><th>Growth</th></tr><tr><td>Q3</td><td>$18.6M</td><td>+23%</td></tr></table>",
        "type":      "table",
        "page":      2,
        "source":    "report.pdf",
        "rrf_score": 0.024,
    },
    {
        "text":      "Customer retention rate remained strong at 94%",
        "type":      "text",
        "page":      2,
        "source":    "report.pdf",
        "rrf_score": 0.019,
    },
    {
        "text":      "Management expects 2027 revenue of $95M representing 39% growth",
        "type":      "text",
        "page":      3,
        "source":    "report.pdf",
        "rrf_score": 0.016,
    },
]

print(f"\nQuery: '{query}'")
print(f"Input: {len(chunks)} chunks from hybrid search")
print("\n[Before reranking] Order by RRF score:")
for i, c in enumerate(chunks, 1):
    print(f"  {i}. rrf={c['rrf_score']} | {c['text'][:60]}...")

# Run reranker
print("\n" + "-" * 55)
reranked = rerank(query, chunks, top_k=3)
print("-" * 55)

print(f"\n[After reranking] Top 3 by reranker score:")
for i, c in enumerate(reranked, 1):
    print(f"  {i}. reranker={c['reranker_score']} | {c['text'][:60]}...")

print("\n" + "=" * 55)
print("✅ Reranker test complete!")
print("=" * 55)
# test_embedder.py
import numpy as np
from ingestion.embedder import embed_query, embed_chunks

print("=" * 55)
print("  DocuMind AI — Embedder Test")
print("=" * 55)

# ── Test 1: single query embedding ────────────────────────────
print("\n[1/3] Testing embed_query...")
vector = embed_query("What was the revenue in Q3?")
print(f"  ✅ Vector dimensions: {len(vector)}")
print(f"  ✅ First 5 values: {[round(v, 4) for v in vector[:5]]}")

# ── Test 2: embed multiple chunks ─────────────────────────────
print("\n[2/3] Testing embed_chunks...")
sample_chunks = [
    {"text": "Revenue grew 23% in Q3 2026",                    "type": "text"},
    {"text": "Company expanded to 3 new markets",               "type": "text"},
    {"text": "<table><tr><td>Q3</td><td>$22M</td></tr></table>","type": "table"},
]
vectors = embed_chunks(sample_chunks)
print(f"  ✅ {len(vectors)} chunks embedded")
print(f"  ✅ Each vector: {len(vectors[0])} dimensions")

# ── Test 3: similarity check ──────────────────────────────────
# This proves semantic search will work:
# Similar sentences should score HIGH
# Unrelated sentences should score LOW
print("\n[3/3] Similarity check...")
v1 = embed_query("Revenue grew in Q3")
v2 = embed_query("Earnings increased in third quarter")
v3 = embed_query("The cat sat on the mat")

# dot product of normalised vectors = cosine similarity
# score closer to 1.0 = very similar meaning
# score closer to 0.0 = very different meaning
sim_12 = round(float(np.dot(v1, v2)), 4)
sim_13 = round(float(np.dot(v1, v3)), 4)

print(f"  'Revenue grew Q3' vs 'Earnings Q3':  {sim_12}  ← should be HIGH")
print(f"  'Revenue grew Q3' vs 'Cat on mat':   {sim_13}  ← should be LOW")
print(f"  ✅ Similarity working correctly: {sim_12 > sim_13}")

print("\n" + "=" * 55)
print("✅ Embedder test complete!")
print("=" * 55)
# test_parser.py
import sys
from pathlib import Path
from ingestion.parser import parse_document

SAMPLE_PDF_PATH = "test_sample.pdf"

# Check file exists
if not Path(SAMPLE_PDF_PATH).exists():
    print(f"❌ File not found: {SAMPLE_PDF_PATH}")
    print("Run: uv run python create_test_pdf.py first")
    sys.exit(1)

print("=" * 55)
print("  DocuMind AI — Parser Test")
print("=" * 55)
print(f"\n✅ Using: {SAMPLE_PDF_PATH}")

# Run the parser
print("\n🔄 Running parser (this takes 30-60 seconds)...")
chunks = parse_document(SAMPLE_PDF_PATH)

# Show results
print("\n" + "=" * 55)
print("  RESULTS")
print("=" * 55)
print(f"Total chunks: {len(chunks)}")

print("\n📋 First 3 chunks:\n")
for i, chunk in enumerate(chunks[:3], 1):
    print(f"Chunk {i}:")
    print(f"  Type:   {chunk['type']}")
    print(f"  Page:   {chunk['page']}")
    print(f"  Source: {chunk['source']}")
    print(f"  Text:   {chunk['text'][:150]}")
    print()

print("=" * 55)
print("✅ Parser test complete!")
print("=" * 55)
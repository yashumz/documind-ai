"""
DocuMind AI — Golden Eval Dataset (25 questions)
Source document: test_sample.pdf (DocuMind AI Annual Report 2026)

How to use:
    from golden_dataset import dataset
    Then pass dataset directly to ragas evaluate().

Question categories:
    Q1-Q8   Factual extraction
    Q9-Q13  Table lookups
    Q14-Q18 Inference / reasoning
    Q19-Q21 Multi-hop reasoning
    Q22-Q23 Product / tech specific
    Q24-Q25 Out-of-scope (system should say "not in document")
"""

from datasets import Dataset

GOLDEN_DATA = {
    "question": [
        # FACTUAL EXTRACTION
        "What was DocuMind AI's total revenue in fiscal year 2026?",
        "By what percentage did revenue grow year-over-year in 2026?",
        "What was the customer retention rate in 2026?",
        "How many enterprise clients did DocuMind onboard in Q4 2026?",
        "What is the total client count as of end of fiscal year 2026?",
        "Which three new markets did DocuMind expand into?",
        "What was Q4 2026 revenue?",
        "By what percentage did DocuMind outperform competitors on internal benchmarks?",
        # TABLE LOOKUPS
        "What was Q1 2026 revenue and how many clients did DocuMind have at end of Q1?",
        "Which quarter had the highest revenue growth percentage in 2026?",
        "What was the quarter-over-quarter growth in Q4 2026?",
        "How many clients did DocuMind have at the end of Q2 2026?",
        "What was Q3 2026 revenue?",
        # INFERENCE / REASONING
        "Which sectors drove strong adoption of DocuMind's platform in 2026?",
        "What does the customer retention rate of 94% indicate about DocuMind's platform?",
        "What is DocuMind's projected revenue for 2027?",
        "What are the key growth drivers DocuMind expects for 2027?",
        "What is the projected year-over-year revenue growth for 2027?",
        # MULTI-HOP
        "How much did DocuMind's client count grow between Q1 and Q4 2026?",
        "What was the revenue increase in absolute dollar terms from Q1 to Q4 2026?",
        "How many net new clients were added across Q2, Q3 and Q4 2026?",
        # PRODUCT / TECH
        "What retrieval approach does DocuMind use to achieve state-of-the-art accuracy?",
        "What new platform is mentioned as a key growth driver for 2027?",
        # OUT OF SCOPE
        "What is DocuMind's employee headcount?",
        "What is DocuMind's net profit margin for 2026?",
    ],

    "answer": [
        # FACTUAL
        "DocuMind AI's total revenue in fiscal year 2026 was $68.4M.",
        "Revenue grew 23% year-over-year in fiscal year 2026.",
        "The customer retention rate in 2026 was 94%.",
        "DocuMind onboarded 47 enterprise clients in Q4 2026.",
        "The total client count at end of fiscal year 2026 was 312 organizations.",
        "DocuMind expanded into Singapore, Dubai, and London.",
        "Q4 2026 revenue was $22.3M.",
        "DocuMind outperformed competitors by 18 percentage points on internal benchmarks.",
        # TABLE
        "Q1 2026 revenue was $12.4M and DocuMind had 218 clients at end of Q1.",
        "Q2 2026 had the highest revenue growth at 22%.",
        "Q4 2026 achieved 20% quarter-over-quarter growth.",
        "DocuMind had 251 clients at the end of Q2 2026.",
        "Q3 2026 revenue was $18.6M.",
        # INFERENCE
        "Strong adoption was driven by enterprise customers in banking, healthcare, and legal sectors.",
        "A 94% retention rate indicates high customer satisfaction with the document intelligence platform.",
        "DocuMind's projected revenue for 2027 is $95M.",
        "Key growth drivers for 2027 include the LangGraph multi-agent platform, the MCP server ecosystem, and expansion into government and defence sectors across Asia Pacific.",
        "Projected year-over-year revenue growth for 2027 is 39%.",
        # MULTI-HOP
        "DocuMind's client count grew from 218 at end of Q1 to 312 at end of Q4, an increase of 94 clients.",
        "Revenue increased from $12.4M in Q1 to $22.3M in Q4, an absolute increase of $9.9M.",
        "Starting from 218 clients at end of Q1, DocuMind added 94 net new clients across Q2, Q3, and Q4 to reach 312.",
        # PRODUCT/TECH
        "DocuMind uses a hybrid retrieval system with cross-encoder reranking to achieve state-of-the-art accuracy.",
        "The LangGraph multi-agent platform is mentioned as a key growth driver for 2027.",
        # OUT OF SCOPE
        "The document does not contain information about DocuMind's employee headcount.",
        "The document does not contain information about DocuMind's net profit margin for 2026.",
    ],

    "contexts": [
        # FACTUAL
        ["DocuMind AI delivered exceptional performance in fiscal year 2026. Revenue grew 23% year-over-year driven by strong adoption of our multi-modal RAG platform across enterprise customers in banking, healthcare, and legal sectors.", "Total $68.4M +20% 312"],
        ["Revenue grew 23% year-over-year driven by strong adoption of our multi-modal RAG platform across enterprise customers in banking, healthcare, and legal sectors."],
        ["Customer retention rate remained strong at 94% reflecting high satisfaction with our document intelligence platform."],
        ["We onboarded 47 enterprise clients in Q4 alone, bringing total client count to 312 organizations worldwide."],
        ["We onboarded 47 enterprise clients in Q4 alone, bringing total client count to 312 organizations worldwide."],
        ["The company expanded operations to 3 new markets including Singapore, Dubai, and London."],
        ["Q4 2026 $22.3M +20% 312", "Q4 achieved the highest revenue at $22.3M representing 20% quarter-over-quarter growth."],
        ["Our hybrid retrieval system with cross-encoder reranking achieved state-of-the-art accuracy on internal benchmarks, outperforming competitors by 18 percentage points."],
        # TABLE
        ["Q1 2026 $12.4M +15% 218", "Quarter Revenue Growth Clients"],
        ["Q1 2026 $12.4M +15% 218", "Q2 2026 $15.1M +22% 251", "Q3 2026 $18.6M +23% 289", "Q4 2026 $22.3M +20% 312"],
        ["Q4 achieved the highest revenue at $22.3M representing 20% quarter-over-quarter growth."],
        ["Q2 2026 $15.1M +22% 251"],
        ["Q3 2026 $18.6M +23% 289"],
        # INFERENCE
        ["Revenue grew 23% year-over-year driven by strong adoption of our multi-modal RAG platform across enterprise customers in banking, healthcare, and legal sectors."],
        ["Customer retention rate remained strong at 94% reflecting high satisfaction with our document intelligence platform."],
        ["Management expects continued strong growth in 2027 with projected revenue of $95M representing 39% year-over-year growth."],
        ["Key growth drivers include expansion of our LangGraph multi-agent platform, launch of the MCP server ecosystem, and penetration into the government and defence sectors across Asia Pacific regions."],
        ["Management expects continued strong growth in 2027 with projected revenue of $95M representing 39% year-over-year growth."],
        # MULTI-HOP
        ["Q1 2026 $12.4M +15% 218", "Q4 2026 $22.3M +20% 312"],
        ["Q1 2026 $12.4M +15% 218", "Q4 2026 $22.3M +20% 312"],
        ["Q1 2026 $12.4M +15% 218", "Q2 2026 $15.1M +22% 251", "Q3 2026 $18.6M +23% 289", "Q4 2026 $22.3M +20% 312"],
        # PRODUCT/TECH
        ["Our hybrid retrieval system with cross-encoder reranking achieved state-of-the-art accuracy on internal benchmarks, outperforming competitors by 18 percentage points."],
        ["Key growth drivers include expansion of our LangGraph multi-agent platform, launch of the MCP server ecosystem, and penetration into the government and defence sectors across Asia Pacific regions."],
        # OUT OF SCOPE
        ["DocuMind AI delivered exceptional performance in fiscal year 2026. Revenue grew 23% year-over-year driven by strong adoption of our multi-modal RAG platform."],
        ["Total $68.4M +20% 312", "Quarter Revenue Growth Clients Q1 2026 $12.4M +15% 218 Q2 2026 $15.1M +22% 251 Q3 2026 $18.6M +23% 289 Q4 2026 $22.3M +20% 312"],
    ],

    "ground_truth": [
        # FACTUAL
        "Total revenue in fiscal year 2026 was $68.4M.",
        "Revenue grew 23% year-over-year.",
        "Customer retention rate was 94%.",
        "47 enterprise clients were onboarded in Q4 2026.",
        "Total client count was 312 organizations.",
        "New markets were Singapore, Dubai, and London.",
        "Q4 2026 revenue was $22.3M.",
        "DocuMind outperformed competitors by 18 percentage points.",
        # TABLE
        "Q1 2026 revenue was $12.4M with 218 clients.",
        "Q2 2026 had the highest revenue growth at 22%.",
        "Q4 2026 had 20% quarter-over-quarter growth.",
        "251 clients at end of Q2 2026.",
        "Q3 2026 revenue was $18.6M.",
        # INFERENCE
        "Banking, healthcare, and legal sectors drove strong adoption.",
        "94% retention rate indicates high customer satisfaction.",
        "Projected 2027 revenue is $95M.",
        "Growth drivers are LangGraph multi-agent platform, MCP server ecosystem, and government/defence sectors in Asia Pacific.",
        "Projected 2027 year-over-year growth is 39%.",
        # MULTI-HOP
        "Client count grew by 94 (from 218 to 312).",
        "Revenue increased by $9.9M (from $12.4M to $22.3M).",
        "94 net new clients were added across Q2, Q3, and Q4.",
        # PRODUCT/TECH
        "Hybrid retrieval with cross-encoder reranking.",
        "LangGraph multi-agent platform.",
        # OUT OF SCOPE
        "The document does not contain employee headcount information.",
        "The document does not contain net profit margin information.",
    ],
}

dataset = Dataset.from_dict(GOLDEN_DATA)

if __name__ == "__main__":
    print(f"Golden dataset ready: {len(dataset)} samples")
    print(f"\nCategory breakdown:")
    print(f"  Factual extraction : Q1-Q8   (8 questions)")
    print(f"  Table lookups      : Q9-Q13  (5 questions)")
    print(f"  Inference/reasoning: Q14-Q18 (5 questions)")
    print(f"  Multi-hop          : Q19-Q21 (3 questions)")
    print(f"  Product/tech       : Q22-Q23 (2 questions)")
    print(f"  Out of scope       : Q24-Q25 (2 questions)")

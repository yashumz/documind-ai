# generation/claude_generator.py
# ─────────────────────────────────────────────────────────────
# Sends reranked context chunks to Claude and generates
# a grounded, cited answer.
#
# Key principle: Claude ONLY uses provided context.
# Never answers from general knowledge.
# Always cites which page/source it used.
# ─────────────────────────────────────────────────────────────

import os
import anthropic
from langfuse import observe
from observability.cost_calculator import calculate_cost
from dotenv import load_dotenv

load_dotenv()

# ── Anthropic client ──────────────────────────────────────────
# AnthropicInstrumentor (set up in langfuse_setup.py)
# automatically traces every .messages.create() call
_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# ── System prompt ─────────────────────────────────────────────
# This is the instruction Claude follows for EVERY query
# It defines Claude's role, rules, and output format
SYSTEM_PROMPT = """You are DocuMind AI, an expert document intelligence assistant.

Your job is to answer questions based ONLY on the provided document context.

RULES:
1. Answer ONLY using information from the provided context chunks
2. Always cite your source: "According to page X of [filename]..."
3. If the answer is not in the context, say exactly:
   "I could not find this information in the provided documents."
4. For numerical data (revenue, dates, percentages), quote exactly
   — never round or approximate
5. For table data, preserve the structure in your answer
6. Be concise and direct — no padding or filler phrases

OUTPUT FORMAT:
- Start with a direct answer to the question
- Support with specific evidence from the context
- End with source citations"""


def _build_context_block(chunks: list[dict]) -> str:
    """
    WHAT:  Formats reranked chunks into a clean context
           block for the Claude prompt

    WHY:   Claude needs context in a structured format
           so it can clearly see what each chunk is,
           where it came from, and how relevant it is

    Real life: Like preparing a briefing document
               for a lawyer before they answer questions
               — organized, clearly labeled, easy to read

    Args:
        chunks: Reranked chunk dicts (top 5 from reranker)

    Returns:
        Formatted string with all chunks labeled
    """
    parts = []

    for i, chunk in enumerate(chunks, 1):
        chunk_type    = chunk.get("type", "text")
        source        = chunk.get("source", "unknown")
        page          = chunk.get("page", "?")
        reranker_score = chunk.get("reranker_score", 0)
        rrf_score     = chunk.get("rrf_score", 0)

        # Format score for display
        score = reranker_score if reranker_score else rrf_score

        # Build the chunk header — helps Claude understand context
        header = (
            f"[CHUNK {i} | type={chunk_type} | "
            f"source={source} | page={page} | "
            f"relevance={score:.3f}]"
        )

        parts.append(f"{header}\n{chunk['text']}")

    # Join with clear separator between chunks
    return "\n\n---\n\n".join(parts)


@observe(name="documind-generation", as_type="span")
def generate_answer(
    query:           str,
    reranked_chunks: list[dict],
) -> dict:
    """
    WHAT:  Main function — generates a grounded answer
           from reranked context chunks using Claude

    WHY:   This is the "G" in RAG — Generation
           Claude synthesises the retrieved context
           into a clear, cited, accurate answer

    @observe decorator:
           Wraps this function in a Langfuse span
           All nested Claude API calls appear under
           this span in the Langfuse dashboard

    Args:
        query:           User's natural language question
        reranked_chunks: Top 5 chunks from reranker.py

    Returns:
        {
            "answer":        str,   ← Claude's response
            "sources_used":  list,  ← [(source, page), ...]
            "model":         str,   ← model used
            "cost":          dict,  ← token cost breakdown
            "chunks_used":   int,   ← how many chunks sent
        }
    """
    # ── Build context block ───────────────────────────────────
    context      = _build_context_block(reranked_chunks)
    user_message = (
        f"CONTEXT DOCUMENTS:\n\n{context}\n\n"
        f"QUESTION: {query}"
    )

    print(f"[Generator] Sending {len(reranked_chunks)} chunks to Claude...")
    print(f"[Generator] Context length: {len(context):,} characters")

    # ── Call Claude API ───────────────────────────────────────
    # AnthropicInstrumentor auto-traces this call
    response = _client.messages.create(
        model="claude-sonnet-4-6",      # best quality for answers
        max_tokens=1024,                # enough for detailed answers
        system=SYSTEM_PROMPT,
        messages=[{
            "role":    "user",
            "content": user_message,
        }],
    )

    answer = response.content[0].text

    # ── Calculate cost ────────────────────────────────────────
    cost = calculate_cost(
        model="claude-sonnet-4-6",
        input_tokens=response.usage.input_tokens,
        output_tokens=response.usage.output_tokens,
    )

    # ── Extract unique sources used ───────────────────────────
    # Deduplicated list of (filename, page) pairs
    sources = list({
        (c["source"], c["page"])
        for c in reranked_chunks
    })

    print(f"[Generator] ✅ Answer: {len(answer)} characters")
    print(f"[Generator] Tokens: {response.usage.input_tokens} in / "
          f"{response.usage.output_tokens} out")
    print(f"[Generator] Cost: ${cost['cost_usd']} "
          f"(₹{cost['cost_inr']})")

    return {
        "answer":       answer,
        "sources_used": sources,
        "model":        "claude-sonnet-4-6",
        "cost":         cost,
        "chunks_used":  len(reranked_chunks),
    }
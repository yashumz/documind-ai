# ingestion/embedder.py
# ─────────────────────────────────────────────────────────────
# Uses HuggingFace transformers directly
# Avoids sentence_transformers → sklearn dependency
# Same model, same quality, no DLL issues on Windows
# ─────────────────────────────────────────────────────────────

import os
import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModel
from dotenv import load_dotenv

load_dotenv()

_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
_tokenizer  = None
_model      = None


def _get_model():
    """
    WHAT:  Loads tokenizer + model (only once)
    WHY:   Heavy to load — keep in memory after first load

    Real life: Like starting a car once and keeping
               engine running instead of restarting
               for every trip
    """
    global _tokenizer, _model

    if _model is None:
        print(f"[Embedder] Loading model: {_MODEL_NAME}")
        _tokenizer = AutoTokenizer.from_pretrained(_MODEL_NAME)
        _model     = AutoModel.from_pretrained(_MODEL_NAME)
        _model.eval()  # inference mode — no training
        print(f"[Embedder] ✅ Model ready")

    return _tokenizer, _model


def _mean_pooling(model_output, attention_mask):
    """
    WHAT:  Averages token embeddings into one vector
    WHY:   Model outputs one vector per token (word piece)
           We need ONE vector for the whole sentence

    Real life: Like averaging scores from multiple judges
               to get one final score for a performance
    """
    # model_output[0] = all token embeddings
    token_embeddings = model_output[0]

    # Expand mask to same shape as embeddings
    input_mask_expanded = (
        attention_mask
        .unsqueeze(-1)
        .expand(token_embeddings.size())
        .float()
    )

    # Weighted average — ignore padding tokens (mask=0)
    return torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(
        input_mask_expanded.sum(1), min=1e-9
    )


def embed_texts(texts: list[str]) -> list[list[float]]:
    """
    WHAT:  Converts list of strings into vectors
    WHY:   Weaviate needs vectors for similarity search

    Real life: Converting words into GPS coordinates
               so we can find nearby (similar) content

    Args:
        texts: List of strings to embed

    Returns:
        List of vectors — one per input string
    """
    tokenizer, model = _get_model()

    # Tokenize — converts words to numbers the model understands
    # padding=True    → make all sequences same length
    # truncation=True → cut sequences longer than max_length
    # max_length=512  → model's maximum input size
    encoded = tokenizer(
        texts,
        padding=True,
        truncation=True,
        max_length=512,
        return_tensors="pt",  # return PyTorch tensors
    )

    # Run model — no gradient calculation needed (we're not training)
    with torch.no_grad():
        output = model(**encoded)

    # Pool token embeddings → one vector per sentence
    embeddings = _mean_pooling(output, encoded["attention_mask"])

    # Normalise to unit length
    # Makes cosine similarity = dot product (faster search)
    embeddings = F.normalize(embeddings, p=2, dim=1)

    # Convert to plain Python lists (Weaviate needs this)
    return embeddings.numpy().tolist()


def embed_query(query: str) -> list[float]:
    """
    WHAT:  Embeds a single query string
    WHY:   Used at search time to embed user's question

    Real life: Converting user's question to GPS coordinates
               so we can find nearby document chunks

    Args:
        query: User's question string

    Returns:
        Single vector as list of floats
    """
    return embed_texts([query])[0]


def embed_chunks(chunks: list[dict]) -> list[list[float]]:
    """
    WHAT:  Embeds list of chunk dicts from parser.py
    WHY:   Convenience — takes parser output directly

    Args:
        chunks: List of chunk dicts (must have "text" key)

    Returns:
        List of vectors in same order as input chunks
    """
    texts = [chunk["text"] for chunk in chunks]

    print(f"[Embedder] Embedding {len(texts)} chunks...")
    vectors = embed_texts(texts)
    print(f"[Embedder] ✅ Done — {len(vectors)} vectors")
    print(f"[Embedder] Vector dimension: {len(vectors[0])}")

    return vectors
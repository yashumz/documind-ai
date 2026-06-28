# ingestion/weaviate_store.py
# ─────────────────────────────────────────────────────────────
# Manages all Weaviate operations:
#   → Connect to Weaviate on EC2
#   → Create collection (like a database table)
#   → Store chunks + vectors
#   → Search for similar chunks
# ─────────────────────────────────────────────────────────────

import os
import json
import weaviate
import weaviate.classes as wvc
from weaviate.classes.config import Property, DataType, Configure
from dotenv import load_dotenv

load_dotenv()

# Collection name — like a table name in a database
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "DocuMindChunk")


def get_client() -> weaviate.WeaviateClient:
    """
    WHAT:  Creates a connection to Weaviate on EC2
    WHY:   We need this before any operation

    Real life: Like logging into the library system
               before you can search or add books

    Returns:
        Open Weaviate client connection
        IMPORTANT: Always close with client.close()
                   or use as context manager
    """
    host      = os.getenv("WEAVIATE_HOST")
    http_port = int(os.getenv("WEAVIATE_PORT", 8080))
    grpc_port = int(os.getenv("WEAVIATE_GRPC_PORT", 50051))

    return weaviate.connect_to_custom(
        http_host=host,
        http_port=http_port,
        http_secure=False,
        grpc_host=host,
        grpc_port=grpc_port,
        grpc_secure=False,
    )


def ensure_collection(client: weaviate.WeaviateClient) -> None:
    """
    WHAT:  Creates the DocuMindChunk collection if it
           doesn't already exist
    WHY:   Like creating a table in a database —
           must exist before we can store anything

    Real life: Like setting up filing cabinet drawers
               before you can file any documents

    Collection schema:
        text       → the chunk content
        chunk_type → "text", "table", or "image_caption"
        page       → page number in source document
        source     → filename (e.g. "report.pdf")
        metadata   → extra info as JSON string
    """
    if client.collections.exists(COLLECTION_NAME):
        print(f"[Weaviate] Collection '{COLLECTION_NAME}' exists ✅")
        return

    print(f"[Weaviate] Creating collection '{COLLECTION_NAME}'...")

    client.collections.create(
        name=COLLECTION_NAME,

        # BYOV = Bring Your Own Vector
        # We generate embeddings ourselves (not Weaviate's built-in)
        vectorizer_config=Configure.Vectorizer.none(),

        # HNSW = Hierarchical Navigable Small World
        # Fast approximate nearest neighbour search algorithm
        # Real life: Like a smart index that groups
        #            similar items together for fast search
        vector_index_config=Configure.VectorIndex.hnsw(),

        properties=[
            Property(name="text",       data_type=DataType.TEXT),
            Property(name="chunk_type", data_type=DataType.TEXT),
            Property(name="page",       data_type=DataType.INT),
            Property(name="source",     data_type=DataType.TEXT),
            Property(name="metadata",   data_type=DataType.TEXT),
        ],
    )

    print(f"[Weaviate] ✅ Collection created")


def store_chunks(
    client:  weaviate.WeaviateClient,
    chunks:  list[dict],
    vectors: list[list[float]],
) -> int:
    """
    WHAT:  Stores chunks + their vectors in Weaviate
    WHY:   Persists the document so it can be searched later

    Real life: Like filing index cards in the cabinet
               Each card has:
               → The content (chunk text)
               → GPS coordinates (vector) for finding it

    Args:
        client:  Open Weaviate connection
        chunks:  List of chunk dicts from parser.py
        vectors: List of vectors from embedder.py
                 Must be same length as chunks

    Returns:
        Number of chunks successfully stored
    """
    collection = client.collections.get(COLLECTION_NAME)
    objects    = []

    # Build list of objects to insert
    for chunk, vector in zip(chunks, vectors):
        objects.append(
            wvc.data.DataObject(
                properties={
                    "text":       chunk["text"],
                    "chunk_type": chunk["type"],
                    "page":       chunk["page"],
                    "source":     chunk["source"],
                    "metadata":   json.dumps(chunk.get("metadata", {})),
                },
                vector=vector,   # the embedding we generated
            )
        )

    # insert_many = batch insert (much faster than one by one)
    # Real life: Like filing 100 cards at once instead
    #            of one card at a time
    print(f"[Weaviate] Storing {len(objects)} chunks...")
    result = collection.data.insert_many(objects)

    # Count successes and failures
    inserted = len(objects) - len(result.errors)

    if result.errors:
        print(f"[Weaviate] ⚠️  {len(result.errors)} errors:")
        for err in list(result.errors.values())[:3]:
            print(f"           {err}")
    else:
        print(f"[Weaviate] ✅ Stored {inserted}/{len(objects)} chunks")

    return inserted


def dense_search(
    client:     weaviate.WeaviateClient,
    vector:     list[float],
    top_k:      int = 20,
    source_filter: str | None = None,
) -> list[dict]:
    """
    WHAT:  Finds chunks most similar to a query vector
    WHY:   Core of the RAG system — retrieves relevant context

    Real life: Like asking the librarian:
               "Find me the 20 index cards most similar
                to this question's GPS coordinates"

    Args:
        client:        Open Weaviate connection
        vector:        Query embedding from embed_query()
        top_k:         How many results to return (default 20)
        source_filter: Only search within this document
                       (None = search all documents)

    Returns:
        List of chunk dicts with added "score" field
        Sorted by similarity (most similar first)
    """
    collection = client.collections.get(COLLECTION_NAME)

    # Build filters if we want to search within one document only
    filters = None
    if source_filter:
        filters = wvc.query.Filter.by_property("source").equal(source_filter)

    # near_vector = find chunks whose vector is closest to ours
    response = collection.query.near_vector(
        near_vector=vector,
        limit=top_k,
        filters=filters,
        return_metadata=wvc.query.MetadataQuery(distance=True),
    )

    # Convert Weaviate response to our standard chunk format
    results = []
    for obj in response.objects:
        results.append({
            "text":      obj.properties["text"],
            "type":      obj.properties["chunk_type"],
            "page":      obj.properties["page"],
            "source":    obj.properties["source"],
            # Convert distance to similarity score
            # distance=0 means identical, distance=2 means opposite
            # score=1 means identical, score=0 means opposite
            "score":     round(1 - (obj.metadata.distance or 0), 4),
            "retrieval": "dense",
        })

    return results


def get_all_chunks(
    client: weaviate.WeaviateClient,
    source: str | None = None,
) -> list[dict]:
    """
    WHAT:  Retrieves all stored chunks (for BM25 search)
    WHY:   BM25 needs the full corpus to build its index

    Real life: Like getting all index cards from the cabinet
               so we can do keyword search across all of them

    Args:
        client: Open Weaviate connection
        source: Filter by document name (None = all)

    Returns:
        List of all chunk dicts
    """
    collection = client.collections.get(COLLECTION_NAME)

    filters = None
    if source:
        filters = wvc.query.Filter.by_property("source").equal(source)

    # fetch_objects = get all objects without vector search
    response = collection.query.fetch_objects(
        filters=filters,
        limit=10000,    # max chunks we expect — adjust if needed
    )

    return [
        {
            "text":   obj.properties["text"],
            "type":   obj.properties["chunk_type"],
            "page":   obj.properties["page"],
            "source": obj.properties["source"],
        }
        for obj in response.objects
    ]


def delete_document_chunks(
    client: weaviate.WeaviateClient,
    source: str,
) -> int:
    """
    WHAT:  Deletes all chunks from a specific document
    WHY:   When user deletes a document, clean up Weaviate too

    Real life: Like removing all index cards from
               a specific book when the book is deleted

    Args:
        client: Open Weaviate connection
        source: Filename to delete (e.g. "report.pdf")

    Returns:
        Number of chunks deleted
    """
    collection = client.collections.get(COLLECTION_NAME)

    result = collection.data.delete_many(
        where=wvc.query.Filter.by_property("source").equal(source)
    )

    deleted = result.successful
    print(f"[Weaviate] ✅ Deleted {deleted} chunks for '{source}'")
    return deleted
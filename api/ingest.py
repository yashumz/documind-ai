# api/ingest.py
# ─────────────────────────────────────────────────────────────
# POST /ingest endpoint
#
# Accepts a PDF file upload and runs the full pipeline:
#   1. Save to S3 (original file safe)
#   2. Parse with Unstructured.io (text+tables+images)
#   3. Embed with sentence-transformers (vectors)
#   4. Store in Weaviate (searchable)
#
# Returns a summary of what was ingested.
# ─────────────────────────────────────────────────────────────

import os
import shutil
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel

from ingestion.s3_handler     import upload_pdf
from ingestion.parser         import parse_document
from ingestion.embedder       import embed_chunks
from ingestion.weaviate_store import get_client, ensure_collection, store_chunks

router    = APIRouter()

# Temporary folder for uploaded files
# Files are deleted after processing — originals are in S3
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


# ── Response model ────────────────────────────────────────────
class IngestResponse(BaseModel):
    """
    WHAT:  Defines the shape of the API response
    WHY:   FastAPI auto-generates documentation from this
           Also validates our response before sending it

    Real life: Like a standard receipt format —
               every ingest returns the same fields
    """
    filename:     str
    s3_key:       str
    total_chunks: int
    text_chunks:  int
    table_chunks: int
    image_chunks: int
    message:      str


@router.post("/ingest", response_model=IngestResponse)
async def ingest_document(file: UploadFile = File(...)):
    """
    WHAT:  Accepts a PDF and runs the full ingestion pipeline
    WHY:   This is the entry point for all documents
           Users call this endpoint to add documents
           to the DocuMind AI knowledge base

    Args:
        file: The uploaded PDF file
              FastAPI handles the multipart form data

    Returns:
        IngestResponse with chunk counts and S3 location

    Raises:
        HTTPException 400: If file is not a PDF
        HTTPException 500: If any pipeline step fails
    """

    # ── Validate file type ────────────────────────────────────
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail=f"Only PDF files accepted. Got: {file.filename}"
        )

    print(f"\n[Ingest] Starting pipeline for: {file.filename}")

    # ── Save uploaded file temporarily ────────────────────────
    # We need it on disk for Unstructured.io to process
    temp_path = UPLOAD_DIR / file.filename
    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        print(f"[Ingest] Saved temp file: {temp_path}")

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save uploaded file: {e}"
        )

    try:
        # ── Step 1: Upload to S3 ──────────────────────────────
        print(f"[Ingest] Step 1/4: Uploading to S3...")
        s3_info = upload_pdf(
            file_path=str(temp_path),
            original_filename=file.filename,
        )
        print(f"[Ingest] ✅ S3: {s3_info['s3_key']}")

        # ── Step 2: Parse PDF ─────────────────────────────────
        print(f"[Ingest] Step 2/4: Parsing PDF...")
        chunks = parse_document(str(temp_path))

        if not chunks:
            raise HTTPException(
                status_code=500,
                detail="No content extracted from PDF"
            )

        # Count chunk types for response
        text_chunks  = sum(1 for c in chunks if c["type"] == "text")
        table_chunks = sum(1 for c in chunks if c["type"] == "table")
        image_chunks = sum(1 for c in chunks if c["type"] == "image_caption")

        print(f"[Ingest] ✅ Parsed: {len(chunks)} chunks "
              f"({text_chunks} text, {table_chunks} tables, "
              f"{image_chunks} images)")

        # ── Step 3: Embed chunks ──────────────────────────────
        print(f"[Ingest] Step 3/4: Embedding chunks...")
        vectors = embed_chunks(chunks)
        print(f"[Ingest] ✅ Embedded: {len(vectors)} vectors")

        # ── Step 4: Store in Weaviate ─────────────────────────
        print(f"[Ingest] Step 4/4: Storing in Weaviate...")
        weaviate_client = get_client()
        try:
            ensure_collection(weaviate_client)
            inserted = store_chunks(weaviate_client, chunks, vectors)
        finally:
            weaviate_client.close()

        print(f"[Ingest] ✅ Stored: {inserted} chunks in Weaviate")
        print(f"[Ingest] 🎉 Pipeline complete for: {file.filename}")

        return IngestResponse(
            filename=file.filename,
            s3_key=s3_info["s3_key"],
            total_chunks=len(chunks),
            text_chunks=text_chunks,
            table_chunks=table_chunks,
            image_chunks=image_chunks,
            message=f"Successfully ingested {file.filename} — "
                    f"{len(chunks)} chunks ready for querying",
        )

    except HTTPException:
        raise   # re-raise HTTP exceptions as-is

    except Exception as e:
        print(f"[Ingest] ❌ Pipeline failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Ingestion pipeline failed: {str(e)}"
        )

    finally:
        # Always delete temp file — originals are safe in S3
        if temp_path.exists():
            temp_path.unlink()
            print(f"[Ingest] Cleaned up temp file")
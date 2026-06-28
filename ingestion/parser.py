# ingestion/parser.py
# ─────────────────────────────────────────────────────────────
# Parses PDF files into typed chunks using Unstructured.io
#
# Output: list of dicts, each dict is one chunk:
# {
#   "text":     "the actual content",
#   "type":     "text" | "table" | "image_caption",
#   "page":     3,
#   "source":   "annual_report.pdf",
#   "metadata": {...}
# }
# ─────────────────────────────────────────────────────────────

import os
import base64
from pathlib import Path
import anthropic
from dotenv import load_dotenv

load_dotenv()

# ── Tell Unstructured exactly where Tesseract is on Windows ──
# This is needed because Windows PATH changes don't always
# propagate into Python subprocess calls without a restart
import unstructured_pytesseract
unstructured_pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)

# Claude client for image captioning
_claude = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))



def _caption_image(image_base64: str) -> str:
    """
    Sends an image to Claude Vision and gets a text description.

    Real life: Like having someone describe a photo in words
               "The chart shows revenue increasing from $12M to $22M"
    """
    try:
        response = _claude.messages.create(
            model="claude-haiku-4-5",
            max_tokens=200,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type":       "base64",
                            "media_type": "image/png",
                            "data":       image_base64,
                        },
                    },
                    {
                        "type": "text",
                        "text": (
                            "Describe this image in 2-3 sentences. "
                            "Focus on data, numbers, labels, and key "
                            "information visible. Be specific and concise."
                        ),
                    },
                ],
            }],
        )
        return response.content[0].text

    except Exception as e:
        print(f"[Parser] ⚠️  Image captioning failed: {e}")
        return "Image content could not be extracted."


def parse_document(file_path: str) -> list[dict]:
    """
    Main function — parses a PDF into typed chunks.

    Real life: Like a librarian breaking a book into
               index cards — one card per topic/section

    Args:
        file_path: Full path to the PDF file

    Returns:
        List of chunk dicts ready for embedding + storage
    """
    from unstructured.partition.pdf import partition_pdf
    from unstructured.documents.elements import (
        NarrativeText,
        Title,
        Table,
        Image,
        ListItem,
        Header,
        Footer,
    )

    path   = Path(file_path)
    chunks = []

    print(f"[Parser] 📄 Parsing: {path.name}")
    print(f"[Parser] Strategy: hi_res (tables + images enabled)")

    elements = partition_pdf(
        filename=str(path),
        strategy="hi_res",
        infer_table_structure=True,
        extract_images_in_pdf=True,
    )

    print(f"[Parser] Found {len(elements)} raw elements — processing...")

    for el in elements:
        page = getattr(el.metadata, "page_number", 1) or 1

        # ── TEXT CHUNKS ───────────────────────────────────────
        if isinstance(el, (NarrativeText, Title, ListItem)):
            text = el.text.strip()

            if len(text) < 30:
                continue

            chunks.append({
                "text":     text,
                "type":     "text",
                "page":     page,
                "source":   path.name,
                "metadata": {
                    "element_id":   str(el.id),
                    "element_type": type(el).__name__,
                },
            })

        # ── TABLE CHUNKS ──────────────────────────────────────
        elif isinstance(el, Table):
            html_text = getattr(el.metadata, "text_as_html", None)
            content   = html_text if html_text else el.text

            if not content or len(content.strip()) < 10:
                continue

            chunks.append({
                "text":     content,
                "type":     "table",
                "page":     page,
                "source":   path.name,
                "metadata": {
                    "element_id": str(el.id),
                    "raw_text":   el.text[:200],
                },
            })

        # ── IMAGE CHUNKS ──────────────────────────────────────
        elif isinstance(el, Image):
            img_b64 = getattr(el.metadata, "image_base64", None)

            if img_b64:
                print(f"[Parser] 🖼️  Captioning image on page {page}...")
                caption = _caption_image(img_b64)

                chunks.append({
                    "text":     f"[Image on page {page}]: {caption}",
                    "type":     "image_caption",
                    "page":     page,
                    "source":   path.name,
                    "metadata": {
                        "element_id": str(el.id),
                    },
                })

        # Skip Headers/Footers
        elif isinstance(el, (Header, Footer)):
            continue

    # Summary
    text_count  = sum(1 for c in chunks if c["type"] == "text")
    table_count = sum(1 for c in chunks if c["type"] == "table")
    image_count = sum(1 for c in chunks if c["type"] == "image_caption")

    print(f"[Parser] ✅ Done — {len(chunks)} chunks extracted:")
    print(f"         📝 Text:   {text_count}")
    print(f"         📊 Tables: {table_count}")
    print(f"         🖼️  Images: {image_count}")

    return chunks
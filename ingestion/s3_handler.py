# ingestion/s3_handler.py
# ─────────────────────────────────────────────────────────────
# Handles all S3 operations:
#   → Upload PDF files when user submits them
#   → Generate a unique storage path for each file
#   → Retrieve file info when needed
# ─────────────────────────────────────────────────────────────

import os
import uuid
import boto3
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()


def get_s3_client():
    """
    WHAT:  Creates a connection to AWS S3
    WHY:   We need this connection before we can
           upload or download anything

    Real life: Like logging into internet banking
               before you can do any transactions
    """
    return boto3.client(
        "s3",
        region_name=os.getenv("AWS_REGION"),
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    )


def upload_pdf(file_path: str, original_filename: str) -> dict:
    """
    WHAT:  Uploads a PDF file to S3
    WHY:   We store originals in S3 so:
           → Files are safe even if EC2 restarts
           → We can reprocess files if pipeline changes
           → Users can download originals later

    Args:
        file_path:         Path to the PDF on local disk
                           e.g. "C:/temp/report.pdf"
        original_filename: The original name user gave the file
                           e.g. "Q3_Annual_Report.pdf"

    Returns:
        {
            "s3_key":    "uploads/2026/06/26/abc123_Q3_Annual_Report.pdf",
            "bucket":    "documind-ai-uploads-yash",
            "filename":  "Q3_Annual_Report.pdf",
            "size_bytes": 245760,
            "uploaded_at": "2026-06-26T10:30:00"
        }

    Real life: Like getting a receipt after depositing
               a document at the bank — confirms it's safe
    """
    s3     = get_s3_client()
    bucket = os.getenv("S3_BUCKET_NAME")

    # Generate unique S3 path to avoid name collisions
    # e.g. two users both upload "report.pdf" → no conflict
    # Path format: uploads/YYYY/MM/DD/uuid_filename.pdf
    date_prefix = datetime.now().strftime("%Y/%m/%d")
    unique_id   = str(uuid.uuid4())[:8]   # first 8 chars of UUID
    s3_key      = f"uploads/{date_prefix}/{unique_id}_{original_filename}"

    # Get file size before uploading
    file_size = os.path.getsize(file_path)

    print(f"[S3] Uploading '{original_filename}' to s3://{bucket}/{s3_key}")

    # Upload the file
    # ExtraArgs sets the content type so browsers know it's a PDF
    s3.upload_file(
        Filename=file_path,         # local file to upload
        Bucket=bucket,              # our S3 bucket
        Key=s3_key,                 # path inside the bucket
        ExtraArgs={"ContentType": "application/pdf"},
    )

    print(f"[S3] ✅ Upload complete — {file_size:,} bytes")

    return {
        "s3_key":      s3_key,
        "bucket":      bucket,
        "filename":    original_filename,
        "size_bytes":  file_size,
        "uploaded_at": datetime.now().isoformat(),
    }


def get_s3_url(s3_key: str) -> str:
    """
    WHAT:  Generates a temporary download URL for a file
    WHY:   S3 files are private (no public access)
           We generate a time-limited URL when needed

    Real life: Like a one-time access code to a locker
               Valid for 1 hour, then expires automatically

    Args:
        s3_key: The path of the file in S3
                e.g. "uploads/2026/06/26/abc123_report.pdf"

    Returns:
        A URL string valid for 1 hour
    """
    s3     = get_s3_client()
    bucket = os.getenv("S3_BUCKET_NAME")

    # generate_presigned_url creates a temporary URL
    # ExpiresIn=3600 means URL expires after 3600 seconds (1 hour)
    url = s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": bucket, "Key": s3_key},
        ExpiresIn=3600,
    )

    return url


def delete_s3_file(s3_key: str) -> bool:
    """
    WHAT:  Deletes a file from S3
    WHY:   When user deletes a document, we clean up S3 too
           Prevents storage costs from accumulating

    Args:
        s3_key: The path of the file to delete

    Returns:
        True if deleted successfully, False if failed
    """
    try:
        s3     = get_s3_client()
        bucket = os.getenv("S3_BUCKET_NAME")

        s3.delete_object(Bucket=bucket, Key=s3_key)
        print(f"[S3] ✅ Deleted: {s3_key}")
        return True

    except Exception as e:
        print(f"[S3] ❌ Delete failed: {e}")
        return False
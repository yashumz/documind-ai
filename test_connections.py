# test_connections.py
# ─────────────────────────────────────────────────────────────
# Verifies all 4 external services are reachable and configured
# correctly before we start building the actual pipeline.
#
# Run with:  uv run python test_connections.py
# ─────────────────────────────────────────────────────────────

import os
from dotenv import load_dotenv

# Load all values from .env file into environment
load_dotenv()


# ── TEST 1: Weaviate ──────────────────────────────────────────
def test_weaviate():
    """
    WHAT:   Connect to Weaviate running on our EC2 instance
    WHY:    If this fails, we can't store or search document chunks
    """
    print("\n[1/4] Testing Weaviate on EC2...")

    try:
        import weaviate

        host      = os.getenv("WEAVIATE_HOST")
        http_port = int(os.getenv("WEAVIATE_PORT", 8080))
        grpc_port = int(os.getenv("WEAVIATE_GRPC_PORT", 50051))

        # Connect to our self-hosted Weaviate on EC2
        # connect_to_custom = for self-hosted instances (not Weaviate Cloud)
        client = weaviate.connect_to_custom(
            http_host=host,
            http_port=http_port,
            http_secure=False,      # no HTTPS yet (portfolio project)
            grpc_host=host,
            grpc_port=grpc_port,
            grpc_secure=False,
        )

        # is_ready() sends a health check ping to Weaviate
        ready   = client.is_ready()
        meta    = client.get_meta()
        version = meta.get("version", "unknown")

        print(f"  ✅ Weaviate ready: {ready}")
        print(f"  ✅ Version: {version}")
        print(f"  ✅ Host: {host}:{http_port}")

        client.close()  # always close connection when done

    except Exception as e:
        print(f"  ❌ Weaviate failed: {e}")
        print(f"  💡 Check: Is EC2 running? Is port 8080 open in security group?")


# ── TEST 2: AWS S3 ────────────────────────────────────────────
def test_s3():
    """
    WHAT:   Connect to S3 and verify our bucket exists
    WHY:    If this fails, we can't store uploaded PDF files
    """
    print("\n[2/4] Testing AWS S3...")

    try:
        import boto3

        # Create S3 client using our IAM credentials from .env
        s3 = boto3.client(
            "s3",
            region_name=os.getenv("AWS_REGION"),
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        )

        bucket = os.getenv("S3_BUCKET_NAME")

        # List objects in bucket — empty bucket returns [] which is fine
        # This also confirms our IAM credentials are valid
        response = s3.list_objects_v2(Bucket=bucket, MaxKeys=1)
        count    = response.get("KeyCount", 0)

        print(f"  ✅ S3 bucket accessible: {bucket}")
        print(f"  ✅ Region: {os.getenv('AWS_REGION')}")
        print(f"  ✅ Objects in bucket: {count} (0 is correct — bucket is empty)")

    except Exception as e:
        print(f"  ❌ S3 failed: {e}")
        print(f"  💡 Check: Are AWS credentials correct in .env?")


# ── TEST 3: Anthropic (Claude) ────────────────────────────────
def test_anthropic():
    """
    WHAT:   Send a tiny test message to Claude and get a response
    WHY:    If this fails, the AI generation part won't work
    """
    print("\n[3/4] Testing Anthropic (Claude)...")

    try:
        import anthropic

        client = anthropic.Anthropic(
            api_key=os.getenv("ANTHROPIC_API_KEY")
        )

        # Use claude-haiku — cheapest model for our test
        # This costs less than $0.001 (less than 0.1 paisa)
        response = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=10,
            messages=[{
                "role": "user",
                "content": "Reply with just the word: CONNECTED"
            }],
        )

        reply        = response.content[0].text
        input_tokens = response.usage.input_tokens
        output_tokens= response.usage.output_tokens

        print(f"  ✅ Claude responded: '{reply}'")
        print(f"  ✅ Tokens used: {input_tokens} in / {output_tokens} out")
        print(f"  ✅ Model: claude-haiku-4-5")

    except Exception as e:
        print(f"  ❌ Anthropic failed: {e}")
        print(f"  💡 Check: Is ANTHROPIC_API_KEY set correctly in .env?")
        print(f"  💡 Check: Do you have API credits at console.anthropic.com?")


# ── TEST 4: Langfuse ──────────────────────────────────────────
def test_langfuse():
    """
    WHAT:   Authenticate with Langfuse Cloud
    WHY:    If this fails, we lose observability (tracing won't work)
    """
    print("\n[4/4] Testing Langfuse...")

    try:
        from langfuse import get_client

        # get_client() reads LANGFUSE_PUBLIC_KEY, SECRET_KEY, BASE_URL from env
        langfuse = get_client()

        # auth_check() pings Langfuse Cloud with our keys
        ok = langfuse.auth_check()

        if ok:
            print(f"  ✅ Langfuse authenticated successfully")
            print(f"  ✅ Base URL: {os.getenv('LANGFUSE_BASE_URL')}")
            print(f"  ✅ Project: documind-ai")
        else:
            print(f"  ❌ Langfuse auth failed — keys may be wrong")

        # flush() sends any pending data before script exits
        langfuse.flush()

    except Exception as e:
        print(f"  ❌ Langfuse failed: {e}")
        print(f"  💡 Check: Are LANGFUSE keys set correctly in .env?")


# ── MAIN ──────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 55)
    print("  DocuMind AI — Connection Tests")
    print("=" * 55)

    test_weaviate()
    test_s3()
    test_anthropic()
    test_langfuse()

    print("\n" + "=" * 55)
    print("  Done! Fix any ❌ before proceeding to Phase 2.")
    print("=" * 55)
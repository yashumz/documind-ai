# observability/langfuse_setup.py
# ─────────────────────────────────────────────────────────────
# Initialises Langfuse and auto-instruments Anthropic SDK.
# Import this ONCE at app startup (in main.py).
# ─────────────────────────────────────────────────────────────

import os
from dotenv import load_dotenv

load_dotenv()


def setup_langfuse():
    """
    WHAT:  Initialises Langfuse observability
    WHY:   Must be called before any LLM calls

    Real life: Like switching on the CCTV system
               before the shop opens
    """
    try:
        from langfuse import get_client
        from opentelemetry.instrumentation.anthropic import AnthropicInstrumentor

        # Auto-patch Anthropic SDK globally
        # Every client.messages.create() is now traced
        AnthropicInstrumentor().instrument()

        # Verify connection to Langfuse Cloud
        langfuse = get_client()
        ok = langfuse.auth_check()

        if ok:
            print("✅ Langfuse connected — tracing active")
        else:
            print("⚠️  Langfuse auth failed — check .env keys")

        return langfuse

    except Exception as e:
        # Observability must NEVER crash the app
        print(f"⚠️  Langfuse setup failed: {e}")
        print("   App will run without observability")
        return None


def flush_langfuse():
    """
    WHAT:  Flushes pending traces to Langfuse Cloud
    WHY:   Langfuse batches traces — flush at shutdown
           to avoid losing the last few traces

    Real life: Like sending all unsent mail before
               closing the post office for the day
    """
    try:
        from langfuse import get_client
        langfuse = get_client()
        langfuse.flush()
        print("[Langfuse] ✅ Traces flushed")
    except Exception as e:
        print(f"[Langfuse] ⚠️  Flush failed: {e}")
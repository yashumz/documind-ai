# observability/middleware.py
# ─────────────────────────────────────────────────────────────
# FastAPI middleware that wraps every HTTP request
# in a Langfuse trace.
# ─────────────────────────────────────────────────────────────

import time
import os
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request

APP_NAME = os.getenv("APP_NAME", "documind-ai")

# Paths that don't need tracing
SKIP_PATHS = {
    "/health",
    "/docs",
    "/openapi.json",
    "/favicon.ico",
    "/redoc",
}


class LangfuseTracingMiddleware(BaseHTTPMiddleware):
    """
    WHAT:  Wraps every HTTP request in a Langfuse trace
    WHY:   End-to-end visibility for every API call

    Real life: Like a receptionist who logs every visitor:
               arrival time, purpose, departure, outcome
    """

    async def dispatch(self, request: Request, call_next):

        # Skip non-business endpoints
        if request.url.path in SKIP_PATHS:
            return await call_next(request)

        start_time = time.time()

        try:
            from langfuse import get_client
            langfuse = get_client()

            with langfuse.start_as_current_observation(
                as_type="span",
                name=f"{APP_NAME}:{request.method}:{request.url.path}",
            ) as span:

                span.update(input={
                    "method": request.method,
                    "path":   request.url.path,
                    "query":  str(request.query_params),
                    "app":    APP_NAME,
                })

                response   = await call_next(request)
                latency_ms = round((time.time() - start_time) * 1000, 2)

                span.update(output={
                    "status_code": response.status_code,
                    "latency_ms":  latency_ms,
                })

                return response

        except Exception:
            # Tracing failure must never break the request
            return await call_next(request)
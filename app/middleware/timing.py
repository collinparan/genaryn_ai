"""
Request timing middleware for performance monitoring
"""

import time
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class TimingMiddleware(BaseHTTPMiddleware):
    """Add request timing information to response headers."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and add timing information."""
        start_time = time.time()

        response = await call_next(request)

        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = f"{process_time:.3f}"

        return response
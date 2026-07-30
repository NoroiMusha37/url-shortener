import uuid6
import structlog
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

class StructlogContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid6.uuid7())

        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            log_id=request_id,
            method=request.method,
            path=request.url.path,
        )

        response = await call_next(request)

        response.headers["X-Request-ID"] = request_id
        
        return response

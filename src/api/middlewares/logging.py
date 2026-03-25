from __future__ import annotations

import time
from collections.abc import Awaitable, Callable

from fastapi import Request
from jose import JWTError, jwt
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from src.core.config.settings import settings
from src.data.clients.database import AsyncSessionLocal
from src.data.models.log_model import Logs, Methods
from src.data.repositories.base_repository import insert_data
from src.observability.logging.logging_config import logger


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        if request.method == "OPTIONS":
            return await call_next(request)

        public_urls = [
            "/",
            "/docs",
            "/openapi.json",
            "/health",
            "/auth/users/login",
            "/auth/users/create",
        ]
        if request.url.path in public_urls:
            return await call_next(request)

        # Extract user_id from token if available
        user_id: int | None = None
        token = None
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
        else:
            token = request.cookies.get("access_token")

        if token:
            try:
                payload = jwt.decode(
                    token, settings.access_secret_key, algorithms=[settings.algorithm]
                )
                user_id = payload.get("user_id")
            except JWTError:
                user_id = None

        # Measure request duration
        start = time.time()
        response = await call_next(request)
        duration = time.time() - start

        # Only log POST, PUT, DELETE
        if request.method in ["POST", "PUT", "DELETE"]:
            try:
                async with AsyncSessionLocal() as db:
                    await insert_data(
                        Logs,
                        db,
                        user_id=user_id,
                        method=Methods(request.method),
                        url=str(request.url),
                        status_code=response.status_code,
                        time_taken=duration,
                    )
            except Exception as e:
                logger.info(f"Logging failed: {e}")

        return response

"""Module: logging.py"""

import time
from collections.abc import Awaitable, Callable

from fastapi import Request
from jose import JWTError, jwt
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from src.config.settings import settings
from src.data.clients.database import AsyncSessionLocal
from src.data.models.log_model import Logs, Methods
from src.data.repositories.base_repository import insert_data
from src.observability.logging.logging_config import logger


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log incoming requests and their outcomes.
    This middleware captures the user ID from the JWT token (if available),
    the HTTP method, the requested URL, the response status code, and the time taken to process the request. It logs this information for all POST, PUT, and DELETE requests to help with monitoring and debugging. If logging fails for any reason, it catches the exception and logs an error message without affecting the response sent to the client."""

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Authenticate incoming requests using JWT tokens.
        This method checks for a JWT token in the Authorization header or cookies, validates it, and attaches the user information to the request state. If authentication fails, it returns a 401 response.        Additionally, it logs the user ID (if available), HTTP method, URL, response status code, and time taken for POST, PUT, and DELETE requests."""
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

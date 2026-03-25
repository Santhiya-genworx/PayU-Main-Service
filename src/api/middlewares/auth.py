from __future__ import annotations

from collections.abc import Awaitable, Callable

from fastapi import Request
from fastapi.responses import Response
from jose import JWTError, jwt
from starlette.middleware.base import BaseHTTPMiddleware

from src.core.config.settings import settings
from src.core.exceptions.exceptions import UnauthorizedException


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        if request.method == "OPTIONS":
            return await call_next(request)

        public_urls = [
            "/",
            "/docs",
            "/openapi.json",
            "/auth/users/login",
            "/auth/users/create",
            "/health",
        ]

        if request.url.path in public_urls:
            return await call_next(request)

        token = request.cookies.get("access_token")
        if not token:
            raise UnauthorizedException(detail="Authorization token missing")

        try:
            payload = jwt.decode(token, settings.access_secret_key, algorithms=[settings.algorithm])
            request.state.user = payload
        except JWTError as err:
            raise UnauthorizedException(detail="Invalid or expired token") from err

        # call_next is now correctly typed as returning Awaitable[Response]
        response = await call_next(request)
        return response

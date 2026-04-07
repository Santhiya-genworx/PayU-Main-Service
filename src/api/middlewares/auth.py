"""Module: auth.py"""

from collections.abc import Awaitable, Callable

from fastapi import Request
from fastapi.responses import Response
from jose import JWTError, jwt
from PayU_Main_Service.src.config.settings import settings
from starlette.middleware.base import BaseHTTPMiddleware

from src.core.exceptions.exceptions import UnauthorizedException


class AuthMiddleware(BaseHTTPMiddleware):
    """Middleware to authenticate requests using JWT tokens.
    This middleware checks for a JWT token in the Authorization header or cookies, validates it, and attaches the user information to the request state. If authentication fails, it returns a 401 response."""

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Authenticate incoming requests using JWT tokens.
        This method checks for a JWT token in the Authorization header or cookies, validates it, and attaches the user information to the request state. If authentication fails, it returns a 401 response."""
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

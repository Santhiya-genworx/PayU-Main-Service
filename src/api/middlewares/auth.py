from fastapi import HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware
from jose import JWTError, jwt
from src.core.config.settings import settings

class AuthMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next):

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
        print("middlware ",request.url)
        if request.url.path in public_urls:
            return await call_next(request)

        token = request.cookies.get("access_token")

        if not token:
            raise HTTPException(status_code=401, detail="Authorization token missing")

        try:
            payload = jwt.decode(
                token,
                settings.access_secret_key,
                algorithms=[settings.algorithm]
            )
            request.state.user = payload
        except JWTError:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        
        response = await call_next(request)
        return response
import time
from fastapi import HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware
from src.data.models.log_model import Logs, Methods
from src.data.repositories.base_repository import commit_transaction, insert_data
from src.api.rest.dependencies import AsyncSessionLocal
from jose import JWTError, jwt
from src.core.config.settings import settings

class LoggingMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next):
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
        
        token = None
        auth_header = request.headers.get("Authorization")
        if auth_header:
            token = auth_header.split(" ")[1]
        else:
            token = request.cookies.get("access_token")
            if not token:
                raise HTTPException(status_code=401, detail="Authorization token missing")

        user_id = None
        if token:
            try:
                payload = jwt.decode(token, settings.access_secret_key, algorithms=[settings.algorithm])
                user_id = payload["user_id"]
            except JWTError:
                user_id = None
        
        start = time.time()
        response = await call_next(request)
        duration = time.time() - start

        if request.method in ["POST", "PUT", "DELETE"]:
            try:
                async with AsyncSessionLocal() as db:
                    data = {
                        "user_id": user_id,
                        "method": Methods(request.method),
                        "url": str(request.url),
                        "status_code": response.status_code,
                        "time_taken": duration
                    }
                    await insert_data(Logs, db, **data)
                    await commit_transaction(db)
            except Exception as e:
                print(f"Logging failed: {str(e)}")
        return response
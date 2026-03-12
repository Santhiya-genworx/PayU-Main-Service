from fastapi import APIRouter, Request, Response
from src.core.config.settings import settings
import httpx

process_router = APIRouter()

url = settings.process_service_url

@process_router.api_route("/process/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def process_proxy(path: str, request: Request):
    query = request.url.query

    target_url = f"{url}/{path}"
    if query:
        target_url = f"{target_url}?{query}"

    async with httpx.AsyncClient(timeout=60.0) as client:
        # Forward the request to process Service
        response = await client.request(
            method=request.method,
            url=target_url,
            headers=request.headers,
            content=await request.body()
        )

    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )
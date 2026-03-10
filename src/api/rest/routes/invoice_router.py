from fastapi import APIRouter, Request, Response
from src.core.config.settings import settings
import httpx

invoice_router = APIRouter()

url = settings.invoice_service_url

@invoice_router.api_route("/process/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def invoice_proxy(path: str, request: Request):
    async with httpx.AsyncClient(timeout=60.0) as client:
        # Forward the request to Invoice Service
        response = await client.request(
            method=request.method,
            url=f"{url}/{path}",
            headers=request.headers,
            content=await request.body()
        )

    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )
"""Module: process_router.py"""

import httpx
from fastapi import APIRouter, Request, Response

from src.config.settings import settings

process_router = APIRouter()

url = settings.process_service_url


@process_router.api_route("/process/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def process_proxy(path: str, request: Request) -> Response:
    """Proxy endpoint to forward requests to the PayU Processing Service API.
    This endpoint captures all requests to the /process/{path} route and forwards them to the Processing Service API. It handles various HTTP methods and ensures that the request body, headers, and query parameters are correctly forwarded to the target API. The response from the Processing Service API is then returned to the client, preserving the status code and relevant headers. This allows for seamless integration between the Main Service and the Processing Service, enabling the Main Service to act as a gateway for processing-related operations without exposing the Processing Service API directly to clients.
    Args:
        path (str): The path to forward the request to, extracted from the URL.
        request (Request): The incoming HTTP request from the client.
    Returns:
        Response: The HTTP response received from the Processing Service API, which is forwarded back to the client.
    """

    query = request.url.query

    target_url = f"{url}/{path.rstrip('/')}"
    if query:
        target_url = f"{target_url}?{query}"

    content_type = request.headers.get("content-type", "")

    headers = {
        k: v for k, v in request.headers.items() if k.lower() not in ["host", "content-length"]
    }

    async with httpx.AsyncClient(timeout=None) as client:
        if "multipart/form-data" in content_type:
            body = await request.body()

            response = await client.request(
                method=request.method, url=target_url, headers=headers, content=body
            )

        else:
            json_body = None
            if request.method in ["POST", "PUT", "PATCH"]:
                try:
                    json_body = await request.json()
                except Exception:
                    json_body = None

            response = await client.request(
                method=request.method, url=target_url, headers=headers, json=json_body
            )

    proxy_response = Response(
        content=response.content,
        status_code=response.status_code,
    )

    for key, value in response.headers.items():
        if key.lower() not in (
            "content-length",
            "transfer-encoding",
            "content-encoding",
        ):
            proxy_response.headers[key] = value

    return proxy_response

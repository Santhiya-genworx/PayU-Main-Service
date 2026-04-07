"""Module: auth_router.py"""

import httpx
from fastapi import APIRouter, Request, Response

from src.config.settings import settings

auth_router = APIRouter()

url = settings.auth_service_url


@auth_router.api_route("/auth/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def auth_proxy(path: str, request: Request) -> Response:
    """Proxy endpoint to forward requests to the PayU Authentication Service API.
    This endpoint captures all requests to the /auth/{path} route and forwards them to the Authentication Service API. It handles various HTTP methods and ensures that the request body, headers, and query parameters are correctly forwarded to the target API. The response from the Authentication Service API is then returned to the client, preserving the status code and relevant headers. This allows for seamless integration between the Main Service and the Authentication Service, enabling the Main Service to act as a gateway for authentication-related operations without exposing the Authentication Service API directly to clients.
    Args:
        path (str): The path to forward the request to, extracted from the URL.
        request (Request): The incoming HTTP request from the client.
    Returns:
        Response: The HTTP response received from the Authentication Service API, which is forwarded back to the client.
    """

    target_url = f"{url}/{path.rstrip('/')}"

    json_body = None
    if request.method in ["POST", "PUT", "PATCH"]:
        try:
            json_body = await request.json()
        except Exception:
            json_body = None

    headers = {
        k: v for k, v in request.headers.items() if k.lower() not in ["host", "content-length"]
    }

    async with httpx.AsyncClient(timeout=None) as client:
        response = await client.request(
            method=request.method, url=target_url, headers=headers, json=json_body
        )

    proxy_response = Response(
        content=response.content,
        status_code=response.status_code,
    )

    for key, value in response.headers.multi_items():
        if key.lower() == "set-cookie":
            proxy_response.headers.append(key, value)
        elif key.lower() not in (
            "content-length",
            "transfer-encoding",
            "content-encoding",
        ):
            proxy_response.headers[key] = value

    return proxy_response

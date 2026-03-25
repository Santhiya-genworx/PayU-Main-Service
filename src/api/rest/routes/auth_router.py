import httpx
from fastapi import APIRouter, Request, Response

from src.core.config.settings import settings

auth_router = APIRouter()

url = settings.auth_service_url


@auth_router.api_route("/auth/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def auth_proxy(path: str, request: Request) -> Response:
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

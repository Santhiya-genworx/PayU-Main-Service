from fastapi import APIRouter, Request, Response
from src.core.config.settings import settings
import httpx

process_router = APIRouter()

url = settings.process_service_url

@process_router.api_route("/process/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def process_proxy(path: str, request: Request):

    query = request.url.query

    target_url = f"{url}/{path.rstrip('/')}"
    if query:
        target_url = f"{target_url}?{query}"

    print("PROCESS PROXY TO:", target_url)

    # ✅ Detect content type
    content_type = request.headers.get("content-type", "")

    headers = {
        k: v
        for k, v in request.headers.items()
        if k.lower() not in ["host", "content-length"]
    }

    async with httpx.AsyncClient(timeout=None) as client:

        # 🔥 CASE 1: FILE UPLOAD (multipart/form-data)
        if "multipart/form-data" in content_type:
            body = await request.body()

            response = await client.request(
                method=request.method,
                url=target_url,
                headers=headers,
                content=body   # ✅ RAW BODY
            )

        # 🔥 CASE 2: JSON
        else:
            json_body = None
            if request.method in ["POST", "PUT", "PATCH"]:
                try:
                    json_body = await request.json()
                except:
                    json_body = None

            response = await client.request(
                method=request.method,
                url=target_url,
                headers=headers,
                json=json_body
            )

    print("PROCESS RESPONSE:", response.status_code)

    proxy_response = Response(
        content=response.content,
        status_code=response.status_code,
    )

    for key, value in response.headers.items():
        if key.lower() not in ("content-length", "transfer-encoding", "content-encoding"):
            proxy_response.headers[key] = value

    return proxy_response
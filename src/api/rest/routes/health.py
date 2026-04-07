"""Module: health.py"""

from fastapi import APIRouter

health_router = APIRouter()


@health_router.get("/health")
def health_check() -> dict[str, str]:
    """Endpoint to check the health of the API.
    This endpoint returns a simple JSON response indicating that the health check was successful. It can be used for monitoring and ensuring that the API is operational. The response is a dictionary containing a message field with the health status of the API.
    Returns:
        A dictionary with a message indicating the health status of the API.
    """
    return {"message": "PayU - Main Service Health Check!"}

from fastapi import APIRouter

health_router = APIRouter()


@health_router.get("/health")
def health_check() -> dict[str, str]:
    return {"message": "PayU - Main Service Health Check!"}

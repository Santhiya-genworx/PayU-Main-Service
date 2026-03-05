from fastapi import APIRouter
from src.api.rest.routes.auth_router import auth_router
from src.api.rest.routes.invoice_router import invoice_router
from src.api.rest.routes.health import health_router

app_router = APIRouter()

app_router.include_router(health_router)
app_router.include_router(auth_router)
app_router.include_router(invoice_router)
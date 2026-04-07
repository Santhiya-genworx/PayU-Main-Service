"""This is the main entry point for the PayU Main Service application. It sets up the FastAPI application, including middleware for CORS and logging, and defines a simple welcome endpoint. The application is configured to allow cross-origin requests from specified origins and to log all incoming requests and outgoing responses for better observability. The welcome endpoint serves as a health check or greeting message to confirm that the service is operational. This module serves as the central hub for initializing and running the PayU Main Service, tying together various components such as configuration, middleware, and API routes."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.middlewares.logging import LoggingMiddleware
from src.api.rest.app import app_router
from src.config.settings import settings

app = FastAPI(title="PayU - Main Service", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(LoggingMiddleware)

app.include_router(app_router)


@app.get("/")
def welcome() -> dict[str, str]:
    """Welcome endpoint for the PayU Main Service. This endpoint serves as a simple health check or greeting message to confirm that the service is up and running. When accessed, it returns a JSON response with a welcome message. This can be useful for monitoring purposes or to provide a friendly message to users who access the root URL of the service.  Returns:    A dictionary containing a welcome message to indicate that the PayU Main Service is operational."""
    return {"message": "Welcome to PayU - Main Service"}

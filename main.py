from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.middlewares.logging import LoggingMiddleware
from src.api.rest.app import app_router

app = FastAPI(title="PayU - Main Service", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"], 
)
app.add_middleware(LoggingMiddleware)

app.include_router(app_router)

@app.get("/")
def welcome():
    return {"message": "Welcome to PayU - Main Service"}
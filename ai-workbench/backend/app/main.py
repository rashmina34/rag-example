from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.chat import router as chat_router
from app.api.workflows import (
    router as workflow_router,
)

from app.models.database import Base
from app.models.database import engine

from app.models import workflow_db


Base.metadata.create_all(
    bind=engine
)


app = FastAPI(
    title="AI Workbench API",
    version="0.3.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(
    chat_router,
    prefix="/api",
)


app.include_router(
    workflow_router,
    prefix="/api",
)


@app.get("/")
def root():

    return {
        "message": "AI Workbench API",
        "version": "0.3.0",
    }


@app.get("/health")
def health():

    return {
        "status": "ok",
    }
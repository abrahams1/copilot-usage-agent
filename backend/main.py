"""FastAPI application entrypoint."""

from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import router
from backend.config import settings

logging.basicConfig(level=settings.log_level)

app = FastAPI(
    title="Copilot Usage Agent",
    version="0.1.0",
    description="AI agent for M365 Copilot, Copilot Studio, and Azure AI Foundry usage analytics.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

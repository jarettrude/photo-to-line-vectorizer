"""
FastAPI main application.

Entry point for the photo-to-line-vectorizer backend service.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from api.endpoints import router as api_router
from config import settings

logging.basicConfig(
    level=logging.INFO if settings.debug else logging.WARNING,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Handles startup and shutdown tasks.
    """
    logger.info("Starting photo-to-line-vectorizer backend")
    logger.info(f"Upload directory: {settings.upload_dir}")
    logger.info(f"Results directory: {settings.results_dir}")

    settings.ensure_directories()

    yield

    logger.info("Shutting down photo-to-line-vectorizer backend")


app = FastAPI(
    title="Photo to Line Vectorizer API",
    description="Convert photographs to plotter-ready line art SVG",
    version="1.0.0",
    lifespan=lifespan,
)

origins = [
    origin.strip() for origin in settings.allowed_origins.split(",") if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

app.include_router(api_router, prefix="/api", tags=["api"])


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Photo to Line Vectorizer API",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "upload": "/api/upload",
            "process": "/api/process",
            "status": "/api/status/{job_id}",
            "download": "/api/download/{job_id}",
        },
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )

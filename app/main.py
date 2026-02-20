import logging
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

# Configure logging BEFORE importing other modules
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("nid-ocr-api")

# Database setup
from app.database import engine, Base
Base.metadata.create_all(bind=engine)

# Routers
from app.routers import ocr_router

# Initialize FastAPI
app = FastAPI(
    title="NID OCR API",
    description="Production-ready API for extracting Name, DOB, and NID Number from ID cards",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(ocr_router.router)

@app.get("/")
async def root():
    return {
        "service": "NID OCR API",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "extract": "/api/v1/extract-nid (POST)",
            "results": "/api/v1/results/{id} (GET)",
        },
        "documentation": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    logger.info("Starting NID OCR API server...")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,  # Disable reload in production
        log_level="info",
        workers=1  # Single worker for simplicity
    )
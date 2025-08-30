"""
Simple FastAPI Application for Week 3

Minimal FastAPI app with only the required /chat and /health endpoints.
"""

import os
import uvicorn
from fastapi import FastAPI

from api.endpoints import chat_router, health_router


# Create simple FastAPI application
app = FastAPI(
    title="CSV Analytics API",
    version="3.0.0"
)

# Include only required endpoints
app.include_router(chat_router)
app.include_router(health_router)


if __name__ == "__main__":
    # Run the server
    print("🚀 Starting FastAPI server...")
    print(f"📡 Host: 0.0.0.0")
    print(f"🔌 Port: 8000")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )

"""
Simple API Models for Week 3

Basic Pydantic models for the required /chat and /health endpoints only.
"""

from pydantic import BaseModel
from typing import Optional


class ChatRequest(BaseModel):
    """Request for chat endpoint."""
    message: str


class ChatResponse(BaseModel):
    """Response from chat endpoint."""
    success: bool
    response: str


class HealthResponse(BaseModel):
    """Response from health endpoint."""
    status: str
    version: str = "3.0.0"

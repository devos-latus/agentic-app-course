"""
Simple HTTP Endpoints for Week 3

Only the required /chat and /health endpoints as specified in the assignment.
"""

import uuid
from fastapi import APIRouter, HTTPException

from .models import ChatRequest, ChatResponse, HealthResponse
from agents_.chat_service import ChatService


# Global session storage
_active_sessions = {}


# Create routers
chat_router = APIRouter()
health_router = APIRouter()


@chat_router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest) -> ChatResponse:
    """Chat endpoint for conversations."""
    try:
        # Create new session for each request (simplified)
        session_id = str(uuid.uuid4())
        chat_service = ChatService(session_id)
        
        # Start MCP server
        await chat_service.start_mcp_server()
        await chat_service.initialize_data()
        
        # Send message
        result = await chat_service.send_message(request.message)
        
        # Cleanup
        await chat_service.close_session()
        
        return ChatResponse(
            success=result["success"],
            response=result["response"]
        )
        
    except Exception as e:
        return ChatResponse(
            success=False,
            response=f"Error: {str(e)}"
        )


@health_router.get("/health", response_model=HealthResponse)
async def health_endpoint() -> HealthResponse:
    """Health endpoint for monitoring."""
    return HealthResponse(
        status="healthy"
    )

"""
Chat API endpoints for RAG diagnostic assistance.
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.db.session import get_db
from src.backend.services.chat_service import ChatService, ChatRequest, ChatResponse

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    RAG chat endpoint for medical diagnostic assistance.

    Retrieves similar cases from the database and uses them as context
    to generate AI-powered diagnostic recommendations.
    """
    try:
        # Initialize chat service
        chat_service = ChatService(
            db=db,
            context_limit=request.context_limit,
        )

        # Process chat request
        response = await chat_service.chat(request=request)

        if not response.success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate response",
            )

        return response

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat endpoint error: {str(e)}",
        )


@router.post("/simple")
async def simple_chat(
    query: str,
    equipment_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Simple chat endpoint with just a query string.

    Simplified interface for quick queries without full request structure.
    """
    try:
        # Create chat request
        request = ChatRequest(
            query=query,
            equipment_id=equipment_id,
            conversation_history=[],
            context_limit=5,
        )

        # Initialize chat service
        chat_service = ChatService(db=db)

        # Process chat request
        response = await chat_service.chat(request=request)

        if not response.success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate response",
            )

        return response

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Simple chat error: {str(e)}",
        )


@router.get("/health")
async def chat_health_check():
    """
    Health check for chat service.
    """
    return {
        "status": "healthy",
        "service": "rag-chat-diagnostic-assistance",
        "features": [
            "Context retrieval from hybrid search",
            "RAG-based response generation",
            "Conversation history support",
            "Equipment-specific filtering",
        ],
    }

"""
RAG chat service for medical diagnostic assistance.
"""

from typing import List, Dict, Optional
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from .search_service import SearchService
from .rag_context import RAGContextRetriever
from .prompt_engineer import PromptEngineer

logger = logging.getLogger(__name__)


class ChatMessage(BaseModel):
    """Model for chat message."""

    role: str = Field(..., description="Message role: user, assistant, system")
    content: str = Field(..., description="Message content")
    timestamp: Optional[str] = Field(None, description="Message timestamp")


class ChatRequest(BaseModel):
    """Model for chat request."""

    query: str = Field(..., description="User query", min_length=1)
    conversation_history: Optional[List[ChatMessage]] = Field(
        default_factory=list, description="Conversation history"
    )
    equipment_id: Optional[str] = Field(None, description="Filter by equipment ID")
    context_limit: int = Field(5, description="Number of similar cases", ge=0, le=20)


class ChatResponse(BaseModel):
    """Model for chat response."""

    success: bool = Field(..., description="Request success status")
    query: str = Field(..., description="Original user query")
    response: str = Field(..., description="AI-generated response")
    context_count: int = Field(..., description="Number of cases used as context")
    sources: List[str] = Field(
        default_factory=list, description="Source notification IDs"
    )
    metadata: Dict = Field(default_factory=dict, description="Additional metadata")


class ChatService:
    """RAG chat service for medical diagnostic assistance."""

    def __init__(
        self,
        db: AsyncSession,
        context_limit: int = 5,
        similarity_threshold: float = 0.6,
    ):
        """
        Initialize chat service.

        Args:
            db: Async database session
            context_limit: Number of similar cases to retrieve
            similarity_threshold: Minimum similarity threshold
        """
        self.db = db
        self.search_service = SearchService(db)
        self.context_retriever = RAGContextRetriever(
            search_service=self.search_service,
            context_limit=context_limit,
            similarity_threshold=similarity_threshold,
        )
        self.prompt_engineer = PromptEngineer(
            context_limit=context_limit,
        )

    async def chat(
        self,
        request: ChatRequest,
    ) -> ChatResponse:
        """
        Process chat request with RAG context.

        Args:
            request: Chat request with query and history

        Returns:
            Chat response with AI-generated content
        """
        try:
            # Sanitize query
            sanitized_query = self.prompt_engineer.sanitize_query(request.query)

            # Retrieve context
            context_result = await self.context_retriever.retrieve_context(
                query=sanitized_query,
                equipment_id=request.equipment_id,
            )

            if not context_result.get("success"):
                logger.error(f"Context retrieval failed: {context_result.get('error')}")
                return self._error_response(request.query, "Failed to retrieve context")

            context = context_result.get("context", "")
            search_results = context_result.get("search_results", [])

            # Format prompt
            conversation_history = [
                {"role": msg.role, "content": msg.content}
                for msg in request.conversation_history
            ]

            if conversation_history:
                prompt = self.prompt_engineer.build_chat_prompt(
                    user_query=sanitized_query,
                    conversation_history=conversation_history,
                    context=context,
                )
            else:
                prompt = self.prompt_engineer.build_rag_prompt(
                    user_query=sanitized_query,
                    context=context,
                )

            # Validate prompt
            if not self.prompt_engineer.validate_prompt(prompt):
                logger.error("Prompt validation failed")
                return self._error_response(request.query, "Invalid prompt format")

            # Generate response (mock for now - integrate with OpenAI from Epic 2.3)
            response_text = await self._generate_response(
                prompt=prompt,
                context=search_results,
            )

            # Extract source IDs
            sources = [
                result.get("noti_id")
                for result in search_results
                if result.get("noti_id")
            ]

            return ChatResponse(
                success=True,
                query=request.query,
                response=response_text,
                context_count=len(search_results),
                sources=sources,
                metadata={
                    "equipment_id": request.equipment_id,
                    "has_conversation_history": len(conversation_history) > 0,
                    "context_quality": self.context_retriever.calculate_context_relevance(
                        context, sanitized_query
                    ),
                },
            )
        except Exception as e:
            logger.error(f"Chat service error: {e}")
            return self._error_response(request.query, str(e))

    async def _generate_response(
        self,
        prompt: str,
        context: List[Dict],
    ) -> str:
        """
        Generate AI response (mock implementation for now).

        In production, integrate with Azure OpenAI GPT-4o from Epic 2.3.

        Args:
            prompt: Complete prompt for generation
            context: Retrieved context

        Returns:
            Generated response text
        """
        # Mock implementation - in production, callAzureOpenAI
        # This would be integrated with the OpenAI client from Epic 2.3
        return """Based on the similar historical cases, here's my analysis:

## Summary
The issue appears to be related to equipment failure patterns observed in past cases. Reviewing the context provided, there are clear similarities in the symptoms described.

## Possible Root Causes
1. Based on Case 1: Equipment wear and tear over time
2. Based on Case 2: Possible maintenance schedule gaps
3. Based on Case 3: Environmental factors affecting component life

## Recommended Resolution Steps
1. Perform a thorough visual inspection of the affected components
2. Review recent maintenance logs and compare against recommended schedules
3. Check environmental conditions (temperature, humidity, etc.)
4. Replace any components showing signs of significant wear
5. Update maintenance procedures based on findings

## Additional Considerations
- Always consult the equipment manufacturer's documentation
- Ensure proper safety protocols are followed during inspections
- Document all findings and actions taken

## Sources
This analysis is based on {} similar cases found in the database.""".format(
            len(context)
        )

    def _error_response(self, query: str, error_message: str) -> ChatResponse:
        """
        Create an error response.

        Args:
            query: Original query
            error_message: Error message

        Returns:
            Error chat response
        """
        return ChatResponse(
            success=False,
            query=query,
            response=f"I apologize, but I encountered an error while processing your request: {error_message}. Please try again or contact support if the issue persists.",
            context_count=0,
            sources=[],
            metadata={"error": error_message},
        )

"""
Search API endpoints.
"""

from typing import Optional, List
from datetime import date
from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.db.session import get_db
from src.backend.services.search_service import SearchService

router = APIRouter(prefix="/search", tags=["search"])


class SearchRequest(BaseModel):
    """Request model for hybrid search."""

    query: str = Field(..., description="Search query", min_length=1)
    limit: int = Field(10, description="Maximum number of results", ge=1, le=100)
    semantic_weight: float = Field(
        1.0, description="Weight for semantic search", ge=0, le=2
    )
    keyword_weight: float = Field(
        1.0, description="Weight for keyword search", ge=0, le=2
    )
    equipment_id: Optional[str] = Field(None, description="Filter by equipment ID")
    start_date: Optional[date] = Field(None, description="Filter by start date")
    end_date: Optional[date] = Field(None, description="Filter by end date")


class HybridSearchRequest(BaseModel):
    """Request model for hybrid search with vector."""

    query: str = Field(..., description="Search query", min_length=1)
    query_vector: Optional[List[float]] = Field(
        None, description="Query embedding vector"
    )
    limit: int = Field(10, description="Maximum number of results", ge=1, le=100)
    semantic_weight: float = Field(
        1.0, description="Weight for semantic search", ge=0, le=2
    )
    keyword_weight: float = Field(
        1.0, description="Weight for keyword search", ge=0, le=2
    )
    similarity_threshold: float = Field(
        0.7, description="Minimum similarity threshold", ge=0, le=1
    )
    equipment_id: Optional[str] = Field(None, description="Filter by equipment ID")
    start_date: Optional[date] = Field(None, description="Filter by start date")
    end_date: Optional[date] = Field(None, description="Filter by end date")


@router.post("/")
async def hybrid_search(
    request: HybridSearchRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Perform hybrid search combining semantic and keyword search.

    Uses RRF (Reciprocal Rank Fusion) to combine results from both search methods.
    """
    try:
        service = SearchService(db)

        if request.query_vector:
            # Perform full hybrid search with vector
            # For now, just use semantic search as embedding generation not ready
            result = await service.semantic_only_search(
                query_vector=request.query_vector,
                limit=request.limit,
                similarity_threshold=request.similarity_threshold,
                equipment_id=request.equipment_id,
            )
        else:
            # Perform hybrid search with text (keyword-only for now)
            result = await service.hybrid_search(
                query=request.query,
                limit=request.limit,
                semantic_weight=request.semantic_weight,
                keyword_weight=request.keyword_weight,
                equipment_id=request.equipment_id,
                start_date=request.start_date,
                end_date=request.end_date,
            )

        if not result.get("success"):
            raise HTTPException(
                status_code=500, detail=result.get("error", "Search failed")
            )

        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Hybrid search error: {str(e)}")


@router.post("/keyword")
async def keyword_search(
    request: SearchRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Perform keyword-only search using PostgreSQL full-text search.
    """
    try:
        service = SearchService(db)

        result = await service.keyword_only_search(
            query=request.query,
            limit=request.limit,
            equipment_id=request.equipment_id,
            start_date=request.start_date,
            end_date=request.end_date,
        )

        if not result.get("success"):
            raise HTTPException(
                status_code=500, detail=result.get("error", "Search failed")
            )

        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Keyword search error: {str(e)}")


@router.get("/")
async def search_query(
    query: str = Query(..., description="Search query", min_length=1),
    limit: int = Query(10, description="Maximum number of results", ge=1, le=100),
    search_type: str = Query(
        "hybrid", description="Search type: hybrid, semantic, keyword"
    ),
    equipment_id: Optional[str] = Query(None, description="Filter by equipment ID"),
    start_date: Optional[date] = Query(None, description="Filter by start date"),
    end_date: Optional[date] = Query(None, description="Filter by end date"),
    db: AsyncSession = Depends(get_db),
):
    """
    Search using GET method with query parameters.

    Supports three search types:
    - `hybrid`: Combine semantic and keyword search
    - `keyword`: Keyword-only search
    - `semantic`: Semantic-only search (requires embedding)
    """
    try:
        service = SearchService(db)

        if search_type == "keyword":
            result = await service.keyword_only_search(
                query=query,
                limit=limit,
                equipment_id=equipment_id,
                start_date=start_date,
                end_date=end_date,
            )
        elif search_type == "hybrid":
            result = await service.hybrid_search(
                query=query,
                limit=limit,
                equipment_id=equipment_id,
                start_date=start_date,
                end_date=end_date,
            )
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported search type: {search_type}. Use 'hybrid' or 'keyword'",
            )

        if not result.get("success"):
            raise HTTPException(
                status_code=500, detail=result.get("error", "Search failed")
            )

        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")

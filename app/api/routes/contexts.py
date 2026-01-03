import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.schemas.task import ContextResponse
from app.core.storage. redis_store import RedisContextStore
from app.api.main import get_context_store

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/{context_id}", response_model=ContextResponse)
async def get_context(
    context_id: str,
    context_store: RedisContextStore = Depends(get_context_store),
):
    """Get a specific context by ID."""
    context = await context_store.get_context(context_id)
    
    if not context:
        raise HTTPException(status_code=404, detail=f"Context {context_id} not found")
    
    return ContextResponse(
        id=context.id,
        content=context.content,
        reported_by=context.reported_by,
        task_id=context.task_id,
        timestamp=context.timestamp
    )


@router.get("/", response_model=List[ContextResponse])
async def list_contexts(
    task_id:  str = Query(None, description="Filter by task ID"),
    limit: int = Query(20, ge=1, le=100),
    context_store: RedisContextStore = Depends(get_context_store),
):
    """List contexts, optionally filtered by task."""
    try:
        if task_id:
            contexts = await context_store.get_contexts_for_task(task_id)
        else:
            contexts = await context_store.get_all_contexts(limit=limit)
        
        # 确保返回的是列表（即使为空）
        if not contexts:
            return []
        
        return [
            ContextResponse(
                id=ctx.id,
                content=ctx.content,
                reported_by=ctx.reported_by,
                task_id=ctx.task_id,
                timestamp=ctx.timestamp
            )
            for ctx in contexts
        ]
    except Exception as e:
        logger. error(f"Error listing contexts:  {e}")
        # 返回空列表而不是抛出异常
        return []


@router.get("/search/", response_model=List[ContextResponse])
async def search_contexts(
    q: str = Query(..., description="Search query", min_length=1),
    limit: int = Query(10, ge=1, le=50),
    context_store: RedisContextStore = Depends(get_context_store),
):
    """Search contexts by content."""
    try:
        contexts = await context_store.search_contexts(q, limit=limit)
        
        if not contexts:
            return []
        
        return [
            ContextResponse(
                id=ctx. id,
                content=ctx. content,
                reported_by=ctx.reported_by,
                task_id=ctx.task_id,
                timestamp=ctx. timestamp
            )
            for ctx in contexts
        ]
    except Exception as e:
        logger. error(f"Error searching contexts:  {e}")
        return []


@router.delete("/{context_id}")
async def delete_context(
    context_id: str,
    context_store: RedisContextStore = Depends(get_context_store),
):
    """Delete a context."""
    deleted = await context_store.delete_context(context_id)
    
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Context {context_id} not found")
    
    return {"message": f"Context {context_id} deleted successfully"}
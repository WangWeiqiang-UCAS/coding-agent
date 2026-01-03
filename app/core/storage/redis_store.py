"""Redis-based context store for multi-agent system."""

import json
import logging
from typing import Optional, List, Dict
import redis. asyncio as redis

from app.core.actions.entities. context import Context

logger = logging.getLogger(__name__)


class RedisContextStore: 
    """Redis-based storage for discovered contexts."""
    
    def __init__(self, redis_client:  redis.Redis):
        """Initialize context store. 
        
        Args:
            redis_client:  Async Redis client instance
        """
        self.redis = redis_client
        self. key_prefix = "context:"
        self.task_index_prefix = "task_contexts:"
    
    async def add_context(self, context: Context) -> bool:
        """Add a context to the store.
        
        Args:
            context: Context object to store
            
        Returns:
            True if added successfully, False if already exists
        """
        key = f"{self.key_prefix}{context.id}"
        
        # Check if already exists
        exists = await self.redis.exists(key)
        async with self.redis.pipeline(transaction=True) as pipe:
            while True:
                try:
                    await pipe.watch(key)  # 监视 key
                    exists = await pipe.exists(key)
                    if exists:
                        return False

                    pipe.multi()  # 开始事务
                    context_data = {
                    "id": context.id,
                    "content": context.content,
                    "reported_by": context.reported_by,
                    "task_id": context.task_id or "",
                    "timestamp": str(context.timestamp)
                    }
                    pipe.hset(key, mapping=context_data)
                    # Add to task index if task_id provided
                    await pipe.execute()  # 如果 key 被修改，自动重试
                    break
                except redis.WatchError:
                    continue  # 重试
        
        # Add to task index if task_id provided
        if context.task_id:
            task_key = f"{self.task_index_prefix}{context.task_id}"
            await self.redis.sadd(task_key, context.id)
        
        # Set expiration (7 days)
        await self. redis.expire(key, 604800)
        
        logger. info(f"Added context {context.id} to store")
        return True
    
    async def get_context(self, context_id: str) -> Optional[Context]:
        """Get a context by ID.
        
        Args:
            context_id: Context identifier
            
        Returns:
            Context object or None if not found
        """
        key = f"{self.key_prefix}{context_id}"
        data = await self.redis.hgetall(key)
        
        if not data:
            logger.debug(f"Context {context_id} not found")
            return None
        
        # Convert bytes to strings and reconstruct Context
        context_dict = {k:  v for k, v in data.items()}
        context_dict["timestamp"] = float(context_dict["timestamp"])
        if not context_dict["task_id"]:
            context_dict["task_id"] = None
        
        return Context(**context_dict)
    
    async def get_contexts_for_task(self, task_id: str) -> List[Context]:
        """Get all contexts associated with a task.
        
        Args:
            task_id:  Task identifier
            
        Returns: 
            List of Context objects
        """
        task_key = f"{self.task_index_prefix}{task_id}"
        context_ids = await self.redis. smembers(task_key)
        
        contexts = []
        for cid in context_ids:
            ctx = await self.get_context(cid)
            if ctx: 
                contexts.append(ctx)
        
        logger.debug(f"Retrieved {len(contexts)} contexts for task {task_id}")
        return contexts
    
    async def get_contexts_by_ids(self, context_ids: List[str]) -> Dict[str, str]:
        """Get multiple contexts by their IDs.
        
        Args:
            context_ids:  List of context identifiers
            
        Returns: 
            Dictionary mapping context_id -> content
        """
        result = {}
        for cid in context_ids: 
            ctx = await self.get_context(cid)
            if ctx:
                result[cid] = ctx.content
            else:
                logger.warning(f"Context {cid} not found")
        
        return result
    
    async def search_contexts(
        self, 
        query:  str, 
        limit: int = 10
    ) -> List[Context]:
        """Search contexts by content (simple substring match).
        
        Args:
            query: Search query
            limit: Maximum results to return
            
        Returns: 
            List of matching Context objects
        """
        # Use SCAN to iterate through all context keys
        contexts = []
        cursor = 0
        query_lower = query.lower()
        
        while True:
            cursor, keys = await self.redis.scan(
                cursor,
                match=f"{self.key_prefix}*",
                count=100
            )
            
            for key in keys:
                if len(contexts) >= limit:
                    return contexts
                
                # Extract context_id from key
                context_id = key.replace(self.key_prefix, '')
                ctx = await self.get_context(context_id)
                
                if ctx and query_lower in ctx.content.lower():
                    contexts.append(ctx)
            
            if cursor == 0:
                break
        
        logger.debug(f"Search found {len(contexts)} contexts for query:  {query}")
        return contexts
    
    async def delete_context(self, context_id: str) -> bool:
        """Delete a context from the store.
        
        Args:
            context_id: Context identifier
            
        Returns: 
            True if deleted, False if not found
        """
        key = f"{self.key_prefix}{context_id}"
        
        # Get context to find task_id
        ctx = await self.get_context(context_id)
        
        # Delete from main store
        deleted = await self.redis.delete(key)
        
        # Remove from task index if exists
        if ctx and ctx.task_id:
            task_key = f"{self.task_index_prefix}{ctx.task_id}"
            await self.redis.srem(task_key, context_id)
        
        if deleted:
            logger.info(f"Deleted context {context_id}")
            return True
        return False
    
    async def get_all_contexts(self, limit: int = 100) -> List[Context]:
        """Get all contexts (for debugging/admin purposes).
        
        Args:
            limit: Maximum contexts to return
            
        Returns: 
            List of Context objects
        """
        contexts = []
        cursor = 0
        
        while True:
            cursor, keys = await self.redis.scan(
                cursor,
                match=f"{self.key_prefix}*",
                count=100
            )
            
            for key in keys:
                if len(contexts) >= limit:
                    return contexts
                
                context_id = key.decode('utf-8').replace(self.key_prefix, '')
                ctx = await self.get_context(context_id)
                if ctx:
                    contexts.append(ctx)
            
            if cursor == 0:
                break
        
        return contexts
    
    async def clear_all(self) -> int:
        """Clear all contexts (for testing purposes).
        
        Returns:
            Number of contexts deleted
        """
        count = 0
        cursor = 0
        
        while True:
            cursor, keys = await self.redis.scan(
                cursor,
                match=f"{self.key_prefix}*",
                count=100
            )
            
            if keys:
                count += await self.redis.delete(*keys)
            
            if cursor == 0:
                break
        
        # Also clear task indexes
        cursor = 0
        while True: 
            cursor, keys = await self.redis.scan(
                cursor,
                match=f"{self.task_index_prefix}*",
                count=100
            )
            
            if keys: 
                await self.redis.delete(*keys)
            
            if cursor == 0:
                break
        
        logger.warning(f"Cleared {count} contexts from store")
        return count

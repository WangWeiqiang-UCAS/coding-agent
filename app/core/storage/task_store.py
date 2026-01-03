"""Redis-based task store for multi-agent system."""

import json
import logging
from typing import Optional, List
import redis.asyncio as redis

from app.core.actions.entities.task import Task, TaskStatus
import time

logger = logging.getLogger(__name__)


class TaskStore:
    """Redis-based storage for task management."""
    
    def __init__(self, redis_client: redis.Redis):
        """Initialize task store.
        
        Args:
            redis_client: Async Redis client instance
        """
        self.redis = redis_client
        self.key_prefix = "task:"
        self.status_index_prefix = "tasks:"
    
    async def create_task(
        self,
        task_id: str,
        agent_type: str,
        title:  str,
        description: str,
        max_turns: int = 20,
        context_refs: Optional[List[str]] = None,
        context_bootstrap: Optional[List[dict]] = None,
    ) -> Task:
        """Create a new task.
        
        Args:
            task_id:  Unique task identifier
            agent_type: Type of agent (explorer/coder)
            title: Task title
            description: Task description
            max_turns: Maximum turns allowed
            context_refs: Context IDs to provide
            context_bootstrap: Bootstrap file information
            
        Returns: 
            Created Task object
        """
        task = Task(
            task_id=task_id,
            agent_type=agent_type,
            title=title,
            description=description,
            status=TaskStatus.PENDING,
            max_turns=max_turns,
            context_refs=context_refs or [],
            context_bootstrap=context_bootstrap or [],
            completed_at=None,
            result=None,
            error=None,
        )
        
        # Store task as JSON
        key = f"{self.key_prefix}{task_id}"
        await self.redis.set(key, task.model_dump_json())
        
        # Add to status index
        await self.redis.sadd(f"{self.status_index_prefix}pending", task_id)
        
        # Set expiration (30 days)
        await self.redis. expire(key, 2592000)
        
        logger.info(f"Created task {task_id}:  {title}")
        return task
    
    async def get_task(self, task_id: str) -> Optional[Task]:
        """Get a task by ID.
        
        Args:
            task_id: Task identifier
            
        Returns:
            Task object or None if not found
        """
        key = f"{self.key_prefix}{task_id}"
        data = await self.redis.get(key)
        
        if not data:
            logger.debug(f"Task {task_id} not found")
            return None
        
        return Task.model_validate_json(data)
    
    async def update_task_status(
        self,
        task_id: str,
        status: TaskStatus,
        result: Optional[dict] = None,
        error: Optional[str] = None,
    ) -> bool:
        """Update task status. 
        
        Args:
            task_id: Task identifier
            status: New status
            result:  Execution result (for completed tasks)
            error: Error message (for failed tasks)
            
        Returns:
            True if updated successfully, False if task not found
        """
        task = await self.get_task(task_id)
        if not task:
            logger.warning(f"Cannot update status:  task {task_id} not found")
            return False
        
        # Remove from old status index
        await self.redis.srem(f"{self.status_index_prefix}{task.status.value}", task_id)
        
        # Update task
        task.status = status
        task.updated_at = time.time()
        
        if result:
            task.result = result
        if error:
            task.error = error
        if status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
            task.completed_at = time.time()
        
        # Save updated task
        key = f"{self.key_prefix}{task_id}"
        await self.redis.set(key, task.model_dump_json())
        
        # Add to new status index
        await self.redis.sadd(f"{self. status_index_prefix}{status. value}", task_id)
        
        logger.info(f"Updated task {task_id} status to {status.value}")
        return True
    
    async def get_tasks_by_status(self, status: TaskStatus, limit: int = 100) -> List[Task]:
        """Get all tasks with a specific status.
        
        Args:
            status: Task status to filter by
            limit: Maximum tasks to return
            
        Returns: 
            List of Task objects
        """
        status_key = f"{self.status_index_prefix}{status.value}"
        task_ids = await self.redis.smembers(status_key)
        
        tasks = []
        for tid in list(task_ids)[:limit]:
            task = await self.get_task(tid)
            if task:
                tasks.append(task)
        
        logger.debug(f"Retrieved {len(tasks)} tasks with status {status.value}")
        return tasks
    
    async def get_all_tasks(self, limit: int = 100) -> List[Task]:
        """Get all tasks (for debugging/admin purposes).
        
        Args:
            limit:  Maximum tasks to return
            
        Returns:
            List of Task objects
        """
        tasks = []
        cursor = 0
        
        while True:
            cursor, keys = await self.redis. scan(
                cursor,
                match=f"{self.key_prefix}*",
                count=100
            )
            
            for key in keys:
                if len(tasks) >= limit:
                    return tasks
                
                task_id = key.replace(self.key_prefix, '')
                task = await self.get_task(task_id)
                if task:
                    tasks.append(task)
            
            if cursor == 0:
                break
        
        return tasks
    
    async def delete_task(self, task_id: str) -> bool:
        """Delete a task. 
        
        Args:
            task_id: Task identifier
            
        Returns:
            True if deleted, False if not found
        """
        task = await self.get_task(task_id)
        if not task:
            return False
        
        # Remove from status index
        await self.redis.srem(f"{self. status_index_prefix}{task. status.value}", task_id)
        
        # Delete task
        key = f"{self. key_prefix}{task_id}"
        deleted = await self.redis.delete(key)
        
        if deleted:
            logger.info(f"Deleted task {task_id}")
            return True
        return False
    
    async def clear_all(self) -> int:
        """Clear all tasks (for testing purposes).
        
        Returns:
            Number of tasks deleted
        """
        count = 0
        cursor = 0
        
        # Delete all task keys
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
        
        # Clear status indexes
        for status in TaskStatus:
            await self.redis.delete(f"{self.status_index_prefix}{status.value}")
        
        logger.warning(f"Cleared {count} tasks from store")
        return count
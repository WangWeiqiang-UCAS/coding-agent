
"""Task management routes with real agent execution."""

import logging
from typing import List
import uuid
import time

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
import redis. asyncio as redis

from app.api.schemas.task import (
    TaskCreateRequest, TaskResponse, TaskDetailResponse, TaskStatusEnum
)
from app.core.storage.task_store import TaskStore
from app.core.storage.redis_store import RedisContextStore
from app.core.actions.entities.task import TaskStatus
from app.api.main import get_task_store, get_context_store
from app.core. agents.orchestrator import OrchestratorAgent
from app.core.execution.command_executor import LocalExecutor
from app.config.settings import settings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/", response_model=TaskResponse, status_code=201)
async def create_task(
    request: TaskCreateRequest,
    background_tasks: BackgroundTasks,
    task_store: TaskStore = Depends(get_task_store),
    context_store: RedisContextStore = Depends(get_context_store),
):
    """Create a new coding task. 
    
    This endpoint creates a task and starts execution in the background.
    """
    task_id = f"task_{uuid.uuid4().hex[:8]}"
    
    logger.info(f"Creating task {task_id}:  {request.instruction[: 50]}...")
    
    # 创建任务
    task = await task_store.create_task(
        task_id=task_id,
        agent_type="orchestrator",
        title=request.instruction[: 100],
        description=request.instruction,
        max_turns=request.max_turns,
    )
    
    # 后台执行（真实 Agent）
    background_tasks.add_task(
        execute_task_with_agent,
        task_id,
        request.instruction,
        request.max_turns,
        task_store,
        context_store
    )
    
    return TaskResponse(
        task_id=task. task_id,
        status=TaskStatusEnum(task.status. value),
        instruction=task.description,
        created_at=task.created_at
    )


@router.get("/{task_id}", response_model=TaskDetailResponse)
async def get_task(
    task_id: str,
    task_store: TaskStore = Depends(get_task_store),
):
    """Get task details by ID."""
    task = await task_store.get_task(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    
    return TaskDetailResponse(
        task_id=task.task_id,
        status=TaskStatusEnum(task.status.value),
        instruction=task.description,
        created_at=task.created_at,
        updated_at=task.updated_at,
        completed_at=task.completed_at,
        result=task.result,
        error=task.error
    )


@router.get("/", response_model=List[TaskResponse])
async def list_tasks(
    status: str = None,
    limit: int = 20,
    task_store: TaskStore = Depends(get_task_store),
):
    """List tasks, optionally filtered by status."""
    if status:
        try:
            task_status = TaskStatus(status)
            tasks = await task_store.get_tasks_by_status(task_status, limit=limit)
        except ValueError: 
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
    else:
        tasks = await task_store.get_all_tasks(limit=limit)
    
    return [
        TaskResponse(
            task_id=task.task_id,
            status=TaskStatusEnum(task. status.value),
            instruction=task.description,
            created_at=task.created_at
        )
        for task in tasks
    ]


@router.delete("/{task_id}")
async def delete_task(
    task_id: str,
    task_store: TaskStore = Depends(get_task_store),
):
    """Delete a task."""
    deleted = await task_store.delete_task(task_id)
    
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    
    return {"message": f"Task {task_id} deleted successfully"}


# ============================================
# 真实 Agent 执行
# ============================================

async def execute_task_with_agent(
    task_id:  str,
    instruction: str,
    max_turns: int,
    task_store: TaskStore,
    context_store: RedisContextStore
):
    """Execute task with real Orchestrator Agent. 
    
    Args:
        task_id: Task identifier
        instruction: Task instruction
        max_turns: Maximum turns allowed
        task_store: Task storage
        context_store: Context storage
    """
    logger.info(f"🚀 Starting agent execution for task {task_id}")
    
    try:
        # 更新状态为 running
        await task_store.update_task_status(task_id, TaskStatus.RUNNING)
        
        # 创建执行器
        executor = LocalExecutor(workspace_dir=str(settings.workspace_dir))
        
        # 创建 Orchestrator Agent
        orchestrator = OrchestratorAgent(
            task_id=task_id,
            executor=executor,
            context_store=context_store,
            task_store=task_store,
        )
        
        # 执行任务
        result = await orchestrator.run(instruction, max_turns=max_turns)
        
        # 更新任务状态
        if result["completed"]:
            await task_store.update_task_status(
                task_id,
                TaskStatus.COMPLETED,
                result={
                    "message": result["finish_message"],
                    "turns_executed": result["turns_executed"],
                    "elapsed_time": result["elapsed_time"],
                }
            )
            logger.info(f"✅ Task {task_id} completed:  {result['finish_message']}")
        else:
            await task_store.update_task_status(
                task_id,
                TaskStatus.FAILED,
                error=result["finish_message"]
            )
            logger.warning(f"⚠️ Task {task_id} failed: {result['finish_message']}")
        
    except Exception as e:
        logger.error(f"❌ Task {task_id} execution error: {e}", exc_info=True)
        await task_store.update_task_status(
            task_id,
            TaskStatus.FAILED,
            error=f"Execution error: {str(e)}"
        )

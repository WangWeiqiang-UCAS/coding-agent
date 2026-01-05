"""Agent runner with long-term memory support."""

import asyncio
import logging
from pathlib import Path
import uuid

from app.core.agents.orchestrator import OrchestratorAgent
from app.core.execution.command_executor import LocalExecutor
from app.core.storage.redis_store import RedisContextStore
from app.core.storage.task_store import TaskStore
from app.config.settings import settings
import redis.asyncio as redis

logger = logging.getLogger(__name__)


class AgentRunner:  
    """Manages agent execution with long-term memory."""
    
    def __init__(self, workspace: str = ".", verbose: bool = False, console=None):
        self.workspace = Path(workspace).absolute()
        self.verbose = verbose
        self.console = console
        
        if verbose:
            logging.basicConfig(level=logging.INFO, format='%(message)s')
        else:
            logging.basicConfig(level=logging.WARNING)
    
    async def run_task(self, instruction: str, max_turns: int = 20) -> dict:
        """Run a coding task with long-term memory.  
        
        Args:
            instruction: Task instruction
            max_turns: Maximum turns
            
        Returns:
            Result dictionary
        """
        task_id = f"cli_{uuid.uuid4().hex[:8]}"
        
        redis_client = await redis.from_url(
            settings.redis_url,
            decode_responses=True
        )
        
        try:
            await redis_client.ping()
            
            context_store = RedisContextStore(redis_client)
            task_store = TaskStore(redis_client)
            executor = LocalExecutor(workspace_dir=str(self.workspace))
            
            await task_store.create_task(
                task_id=task_id,
                agent_type="orchestrator",
                title=instruction[:100],
                description=instruction,
                max_turns=max_turns
            )
            
            agent = OrchestratorAgent(
                task_id=task_id,
                executor=executor,
                context_store=context_store,
                task_store=task_store,
                redis_client=redis_client,
                console=self.console,
            )
            
            if self.verbose:
                logger.info(f"Starting task {task_id}: {instruction}")
            
            result = await agent.run(instruction, max_turns=max_turns)
            
            from app.core.actions.entities.task import TaskStatus
            
            if result["completed"]:
                await task_store.update_task_status(
                    task_id,
                    TaskStatus.COMPLETED,
                    result=result
                )
            else:
                await task_store.update_task_status(
                    task_id,
                    TaskStatus.FAILED,
                    error=result["finish_message"]
                )
            
            result['task_id'] = task_id
            
            return result
            
        except redis.ConnectionError as e:
            logger.error(f"Redis connection failed: {e}")
            return {
                "completed": False,
                "finish_message": f"Redis connection failed: {e}",
                "turns_executed": 0,
                "elapsed_time": 0.0,
                "task_id": task_id
            }
        finally:
            await redis_client.close()
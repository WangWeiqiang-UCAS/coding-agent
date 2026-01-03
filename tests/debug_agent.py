
"""Quick debug script to test agent locally."""

import asyncio
import sys
sys.path.insert(0, '.')

from app.core.agents.orchestrator import OrchestratorAgent
from app.core. execution.command_executor import LocalExecutor
from app.core.storage.redis_store import RedisContextStore
from app.core.storage.task_store import TaskStore
from app.config.settings import settings
import redis.asyncio as redis


async def main():
    """Quick agent test."""
    print("🤖 Quick Agent Debug Test")
    print("=" * 60)
    
    # 连接 Redis
    redis_client = redis.from_url(settings.redis_url, decode_responses=True)
    context_store = RedisContextStore(redis_client)
    task_store = TaskStore(redis_client)
    
    # 创建执行器
    executor = LocalExecutor(workspace_dir="/tmp")
    
    # 创建任务
    task_id = "debug_task"
    await task_store.create_task(
        task_id=task_id,
        agent_type="orchestrator",
        title="Debug test",
        description="Debug test task",
        max_turns=5,
    )
    
    # 创建 Agent
    agent = OrchestratorAgent(
        task_id=task_id,
        executor=executor,
        context_store=context_store,
        task_store=task_store,
    )
    
    # 运行简单任务
    instruction = """Create a file at /tmp/test.txt with content "Hello Agent!"
Then read it back to verify.  Finally, finish."""
    
    print(f"\n📋 Task: {instruction}")
    print("\n🚀 Starting execution.. .\n")
    
    result = await agent.run(instruction, max_turns=5)
    
    print("\n" + "=" * 60)
    print("📊 Result:")
    print(f"  Completed: {result['completed']}")
    print(f"  Message: {result['finish_message']}")
    print(f"  Turns:  {result['turns_executed']}")
    print(f"  Time: {result['elapsed_time']:.2f}s")
    print("=" * 60)
    
    await redis_client.aclose()


if __name__ == "__main__": 
    asyncio.run(main())

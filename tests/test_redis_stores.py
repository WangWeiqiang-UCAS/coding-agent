"""Test Redis storage layers."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import redis.asyncio as redis
from app. config. settings import settings
from app.core.storage. redis_store import RedisContextStore
from app.core.storage.task_store import TaskStore
from app.core.actions.entities.context import Context
from app.core. actions.entities.task import TaskStatus
import time


async def test_context_store():
    """Test context store operations."""
    print("=" * 60)
    print("🧪 Test 1: Context Store")
    print("=" * 60)
    
    # Connect to Redis
    r = redis.from_url(settings.redis_url, decode_responses=True)
    store = RedisContextStore(r)
    
    try:
        # Clear existing data
        await store.clear_all()
        print("✅ Cleared existing contexts")
        
        # Test 1: Add context
        ctx1 = Context(
            id="test_ctx_1",
            content="This is a test context about API endpoints",
            reported_by="test_agent",
            task_id="task_001"
        )
        result = await store.add_context(ctx1)
        assert result is True, "Failed to add context"
        print("✅ Added context")
        
        # Test 2: Get context
        retrieved = await store.get_context("test_ctx_1")
        assert retrieved is not None, "Failed to retrieve context"
        assert retrieved.content == ctx1.content, "Content mismatch"
        print(f"✅ Retrieved context:  {retrieved.id}")
        
        # Test 3: Add another context for same task
        ctx2 = Context(
            id="test_ctx_2",
            content="Another context about database schema",
            reported_by="test_agent",
            task_id="task_001"
        )
        await store.add_context(ctx2)
        print("✅ Added second context")
        
        # Test 4: Get contexts for task
        task_contexts = await store.get_contexts_for_task("task_001")
        assert len(task_contexts) == 2, f"Expected 2 contexts, got {len(task_contexts)}"
        print(f"✅ Retrieved {len(task_contexts)} contexts for task")
        
        # Test 5: Get contexts by IDs
        ctx_dict = await store.get_contexts_by_ids(["test_ctx_1", "test_ctx_2"])
        assert len(ctx_dict) == 2, "Failed to get contexts by IDs"
        print(f"✅ Got contexts by IDs: {list(ctx_dict.keys())}")
        
        # Test 6: Search contexts
        results = await store. search_contexts("API", limit=10)
        assert len(results) >= 1, "Search failed"
        print(f"✅ Search found {len(results)} contexts")
        
        # Test 7: Delete context
        deleted = await store. delete_context("test_ctx_1")
        assert deleted is True, "Failed to delete context"
        print("✅ Deleted context")
        
        # Verify deletion
        retrieved = await store.get_context("test_ctx_1")
        assert retrieved is None, "Context still exists after deletion"
        print("✅ Verified deletion")
        
        print("\n✅ All context store tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        await r.close()


async def test_task_store():
    """Test task store operations."""
    print("\n" + "=" * 60)
    print("🧪 Test 2: Task Store")
    print("=" * 60)
    
    # Connect to Redis
    r = redis.from_url(settings.redis_url, decode_responses=True)
    store = TaskStore(r)
    
    try:
        # Clear existing data
        await store.clear_all()
        print("✅ Cleared existing tasks")
        
        # Test 1: Create task
        task = await store.create_task(
            task_id="test_task_1",
            agent_type="explorer",
            title="Test Task",
            description="This is a test task",
            max_turns=20,
            context_refs=["ctx_1", "ctx_2"],
            context_bootstrap=[{"path": "/test", "reason": "test file"}]
        )
        assert task. status == TaskStatus.PENDING, "Task should be pending"
        print(f"✅ Created task:  {task.task_id}")
        
        # Test 2: Get task
        retrieved = await store.get_task("test_task_1")
        assert retrieved is not None, "Failed to retrieve task"
        assert retrieved.title == "Test Task", "Title mismatch"
        print(f"✅ Retrieved task:  {retrieved.title}")
        
        # Test 3: Update task status
        success = await store.update_task_status(
            "test_task_1",
            TaskStatus. RUNNING
        )
        assert success is True, "Failed to update status"
        print("✅ Updated task status to RUNNING")
        
        # Verify status update
        task = await store.get_task("test_task_1")
        assert task.status == TaskStatus.RUNNING, "Status not updated"
        print("✅ Verified status update")
        
        # Test 4: Create multiple tasks
        await store.create_task(
            task_id="test_task_2",
            agent_type="coder",
            title="Second Task",
            description="Another test task",
        )
        await store.create_task(
            task_id="test_task_3",
            agent_type="explorer",
            title="Third Task",
            description="Yet another test task",
        )
        print("✅ Created multiple tasks")
        
        # Test 5: Get tasks by status
        pending_tasks = await store.get_tasks_by_status(TaskStatus.PENDING)
        assert len(pending_tasks) == 2, f"Expected 2 pending tasks, got {len(pending_tasks)}"
        print(f"✅ Found {len(pending_tasks)} pending tasks")
        
        running_tasks = await store. get_tasks_by_status(TaskStatus.RUNNING)
        assert len(running_tasks) == 1, f"Expected 1 running task, got {len(running_tasks)}"
        print(f"✅ Found {len(running_tasks)} running task")
        
        # Test 6: Complete task with result
        success = await store. update_task_status(
            "test_task_1",
            TaskStatus.COMPLETED,
            result={"message": "Task completed successfully"}
        )
        assert success is True, "Failed to complete task"
        print("✅ Completed task with result")
        
        # Verify completion
        task = await store.get_task("test_task_1")
        assert task. status == TaskStatus.COMPLETED, "Task not completed"
        assert task.result is not None, "Result not saved"
        assert task.completed_at is not None, "Completion time not set"
        print("✅ Verified task completion")
        
        # Test 7: Fail task with error
        await store.create_task(
            task_id="test_task_4",
            agent_type="coder",
            title="Failing Task",
            description="This task will fail",
        )
        success = await store.update_task_status(
            "test_task_4",
            TaskStatus.FAILED,
            error="Simulated error"
        )
        assert success is True, "Failed to mark task as failed"
        print("✅ Marked task as failed with error")
        
        # Test 8: Get all tasks
        all_tasks = await store.get_all_tasks()
        assert len(all_tasks) >= 4, "Failed to get all tasks"
        print(f"✅ Retrieved {len(all_tasks)} total tasks")
        
        # Test 9: Delete task
        deleted = await store. delete_task("test_task_4")
        assert deleted is True, "Failed to delete task"
        print("✅ Deleted task")
        
        print("\n✅ All task store tests passed!")
        return True
        
    except Exception as e: 
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally: 
        await r.close()


async def test_integration():
    """Test integration between context and task stores."""
    print("\n" + "=" * 60)
    print("🧪 Test 3: Integration Test")
    print("=" * 60)
    
    # Connect to Redis
    r = redis. from_url(settings.redis_url, decode_responses=True)
    context_store = RedisContextStore(r)
    task_store = TaskStore(r)
    
    try:
        # Clear existing data
        await context_store. clear_all()
        await task_store.clear_all()
        print("✅ Cleared all data")
        
        # Create a task
        task = await task_store.create_task(
            task_id="integration_task",
            agent_type="explorer",
            title="Integration Test Task",
            description="Task for integration testing",
            context_refs=["ctx_ref_1"]
        )
        print(f"✅ Created task: {task.task_id}")
        
        # Add contexts reported by this task
        ctx1 = Context(
            id="ctx_from_task",
            content="Context discovered during task execution",
            reported_by="explorer_agent",
            task_id="integration_task"
        )
        await context_store.add_context(ctx1)
        print(f"✅ Added context linked to task")
        
        # Retrieve contexts for this task
        task_contexts = await context_store.get_contexts_for_task("integration_task")
        assert len(task_contexts) == 1, "Context not linked to task"
        print(f"✅ Retrieved {len(task_contexts)} contexts for task")
        
        # Complete the task
        await task_store.update_task_status(
            "integration_task",
            TaskStatus.COMPLETED,
            result={"contexts_discovered": 1}
        )
        print("✅ Completed task")
        
        # Verify task and contexts are accessible
        final_task = await task_store. get_task("integration_task")
        final_contexts = await context_store. get_contexts_for_task("integration_task")
        
        assert final_task.status == TaskStatus.COMPLETED, "Task not completed"
        assert len(final_contexts) == 1, "Contexts not preserved"
        print("✅ Verified data integrity")
        
        print("\n✅ Integration test passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Integration test failed: {e}")
        import traceback
        traceback. print_exc()
        return False
        
    finally:
        await r.close()


async def main():
    """Run all tests."""
    print("\n" + "🚀" * 30)
    print("Redis Storage Layer Tests")
    print("🚀" * 30)
    
    print(f"\n📋 Configuration:")
    print(f"   Redis URL: {settings.redis_url}")
    
    # Check Redis connection
    try:
        r = redis.from_url(settings. redis_url)
        await r.ping()
        print(f"   ✅ Redis connection OK")
        await r.close()
    except Exception as e:
        print(f"   ❌ Redis connection failed: {e}")
        print("\n⚠️  Please ensure Redis is running:")
        print("   docker ps | grep redis")
        return
    
    # Run tests
    results = []
    results.append(await test_context_store())
    results.append(await test_task_store())
    results.append(await test_integration())
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    print(f"   Total:  {len(results)} tests")
    print(f"   Passed: {sum(results)}")
    print(f"   Failed: {len(results) - sum(results)}")
    
    if all(results):
        print("\n🎉 All storage tests passed!   Ready to build agents.")
    else:
        print("\n⚠️  Some tests failed.   Please check the output above.")
    print("=" * 60)


if __name__ == "__main__": 
    asyncio.run(main())

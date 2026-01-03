
"""Simple API test client."""

import asyncio
import httpx
import time


BASE_URL = "http://localhost:8000"


async def test_health():
    """Test health endpoint."""
    print("=" * 60)
    print("🧪 Testing Health Endpoint")
    print("=" * 60)
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
    print()


async def test_create_task():
    """Test task creation."""
    print("=" * 60)
    print("🧪 Testing Task Creation")
    print("=" * 60)
    
    async with httpx.AsyncClient() as client:
        # 创建任务
        task_data = {
            "instruction": "Create a simple Python function to calculate factorial",
            "max_turns":  30
        }
        
        response = await client.post(
            f"{BASE_URL}/api/v1/tasks/",
            json=task_data
        )
        
        print(f"Status: {response.status_code}")
        task = response.json()
        print(f"Task created: {task['task_id']}")
        print(f"Status: {task['status']}")
        
        task_id = task['task_id']
        
        # 等待任务执行
        print("\nWaiting for task execution...")
        await asyncio.sleep(3)
        
        # 查询任务状态
        response = await client.get(f"{BASE_URL}/api/v1/tasks/{task_id}")
        task_detail = response.json()
        
        print(f"\nTask {task_id} status: {task_detail['status']}")
        if task_detail. get('result'):
            print(f"Result: {task_detail['result']}")
        if task_detail. get('error'):
            print(f"Error: {task_detail['error']}")
    print()


async def test_list_tasks():
    """Test listing tasks."""
    print("=" * 60)
    print("🧪 Testing Task Listing")
    print("=" * 60)
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/api/v1/tasks/")
        tasks = response.json()
        
        print(f"Found {len(tasks)} tasks:")
        for task in tasks:
            print(f"  - {task['task_id']}:  {task['status']}")
    print()


async def test_contexts():
    """Test context endpoints."""
    print("=" * 60)
    print("🧪 Testing Context Endpoints")
    print("=" * 60)
    
    async with httpx.AsyncClient() as client:
        # 列出所有上下文
        response = await client.get(f"{BASE_URL}/api/v1/contexts/")
        contexts = response.json()
        
        print(f"Found {len(contexts)} contexts in store")
    print()


async def main():
    """Run all tests."""
    print("\n" + "🚀" * 30)
    print("API Test Suite")
    print("🚀" * 30 + "\n")
    
    try:
        await test_health()
        await test_create_task()
        await test_list_tasks()
        await test_contexts()
        
        print("=" * 60)
        print("✅ All tests completed!")
        print("=" * 60)
        
    except httpx.ConnectError: 
        print("❌ Failed to connect to API")
        print("Make sure the server is running:  uvicorn app. api. main:app --reload")
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

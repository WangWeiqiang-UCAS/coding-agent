
"""End-to-end agent test."""

import asyncio
import httpx
import time


BASE_URL = "http://localhost:8000"


async def test_simple_task():
    """Test a simple coding task."""
    print("=" * 60)
    print("🧪 End-to-End Agent Test:  Simple File Creation")
    print("=" * 60)
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        # 创建任务
        task_data = {
            "instruction": """Create a Python file at /tmp/hello.py with the following content:
def greet(name):
    return f"Hello, {name}!"

if __name__ == "__main__": 
    print(greet("World"))

After creating the file, run it to verify it works, then finish.""",
            "max_turns":  10
        }
        
        print("\n📤 Creating task...")
        response = await client.post(
            f"{BASE_URL}/api/v1/tasks/",
            json=task_data
        )
        
        if response.status_code != 201:
            print(f"❌ Failed to create task: {response.text}")
            return
        
        task = response.json()
        task_id = task['task_id']
        
        print(f"✅ Task created:  {task_id}")
        print(f"   Status: {task['status']}")
        
        # 轮询任务状态
        print("\n⏳ Waiting for agent execution...")
        max_wait = 60  # 60 seconds
        start = time.time()
        
        while time.time() - start < max_wait:
            await asyncio.sleep(2)
            
            response = await client.get(f"{BASE_URL}/api/v1/tasks/{task_id}")
            task_detail = response.json()
            status = task_detail['status']
            
            print(f"   [{int(time.time() - start)}s] Status: {status}")
            
            if status in ['completed', 'failed']:
                break
        
        # 显示最终结果
        print("\n" + "=" * 60)
        print("📊 Final Result")
        print("=" * 60)
        
        response = await client.get(f"{BASE_URL}/api/v1/tasks/{task_id}")
        task_detail = response.json()
        
        print(f"Status: {task_detail['status']}")
        print(f"Turns executed: {task_detail. get('result', {}).get('turns_executed', 'N/A')}")
        print(f"Elapsed time: {task_detail.get('result', {}).get('elapsed_time', 'N/A'):.2f}s")
        
        if task_detail['status'] == 'completed':
            print(f"\n✅ Success!")
            print(f"Message: {task_detail.get('result', {}).get('message', 'N/A')}")
        else:
            print(f"\n❌ Failed")
            print(f"Error:  {task_detail.get('error', 'N/A')}")


async def test_code_analysis():
    """Test code analysis task."""
    print("\n" + "=" * 60)
    print("🧪 End-to-End Agent Test: Code Analysis")
    print("=" * 60)
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        task_data = {
            "instruction": """Analyze the workspace directory: 
1. List all Python files
2. Count total lines of code
3. Create a summary file at /tmp/code_summary.txt

Then finish with a summary of your findings.""",
            "max_turns": 15
        }
        
        print("\n📤 Creating analysis task...")
        response = await client.post(
            f"{BASE_URL}/api/v1/tasks/",
            json=task_data
        )
        
        task = response.json()
        task_id = task['task_id']
        print(f"✅ Task created: {task_id}")
        
        # 等待完成
        print("\n⏳ Waiting for analysis...")
        await asyncio.sleep(10)
        
        # 查看结果
        response = await client.get(f"{BASE_URL}/api/v1/tasks/{task_id}")
        task_detail = response.json()
        
        print(f"\n📊 Status: {task_detail['status']}")
        if task_detail. get('result'):
            print(f"Message: {task_detail['result']. get('message', 'N/A')}")


async def main():
    """Run all E2E tests."""
    print("\n" + "🤖" * 30)
    print("End-to-End Agent Test Suite")
    print("🤖" * 30)
    
    try:
        await test_simple_task()
        await test_code_analysis()
        
        print("\n" + "=" * 60)
        print("✅ All E2E tests completed!")
        print("=" * 60)
        
    except httpx.ConnectError:
        print("❌ Failed to connect to API")
        print("Make sure the server is running:  uvicorn app. api.main:app --reload")
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

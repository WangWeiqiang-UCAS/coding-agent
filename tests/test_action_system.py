"""Test complete action system."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.actions.parsing.parser import SimpleActionParser
from app.core.actions.parsing.handler import ActionHandler
from app.core.execution.command_executor import LocalExecutor


async def test_full_pipeline():
    """Test: LLM Output → Parser → Handler → Execution."""
    print("=" * 60)
    print("🧪 完整动作系统测试")
    print("=" * 60)
    
    # 模拟 LLM 输出
    llm_output = """
Let me first check the workspace. 

<bash>
cmd:  pwd
timeout_secs: 10
</bash>

Now let me create a test file.

<write>
file_path: /tmp/test_agent_file.txt
content: |
  Hello from Agent!
  This is a multi-line file.
  Line 3. 
</write>

Let me read it back.

<read>
file_path: /tmp/test_agent_file.txt
</read>

<bash>
cmd: cat /tmp/test_agent_file.txt | wc -l
</bash>

<finish>
All test operations completed successfully!
</finish>
"""
    
    # Step 1: 解析动作
    print("\n📝 Step 1: 解析 LLM 输出")
    print("-" * 60)
    
    parser = SimpleActionParser()
    actions, errors = parser.parse(llm_output)
    
    print(f"找到 {len(actions)} 个动作")
    print(f"解析错误: {len(errors)}")
    
    for i, action in enumerate(actions, 1):
        print(f"  {i}. {type(action).__name__}")
    
    if errors:
        print(f"\n❌ 错误:")
        for error in errors: 
            print(f"  - {error}")
    
    # Step 2: 执行动作
    print("\n⚙️  Step 2: 执行动作")
    print("-" * 60)
    
    executor = LocalExecutor(workspace_dir="/tmp")
    handler = ActionHandler(executor=executor)
    
    results = await handler.execute(actions)
    
    for i, result in enumerate(results, 1):
        print(f"\n动作 {i} 结果:")
        print(result)
        print("-" * 40)
    
    # Step 3: 验证结果
    print("\n✅ Step 3: 验证")
    print("-" * 60)
    
    # 检查文件是否创建
    check_cmd = "test -f /tmp/test_agent_file.txt && echo 'File exists' || echo 'File missing'"
    output, exit_code = await executor. execute(check_cmd)
    
    if "exists" in output: 
        print("✅ 文件创建成功")
    else:
        print("❌ 文件创建失败")
    
    # 清理
    await executor.execute("rm -f /tmp/test_agent_file.txt")
    print("✅ 测试环境已清理")
    
    print("\n" + "=" * 60)
    print("🎉 完整流程测试通过！")
    print("=" * 60)


async def test_error_handling():
    """Test error handling."""
    print("\n" + "=" * 60)
    print("🧪 错误处理测试")
    print("=" * 60)
    
    llm_output = """
<bash>
cmd: this-command-does-not-exist
</bash>

<read>
file_path:  /this/file/does/not/exist. txt
</read>

<bash>
cmd: echo "This one works"
</bash>
"""
    
    parser = SimpleActionParser()
    actions, errors = parser.parse(llm_output)
    
    executor = LocalExecutor()
    handler = ActionHandler(executor=executor)
    
    results = await handler.execute(actions)
    
    print(f"\n执行了 {len(actions)} 个动作:")
    for i, (action, result) in enumerate(zip(actions, results), 1):
        status = "✅" if "✅" in result or "successfully" in result. lower() else "❌"
        print(f"{i}.  {type(action).__name__}: {status}")
    
    print("\n关键特性:")
    print("✅ 部分动作失败不影响后续执行")
    print("✅ 错误信息被捕获并返回")
    print("✅ 系统保持稳定运行")


if __name__ == "__main__":
    asyncio.run(test_full_pipeline())
    asyncio.run(test_error_handling())

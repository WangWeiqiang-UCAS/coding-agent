"""Quick parser test."""

import sys
sys.path.insert(0, '.')

from app.core.actions.parsing.parser import SimpleActionParser

# 测试用例 1：单个动作
llm_output_1 = """
Let me read the file first. 

<read>
file_path: src/main.py
offset: 10
limit: 50
</read>
"""

parser = SimpleActionParser()
actions, errors = parser.parse(llm_output_1)

print("=" * 60)
print("测试 1：单个 read 动作")
print("=" * 60)
print(f"找到 {len(actions)} 个动作")
print(f"错误数：{len(errors)}")
if actions:
    action = actions[0]
    print(f"动作类型：{type(action).__name__}")
    print(f"file_path: {action.file_path}")
    print(f"offset: {action.offset}")
    print(f"limit: {action.limit}")

# 测试用例 2：多个动作
llm_output_2 = """
<read>
file_path: test.py
</read>

<bash>
cmd: ls -la
timeout_secs: 30
</bash>

<finish>
All tasks completed successfully!
</finish>
"""

actions, errors = parser.parse(llm_output_2)

print("\n" + "=" * 60)
print("测试 2：多个动作")
print("=" * 60)
print(f"找到 {len(actions)} 个动作")
for i, action in enumerate(actions, 1):
    print(f"{i}. {type(action).__name__}")

# 测试用例 3：错误的 YAML
llm_output_3 = """
<read>
file_path: test. py
offset: abc
</read>
"""

actions, errors = parser.parse(llm_output_3)

print("\n" + "=" * 60)
print("测试 3：错误处理")
print("=" * 60)
print(f"找到 {len(actions)} 个动作")
print(f"错误数：{len(errors)}")
if errors:
    print(f"错误信息：{errors[0]}")


import sys
sys.path.insert(0, '.')

from app.core.actions.parsing.parser import SimpleActionParser

llm_output = """
<task_create>
agent_type: explorer
title: Test Task
description: This is a test
context_refs:
  - ctx_1
  - ctx_2
  - ctx_3
max_turns: 15
auto_launch: true
</task_create>
"""

parser = SimpleActionParser()
actions, errors = parser.parse(llm_output)

if actions:
    action = actions[0]
    print(f"✅ 解析成功！")
    print(f"agent_type: {action.agent_type}")
    print(f"title: {action.title}")
    print(f"context_refs: {action.context_refs}")
    print(f"类型检查：{type(action. context_refs)} = {action.context_refs}")
else:
    print(f"❌ 解析失败")
    print(f"错误：{errors}")
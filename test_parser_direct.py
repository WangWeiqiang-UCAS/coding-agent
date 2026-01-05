"""Direct parser test."""

import sys
sys.path.insert(0, '.')

from app.core.actions.parsing.parser import SimpleActionParser

# 测试用例 1: 标准格式（带 |）
test1 = """
<write>
file_path:  /tmp/test1.txt
content: |
  第一行
  第二行
  第三行
</write>
"""

# 测试用例 2: 无 | 标记（LLM 可能这样生成）
test2 = """
<write>
file_path: /tmp/test2.txt
content: 第一行
第二行
第三行
</write>
"""

# 测试用例 3: 空值后跟内容
test3 = """
<write>
file_path: /tmp/test3.txt
content:
第一行
第二行
第三行
</write>
"""

parser = SimpleActionParser()

for i, test_case in enumerate([test1, test2, test3], 1):
    print(f"\n{'='*60}")
    print(f"测试用例 {i}")
    print(f"{'='*60}")
    
    actions, errors = parser.parse(test_case)
    
    if errors:
        print(f"❌ 解析错误: {errors}")
    
    if actions:
        action = actions[0]
        print(f"✅ 解析成功")
        print(f"   file_path: {action. file_path}")
        print(f"   content 长度: {len(action. content)} 字符")
        print(f"   content 行数: {len(action.content.splitlines())} 行")
        print(f"   content 内容:")
        print("   ---")
        for line in action.content.splitlines():
            print(f"   {repr(line)}")
        print("   ---")
    else:
        print(f"❌ 未解析到任何 action")


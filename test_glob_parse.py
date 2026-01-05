"""Test glob parsing with problematic format."""

import sys
sys.path.insert(0, '.')

from app.core.actions.parsing.parser import SimpleActionParser

# 可能导致问题的格式
test_cases = [
    # Case 1: 标准格式
    """
<glob>
pattern: "*.py"
path: app/core/
</glob>
""",
    
    # Case 2: 没有引号
    """
<glob>
pattern: *.py
path: app/core/
</glob>
""",
    
    # Case 3: 可能导致问题的格式（标签和 key 粘在一起）
    """
<glob>pattern: "*.py"
path: app/core/
</glob>
""",
]

parser = SimpleActionParser()

for i, test in enumerate(test_cases, 1):
    print(f"\n{'='*60}")
    print(f"Test Case {i}")
    print(f"{'='*60}")
    print(f"Input:\n{test}")
    
    actions, errors = parser.parse(test)
    
    if errors:
        print(f"\n❌ Errors: {errors}")
    
    if actions:
        action = actions[0]
        print(f"\n✅ Parsed successfully")
        print(f"   Type: {type(action).__name__}")
        print(f"   pattern: {action.pattern}")
        print(f"   path: {action.path}")
    else:
        print(f"\n❌ No actions parsed")


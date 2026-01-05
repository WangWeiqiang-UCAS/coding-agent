"""Built-in task templates."""

TEMPLATES = {
    "refactor": "分析 {file} 的代码结构，提出重构建议，并生成重构后的代码",
    "test": "为 {file} 中的函数生成单元测试，保存到 tests/ 目录",
    "doc": "为 {file} 生成详细的文档字符串和 README",
    "fix": "分析 {file} 中的潜在 bug 并修复",
    "optimize": "优化 {file} 的性能，减少时间复杂度",
    "security": "检查 {file} 的安全问题（SQL 注入、XSS 等）并修复",
}


def get_template(name: str, **kwargs) -> str:
    """Get task template.
    
    Args:
        name: Template name
        **kwargs: Template variables
        
    Returns:
        Formatted instruction
    """
    template = TEMPLATES.get(name)
    if not template:
        available = ", ".join(TEMPLATES.keys())
        raise ValueError(f"Unknown template: {name}. Available: {available}")
    
    return template.format(**kwargs)

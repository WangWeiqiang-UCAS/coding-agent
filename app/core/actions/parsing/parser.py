import re
import logging
from typing import List, Tuple, Optional
import yaml
from pydantic import ValidationError

from app.core.actions.entities.actions import Action, ACTION_TYPE_MAP, FinishAction

logger = logging.getLogger(__name__)

class SimpleActionParser:
    """Parse actions from LLM output using XML-like tags."""
    
    def __init__(self):
        # 正则表达式：匹配 <tag>content</tag>
        # 优化：
        # 1. (?i) 开启大小写不敏感（虽然 xml 通常大小写敏感，但 LLM 容易混淆）
        # 2. \1 确保闭合标签与开始标签一致
        self.action_pattern = re.compile(
            r'<(\w+)>(.*?)</\1>', 
            re.DOTALL | re.IGNORECASE
        )
    
    def parse(self, llm_output: str) -> Tuple[List[Action], List[str]]:
        """Parse actions from LLM output.
        
        Returns:
            Tuple of (actions, errors)
        """
        actions = []
        errors = []
        
        # 提取所有 <tag>content</tag> 块
        matches = self.action_pattern.findall(llm_output)
        
        if not matches:
            logger.debug("No action tags found in LLM output")
            return [], []
        
        logger.debug(f"Found {len(matches)} action tags")
        
        for tag_name, content in matches:
            # 统一转为小写处理，处理例如 <Bash>...</Bash> 的情况
            tag_name = tag_name.lower()
            
            try:
                action = self._parse_single_action(tag_name, content)
                if action:
                    actions.append(action)
                    logger.debug(f"Successfully parsed {tag_name} action")
            except ValidationError as e:
                # 专门捕获 Pydantic 验证错误，简化错误信息反馈给 LLM
                error_msg = f"Validation error in <{tag_name}>: {self._format_pydantic_error(e)}"
                errors.append(error_msg)
                logger.warning(error_msg)
            except Exception as e:
                # 捕获 YAML 解析或其他错误
                error_msg = f"Failed to parse <{tag_name}> content: {str(e)}"
                errors.append(error_msg)
                logger.warning(error_msg)
        
        return actions, errors
    
    def _parse_single_action(self, tag_name: str, content: str) -> Optional[Action]:
        """Parse a single action from tag name and content."""
        
        # 查找对应的 Action 类
        action_class = ACTION_TYPE_MAP.get(tag_name)
        
        if not action_class:
            logger.debug(f"Unknown action tag: {tag_name}")
            return None
        
        # 清理内容
        content = content.strip()

        # --- 新增：清理 LLM 可能生成的 Markdown 代码块标记 ---
        # 很多 LLM 会输出:
        # <bash>
        # ```bash
        # ls -la
        # ```
        # </bash>
        if content.startswith("```"):
            lines = content.splitlines()
            # 如果第一行是 ```yaml 或 ```bash，去掉它
            if lines[0].startswith("```"):
                lines = lines[1:]
            # 如果最后一行是 ```，去掉它
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            content = "\n".join(lines).strip()
        # --------------------------------------------------
        
        # 特殊处理：finish action 的 content 通常是纯文本 message，不是 YAML
        if action_class == FinishAction:
            # 如果 FinishAction 定义接受 message 参数
            return FinishAction(message=content)
        
        # 其他 action：解析为 YAML
        try:
            # 解析 YAML
            params = yaml.safe_load(content)
            
            # 处理空内容情况
            if params is None:
                params = {}
            
            # 如果解析结果不是字典 (例如 LLM 直接输出了命令字符串 'ls -la')
            # 尝试将其包装为默认字段（假设 Action 有个 content 字段，或者你需要根据 Action 类型特殊处理）
            if not isinstance(params, dict):
                # 这里根据你的 BashAction 定义，可能需要改为 cmd=str(params)
                # 这是一个假设的兜底策略
                if tag_name == 'bash': 
                     params = {"cmd": str(params)}
                else:
                     params = {"content": str(params)}
            
            # 使用 Pydantic 验证和构造
            # 这里会抛出 ValidationError，由上层捕获
            action = action_class(**params)
            return action
            
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML format: {e}")

    def _format_pydantic_error(self, e: ValidationError) -> str:
        """Helper to format Pydantic errors into a concise string."""
        # 将多行的复杂错误转换为简单的 "Field 'x': error message" 格式
        messages = []
        for err in e.errors():
            loc = ".".join(str(l) for l in err['loc'])
            msg = err['msg']
            messages.append(f"Field '{loc}': {msg}")
        return "; ".join(messages)

# 便捷函数保持不变
def parse_actions(llm_output: str) -> Tuple[List[Action], List[str]]:
    parser = SimpleActionParser()
    return parser.parse(llm_output)
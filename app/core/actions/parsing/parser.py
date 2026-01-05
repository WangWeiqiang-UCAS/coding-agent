"""Robust action parser with strict format handling."""

import re
import logging
from typing import List, Tuple, Optional

from app.core.actions.entities. actions import Action, ACTION_TYPE_MAP, FinishAction

logger = logging.getLogger(__name__)


class SimpleActionParser:
    """Parse actions from LLM output."""
    
    def __init__(self):
        # Match action tags with content between them
        self.action_pattern = re.compile(r'<(\w+)>\s*(.*?)\s*</\1>', re.DOTALL)
    
    def parse(self, llm_output: str) -> Tuple[List[Action], List[str]]:
        """Parse actions from LLM output."""
        actions = []
        errors = []
        
        matches = self.action_pattern.findall(llm_output)
        
        if not matches:
            return [], []
        
        for tag_name, content in matches:
            tag_name = tag_name.lower()
            
            try:
                action = self._parse_single_action(tag_name, content)
                if action:
                    actions.append(action)
                    logger.debug(f"✅ Parsed {tag_name} action")
            except Exception as e:
                error_msg = f"Failed to parse <{tag_name}>: {str(e)}"
                errors.append(error_msg)
                logger.warning(error_msg)
        
        return actions, errors
    
    def _parse_single_action(self, tag_name: str, content: str) -> Optional[Action]:
        """Parse a single action."""
        action_class = ACTION_TYPE_MAP.get(tag_name)
        
        if not action_class:
            logger.debug(f"Unknown action:  {tag_name}")
            return None
        
        # Special handling for finish action
        if action_class == FinishAction:
            return FinishAction(message=content. strip())
        
        content = content.strip()
        params = self._parse_params(content)
        
        if not isinstance(params, dict):
            params = {"content": str(params)}
        
        logger.debug(f"Parsed params for {tag_name}: {list(params.keys())}")
        
        return action_class(**params)
    
    def _parse_params(self, content: str) -> dict:
        """Parse YAML-style parameters with robust multiline support."""
        lines = content.split('\n')
        params = {}
        i = 0
        
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()
            
            # Skip empty lines and comments
            if not stripped or stripped.startswith('#'):
                i += 1
                continue
            
            # Look for key:  value pattern
            if ':' not in line:
                i += 1
                continue
            
            # Split on first colon
            colon_idx = line.index(':')
            key = line[: colon_idx].strip()
            rest = line[colon_idx + 1:].strip()
            
            # Remove quotes from key (handles weird cases)
            key = key.strip('"\'')
            
            # Case 1: Explicit multiline with pipe |
            if rest == '|':
                i += 1
                content_lines = []
                base_indent = None
                
                while i < len(lines):
                    next_line = lines[i]
                    
                    # Stop at next key (unindented line with colon)
                    if next_line and not next_line[0].isspace() and ': ' in next_line:
                        break
                    
                    # Determine base indentation from first content line
                    if base_indent is None and next_line. strip():
                        base_indent = len(next_line) - len(next_line.lstrip())
                    
                    # Strip base indentation
                    if base_indent is not None:
                        if len(next_line) >= base_indent:
                            content_lines.append(next_line[base_indent:])
                        else:
                            content_lines.append(next_line. lstrip())
                    
                    i += 1
                
                params[key] = '\n'.join(content_lines).rstrip()
            
            # Case 2: Empty value - collect following lines
            elif rest == '':
                i += 1
                content_lines = []
                
                while i < len(lines):
                    next_line = lines[i]
                    next_stripped = next_line.strip()
                    
                    # Stop at next key
                    if next_stripped and ':' in next_line and not next_line[0].isspace():
                        break
                    
                    # Add line content
                    if next_stripped: 
                        content_lines.append(next_stripped)
                    
                    i += 1
                
                params[key] = '\n'.join(content_lines)
            
            # Case 3: Value on same line
            else:
                # Remove quotes if present
                value = rest
                if (value.startswith('"') and value.endswith('"')) or \
                   (value.startswith("'") and value.endswith("'")):
                    value = value[1:-1]
                
                # Check if there are more lines belonging to this value
                value_lines = [value]
                i += 1
                
                while i < len(lines):
                    next_line = lines[i]
                    next_stripped = next_line.strip()
                    
                    # Empty line - skip but continue
                    if not next_stripped: 
                        i += 1
                        continue
                    
                    # Next key - stop
                    if ':' in next_line and not next_line[0].isspace():
                        break
                    
                    # More content for current value
                    value_lines.append(next_stripped)
                    i += 1
                
                params[key] = '\n'.join(value_lines)
        
        return params

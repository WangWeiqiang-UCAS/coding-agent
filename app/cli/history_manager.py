
"""Task history manager using local JSON storage."""

import json
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Dict
import os


class HistoryManager:
    """Manages task execution history."""
    
    def __init__(self, history_file: Optional[str] = None):
        """Initialize history manager.
        
        Args:
            history_file: Path to history file (default: ~/.coding_agent/history.json)
        """
        if history_file:
            self. history_file = Path(history_file)
        else:
            # 使用用户主目录
            home = Path.home()
            self.history_dir = home / ".coding_agent"
            self.history_dir.mkdir(exist_ok=True)
            self.history_file = self.history_dir / "history.json"
        
        # 确保文件存在
        if not self.history_file.exists():
            self.history_file.write_text("[]")
    
    def save(self, instruction: str, result: dict):
        """Save task result to history.
        
        Args:
            instruction: Task instruction
            result:  Execution result
        """
        history = self._load()
        
        # 创建历史记录
        record = {
            "task_id": result. get("task_id", "unknown"),
            "instruction": instruction,
            "completed": result["completed"],
            "finish_message": result["finish_message"],
            "turns_executed": result["turns_executed"],
            "elapsed_time": result["elapsed_time"],
            "timestamp": datetime. now().isoformat(),
        }
        
        # 添加到历史（最新在前）
        history.insert(0, record)
        
        # 限制历史数量（保留最近 100 条）
        history = history[:  100]
        
        self._save(history)
    
    def list(self, limit:  int = 10) -> List[Dict]:
        """Get recent task history.
        
        Args:
            limit: Number of tasks to return
            
        Returns: 
            List of task records
        """
        history = self._load()
        return history[: limit]
    
    def get(self, task_id: str) -> Optional[Dict]:
        """Get specific task by ID.
        
        Args:
            task_id: Task identifier
            
        Returns:
            Task record or None
        """
        history = self._load()
        
        for record in history:
            if record["task_id"]. startswith(task_id):
                return record
        
        return None
    
    def clear(self):
        """Clear all history."""
        self._save([])
    
    def _load(self) -> List[Dict]:
        """Load history from file."""
        try:
            with open(self.history_file, 'r') as f:
                return json.load(f)
        except Exception: 
            return []
    
    def _save(self, history:  List[Dict]):
        """Save history to file."""
        with open(self.history_file, 'w') as f:
            json.dump(history, f, indent=2)

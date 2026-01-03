"""Core action definitions."""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field


# ============================================================
# 基础动作类
# ============================================================

class Action(BaseModel):
    """Base class for all actions."""
    pass


# ============================================================
# 文件操作动作
# ============================================================

class ReadAction(Action):
    """Read file content. 
    
    Example:
        <read>
        file_path: src/main.py
        offset: 10
        limit: 50
        </read>
    """
    file_path: str = Field(..., description="Path to the file to read")
    offset: Optional[int] = Field(None, description="Start line number (1-indexed)")
    limit: Optional[int] = Field(None, description="Number of lines to read")
    
    class Config:
        json_schema_extra = {
            "example": {
                "file_path": "src/main.py",
                "offset": 10,
                "limit": 50
            }
        }


class WriteAction(Action):
    """Write content to a file.
    
    Example:
        <write>
        file_path: src/new_file.py
        content: |
          def hello():
              print("Hello, World!")
        </write>
    """
    file_path: str = Field(..., description="Path to the file to write")
    content: str = Field(..., description="Content to write to the file")


class EditAction(Action):
    """Edit file by string replacement.
    
    Example:
        <edit>
        file_path: src/main.py
        old_string: "def old_function():"
        new_string: "def new_function():"
        </edit>
    """
    file_path: str = Field(..., description="Path to the file to edit")
    old_string: str = Field(..., description="String to find")
    new_string: str = Field(..., description="Replacement string")
    replace_all: bool = Field(True, description="Replace all occurrences")


# ============================================================
# 执行动作
# ============================================================

class BashAction(Action):
    """Execute a bash command.
    
    Example:
        <bash>
        cmd: ls -la /workspace
        timeout_secs: 30
        </bash>
    """
    cmd:  str = Field(..., description="Command to execute")
    timeout_secs: int = Field(300, description="Timeout in seconds")


class FinishAction(Action):
    """Mark task as complete.
    
    Example:
        <finish>
        Task completed successfully!  All tests are passing.
        </finish>
    """
    message: str = Field(..., description="Completion message")


# ============================================================
# 搜索动作
# ============================================================

class GrepAction(Action):
    """Search for pattern in files.
    
    Example:
        <grep>
        pattern:  "def.*login"
        path: src/
        </grep>
    """
    pattern: str = Field(..., description="Regex pattern to search")
    path: str = Field(".", description="Directory to search in")
    include:  Optional[str] = Field(None, description="File pattern to include (e.g., '*.py')")


class GlobAction(Action):
    """Find files matching pattern.
    
    Example:
        <glob>
        pattern:  "**/*.py"
        path: src/
        </glob>
    """
    pattern: str = Field(..., description="Glob pattern (e.g., '**/*.py')")
    path: str = Field(".", description="Base directory")


# ============================================================
# 多智能体动作
# ============================================================

class TaskCreateAction(Action):
    """Create a task for a subagent.
    
    Example:
        <task_create>
        agent_type: explorer
        title:  Investigate API structure
        description: |
          Find all API endpoints in the codebase. 
          Report the following:
          1. Endpoint paths
          2. HTTP methods
          3. Request/response schemas
        max_turns: 15
        context_refs: 
          - ctx_database_schema
        auto_launch: true
        </task_create>
    """
    agent_type:  Literal["explorer", "coder"] = Field(..., description="Type of agent")
    title: str = Field(..., description="Task title")
    description: str = Field(..., description="Detailed task description")
    max_turns: int = Field(20, description="Maximum turns allowed")
    context_refs: List[str] = Field(default_factory=list, description="Context IDs to provide")
    context_bootstrap: List[dict] = Field(default_factory=list, description="Bootstrap file info")
    auto_launch: bool = Field(True, description="Automatically launch after creation")


class LaunchSubagentAction(Action):
    """Launch a subagent to execute a task.
    
    Example:
        <launch_subagent>
        task_id: task_001
        </launch_subagent>
    """
    task_id: str = Field(..., description="ID of the task to execute")


class ReportAction(Action):
    """Report task results (used by subagents).
    
    Example:
        <report>
        contexts:
          - id: api_endpoints
            content: |
              Found 3 API endpoints:
              - POST /api/login
              - GET /api/users
              - DELETE /api/users/: id
        comments:  |
          Investigation complete. All endpoints use JWT authentication.
        </report>
    """
    contexts: List[dict] = Field(default_factory=list, description="Discovered contexts")
    comments: str = Field(... , description="Summary and recommendations")


# ============================================================
# 动作类型映射表
# ============================================================

ACTION_TYPE_MAP = {
    # 文件操作
    "read":  ReadAction,
    "file":  ReadAction,  # 别名
    "write": WriteAction,
    "edit": EditAction,
    
    # 执行
    "bash": BashAction,
    "finish": FinishAction,
    
    # 搜索
    "grep": GrepAction,
    "search": GrepAction,  # 别名
    "glob": GlobAction,
    "find": GlobAction,  # 别名
    
    # 多智能体
    "task_create": TaskCreateAction,
    "launch_subagent":  LaunchSubagentAction,
    "report": ReportAction,
}

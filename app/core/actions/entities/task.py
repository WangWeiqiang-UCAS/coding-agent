"""Task entity models."""

from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
import time


class TaskStatus(str, Enum):
    """Task execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Task(BaseModel):
    """A task to be executed by a subagent."""
    
    task_id: str = Field(..., description="Unique task identifier")
    agent_type: str = Field(..., description="Type of agent (explorer/coder)")
    title: str = Field(..., description="Task title")
    description: str = Field(..., description="Detailed task description")
    status: TaskStatus = Field(default=TaskStatus.PENDING, description="Task status")
    max_turns: int = Field(default=20, description="Maximum turns allowed")
    context_refs: List[str] = Field(default_factory=list, description="Context IDs to provide")
    context_bootstrap: List[dict] = Field(default_factory=list, description="Bootstrap file info")
    created_at: float = Field(default_factory=time.time, description="Creation timestamp")
    updated_at: float = Field(default_factory=time.time, description="Last update timestamp")
    completed_at: Optional[float] = Field(None, description="Completion timestamp")
    result: Optional[Dict] = Field(None, description="Task execution result")
    error: Optional[str] = Field(None, description="Error message if failed")
    
    class Config: 
        json_schema_extra = {
            "example": {
                "task_id": "task_001",
                "agent_type": "explorer",
                "title": "Investigate API structure",
                "description": "Analyze the codebase and identify all API endpoints",
                "status": "pending",
                "max_turns": 20,
                "context_refs": [],
                "context_bootstrap": [],
                "created_at": 1234567890.123,
                "updated_at": 1234567890.123
            }
        }
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return self.model_dump()
    
    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        """Create from dictionary."""
        # Convert status string to enum if needed
        if isinstance(data.get("status"), str):
            data["status"] = TaskStatus(data["status"])
        return cls(**data)


class SubagentTask(BaseModel):
    """Task specification for subagent execution."""
    
    agent_type: str = Field(..., description="Type of agent (explorer/coder)")
    title: str = Field(..., description="Task title")
    description: str = Field(..., description="Task description")
    max_turns: int = Field(default=20, description="Maximum turns")
    ctx_store_ctxts: Dict[str, str] = Field(default_factory=dict, description="Resolved contexts")
    bootstrap_ctxts: List[Dict[str, str]] = Field(default_factory=list, description="Bootstrap files")
    
    class Config:
        json_schema_extra = {
            "example": {
                "agent_type": "coder",
                "title": "Fix bug in auth module",
                "description": "Fix the authentication logic that allows unauthorized access",
                "max_turns":  15,
                "ctx_store_ctxts": {
                    "auth_structure": "The auth module is in src/auth. py..."
                },
                "bootstrap_ctxts": [
                    {"path": "src/auth.py", "content": ".. .", "reason": "Main auth file"}
                ]
            }
        }
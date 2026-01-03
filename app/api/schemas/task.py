
"""Task-related schemas for API."""

from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum


class TaskStatusEnum(str, Enum):
    """Task status for API responses."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskCreateRequest(BaseModel):
    """Request to create a new task."""
    instruction: str = Field(..., description="Task instruction for the agent", min_length=1)
    max_turns: int = Field(default=50, description="Maximum turns", ge=1, le=200)
    
    class Config:
        json_schema_extra = {
            "example": {
                "instruction": "Fix the login bug in the authentication module",
                "max_turns":  50
            }
        }


class TaskResponse(BaseModel):
    """Response after creating a task."""
    task_id: str = Field(..., description="Unique task identifier")
    status: TaskStatusEnum = Field(... , description="Current task status")
    instruction: str = Field(..., description="Task instruction")
    created_at: float = Field(..., description="Creation timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "task_abc12345",
                "status": "pending",
                "instruction": "Fix the login bug",
                "created_at": 1234567890.123
            }
        }


class TaskDetailResponse(TaskResponse):
    """Detailed task information."""
    updated_at: float = Field(..., description="Last update timestamp")
    completed_at: Optional[float] = Field(None, description="Completion timestamp")
    result: Optional[dict] = Field(None, description="Task result")
    error: Optional[str] = Field(None, description="Error message if failed")


class ContextResponse(BaseModel):
    """Context information."""
    id: str
    content: str
    reported_by: str
    task_id: Optional[str]
    timestamp: float


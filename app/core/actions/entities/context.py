"""Context entity for storing discovered information."""

from pydantic import BaseModel, Field
from typing import Optional
import time


class Context(BaseModel):
    """A piece of discovered information or knowledge."""
    
    id: str = Field(..., description="Unique context identifier")
    content: str = Field(..., description="Context content")
    reported_by: str = Field(..., description="Agent ID that reported this context")
    task_id: Optional[str] = Field(None, description="Associated task ID")
    timestamp: float = Field(default_factory=time.time, description="Creation timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "api_structure",
                "content": "The API has 3 main endpoints: /users, /posts, /comments",
                "reported_by": "explorer-abc123",
                "task_id": "task_001",
                "timestamp": 1234567890.123
            }
        }
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return self.model_dump()
    
    @classmethod
    def from_dict(cls, data: dict) -> "Context":
        """Create from dictionary."""
        return cls(**data)
"""Common response schemas."""

from pydantic import BaseModel, Field
from typing import Optional, Any


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(..., description="Service status")
    redis:  str = Field(..., description="Redis connection status")
    timestamp: float = Field(..., description="Check timestamp")


class ErrorResponse(BaseModel):
    """Error response."""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    task_id: Optional[str] = Field(None, description="Related task ID")

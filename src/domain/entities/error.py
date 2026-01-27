from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

class ErrorResponse(BaseModel):
    error_code: str = Field(description="Semantic error identifier (e.g., EMPLOYEE_NOT_FOUND, UNAUTHORIZED)")
    message: str = Field(description="Human-readable explanation of the error")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Contextual data about the error (e.g., invalid fields, resource IDs)")
    retry_allowed: bool = Field(default=False, description="Hint to the client if the operation might succeed on retry")

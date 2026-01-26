from typing import Optional, Dict, Any
from pydantic import BaseModel

class ErrorResponse(BaseModel):
    error_code: str
    message: str
    details: Optional[Dict[str, Any]] = None

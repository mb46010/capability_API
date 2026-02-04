import httpx
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

def map_backend_error(e: Exception) -> str:
    if isinstance(e, httpx.HTTPStatusError):
        status_code = e.response.status_code
        try:
            error_data = e.response.json()
            message = error_data.get("message", e.response.text)
            error_code = error_data.get("error_code", str(status_code))
        except:
            message = e.response.text
            error_code = str(status_code)

        if status_code == 401:
            if "mfa" in message.lower() or error_code == "MFA_REQUIRED":
                return "MFA_REQUIRED: This action requires multi-factor authentication."
            return "UNAUTHORIZED: Session expired or invalid token."
        
        if status_code == 403:
            return f"FORBIDDEN: You do not have permission for this action. ({message})"
        
        if status_code == 404:
            return f"NOT_FOUND: The requested resource was not found. ({message})"
        
        if status_code >= 500:
            # Sanitization for 5xx errors (Constitution/Spec requirement)
            logger.error(f"Internal Backend Error: {status_code} - {e.response.text}")
            return "INTERNAL_ERROR: An unexpected error occurred in the backend. Please try again later."
            
        return f"ERROR ({error_code}): {message}"
    
    if isinstance(e, httpx.ConnectError):
        return "SERVICE_UNAVAILABLE: Could not connect to the HR backend. Please check if the Capability API is running."

    logger.error(f"Unhandled error: {str(e)}")
    return "INTERNAL_ERROR: An unexpected error occurred."

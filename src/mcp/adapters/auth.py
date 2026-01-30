import jwt
import logging
from typing import Optional, List
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class PrincipalContext(BaseModel):
    subject: str
    principal_type: str
    groups: List[str] = []
    mfa_verified: bool = False
    raw_token: str

def extract_principal(token: str) -> Optional[PrincipalContext]:
    try:
        # Decode without verification - backend will verify. 
        # We just need the claims for tool discovery logic.
        payload = jwt.decode(token, options={"verify_signature": False})
        
        amr = payload.get("amr", [])
        mfa_verified = "mfa" in amr
        
        return PrincipalContext(
            subject=payload.get("sub", "unknown"),
            principal_type=payload.get("principal_type", "HUMAN"),
            groups=payload.get("groups", []),
            mfa_verified=mfa_verified,
            raw_token=token
        )
    except Exception as e:
        logger.error(f"Failed to decode token: {str(e)}")
        return None

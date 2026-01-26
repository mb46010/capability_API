from fastapi import Header, HTTPException, Depends
from typing import Optional

async def get_current_principal(
    x_principal_id: Optional[str] = Header(None, alias="X-Principal-ID"),
    x_principal_type: Optional[str] = Header(None, alias="X-Principal-Type"),
    x_principal_groups: Optional[str] = Header(None, alias="X-Principal-Groups"),
    authorization: Optional[str] = Header(None)
):
    """
    Mock Auth dependency. In a real world, this would validate the JWT in 'Authorization' header
    against Okta JWKS.
    For MVP/Dev, we trust the injected Headers (simulating an upstream Gateway or Test Client).
    """
    
    # 1. If we are in local/test environment, allow header injection
    # In PROD, we must validate the JWT.
    
    # Simple check: require at least a Principal ID
    if not x_principal_id:
         # Fallback: Check if Authorization header is present (Mock)
         if not authorization:
             raise HTTPException(status_code=401, detail="Missing authentication")
         
         # Mock extracting from token
         # For now, just fail if no explicit headers are provided to force client to identify
         raise HTTPException(status_code=401, detail="Missing Principal Identity Headers")

    return {
        "id": x_principal_id,
        "type": x_principal_type or "HUMAN",
        "groups": x_principal_groups.split(",") if x_principal_groups else []
    }

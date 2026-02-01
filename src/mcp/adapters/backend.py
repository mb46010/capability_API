import httpx
import logging
from typing import Dict, Any, Optional
from src.mcp.lib.config import settings

logger = logging.getLogger(__name__)

class CapabilityAPIClient:
    def __init__(self, base_url: str = settings.CAPABILITY_API_BASE_URL):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(timeout=30.0)

    async def call_action(self, domain: str, action: str, parameters: Dict[str, Any], token: str) -> Dict[str, Any]:
        url = f"{self.base_url}/actions/{domain}/{action}"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "X-Acting-Through": "mcp-server"
        }
        payload = {"parameters": parameters}
        
        try:
            response = await self.client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Backend error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Connection error: {str(e)}")
            raise

    async def close(self):
        await self.client.aclose()

backend_client = CapabilityAPIClient()

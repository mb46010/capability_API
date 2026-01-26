from abc import ABC, abstractmethod
from typing import Dict, Any

class ConnectorPort(ABC):
    @abstractmethod
    async def execute(self, action: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute an action against the external system.
        Returns the raw data payload.
        """
        pass

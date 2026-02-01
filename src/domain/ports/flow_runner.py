from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class FlowRunnerPort(ABC):
    @abstractmethod
    async def start_flow(
        self,
        domain: str,
        flow: str,
        params: Dict[str, Any],
        principal_id: str,
    ) -> str:
        """Starts a flow execution and returns the Execution ID."""
        pass

    @abstractmethod
    async def get_flow_status(self, flow_id: str) -> Optional[Dict[str, Any]]:
        """Returns the raw status dictionary of the flow execution."""
        pass

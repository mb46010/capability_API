from typing import Dict, Any
from src.domain.ports.connector import ConnectorPort

class MockConnectorAdapter(ConnectorPort):
    async def execute(self, action: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        # Simulate some latency or processing
        if action == "get_employee":
            return {
                "id": parameters.get("employee_id"),
                "name": "John Doe",
                "role": "Engineer",
                "email": "john.doe@example.com" # Sensitive! PII masking will be needed later
            }
        
        return {"status": "executed", "action": action, "params": parameters}

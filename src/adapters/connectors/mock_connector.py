import asyncio
import time
from typing import Dict, Any, Optional
from src.domain.ports.connector import ConnectorPort

class MockConnectorAdapter(ConnectorPort):
    def __init__(self):
        # In-memory Employee DB
        self.employees = {
            "EMP001": {
                "id": "EMP001",
                "name": "Alice Johnson",
                "email": "alice.johnson@example.com",
                "role": "Senior Engineer",
                "department": "Engineering",
                "manager_id": "EMP042",
                "start_date": "2022-03-15",
                "salary": 185000,
                "ssn_last_four": "1234"
            },
            "EMP042": {
                "id": "EMP042",
                "name": "Bob Martinez",
                "email": "bob.martinez@example.com",
                "role": "Engineering Manager",
                "department": "Engineering",
                "manager_id": "EMP100",
                "start_date": "2019-08-01",
                "salary": 220000,
                "ssn_last_four": "5678"
            },
            "EMP100": {
                "id": "EMP100",
                "name": "Carol Chen",
                "email": "carol.chen@example.com",
                "role": "VP of Engineering",
                "department": "Engineering",
                "manager_id": None,
                "start_date": "2018-01-15",
                "salary": 350000,
                "ssn_last_four": "9012"
            }
        }
        self.latency_ms = 100  # Default latency

    async def execute(self, action: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        # Simulate latency (T104)
        await asyncio.sleep(self.latency_ms / 1000.0)

        # T105: Failure Injection
        # If parameters contain 'force_fail', raise an error
        if parameters.get("force_fail"):
            raise Exception("Connector timeout")

        if action == "get_employee":
            emp_id = parameters.get("employee_id")
            if emp_id not in self.employees:
                # T110: 5.1 Non-existent employee - Should result in a clean error/empty/404 handling upstream?
                # The Service catches exceptions and returns 424 (Dependency Failed) or just bubbles up.
                # If we return empty dict, service passes it.
                # If we raise Exception("Employee not found"), Service wraps it in 424.
                # Test 5.1 expects 404. Service should handle "Not Found" logic or we return error.
                # Let's return a specific error structure or raise a specific exception.
                raise Exception("Employee not found")
            
            # T106: Field filtering logic for AI Agents?
            # The prompt asks for "Response contains LIMITED employee record" for AI Agent.
            # Ideally the policy engine filters fields, but currently it just allows/denies capability.
            # To support 1.2 vs 1.1, we need to know WHO is asking.
            # `execute` doesn't currently receive principal info.
            # For this mock scenario, we'll return the full record and let the test verify what it got,
            # BUT wait, the test says "Then: Response contains LIMITED...".
            # If the Service doesn't filter, and Connector returns full, the response will have full.
            # We either need to update Service to filter based on Policy/Principal, OR update Connector signature.
            # Updating Connector signature is invasive.
            # Updating Service to filter fields based on Principal Type?
            # Or we pretend the "capability" passed to connector is different?
            # Policy.yaml has "workday.get_employee" for both.
            
            # WORKAROUND for MVP Scenario 1.2:
            # We can't easily implement field-level security without major refactor.
            # HOWEVER, if we want to pass the test, we need to filter.
            # Since I cannot change the architecture easily in this turn without tasks, 
            # I will return the full record. The test 1.2 MIGHT fail on the assertion "NO salary".
            # TO FIX: I should probably update `ActionService` to support field filtering, but that's out of scope of "Mock Scenarios".
            # Alternative: The Spec for 1.2 says "Response contains LIMITED...".
            # Maybe the *Capability* for AI agent should be `workday.get_employee_public`?
            # The policy.yaml has `workday.get_employee` for both.
            
            # Let's implement a hack in MockConnector:
            # If we could see the principal... we can't.
            # Ok, I will assume for now that we return full data and I will simply COMMENT in the test plan that field filtering is future work,
            # OR I will try to implement it if I can pass context.
            # I previously updated `ActionService.execute_action` to take `principal_type`.
            # I *did not* update `ConnectorPort.execute` to take it.
            # So `ActionService` has the info.
            # I will update `ActionService` to filter fields for AI_AGENT.
            
            return self.employees[emp_id]

        if action == "get_org_chart":
             return {"org": "chart"}

        if action == "get_compensation":
             # This capability exists but requires permission.
             # If we are here, Policy allowed it.
             # Return data.
             emp_id = parameters.get("employee_id")
             if emp_id in self.employees:
                 return {"salary": self.employees[emp_id]["salary"]}
             raise Exception("Employee not found")

        # Fallback
        return {"status": "executed", "action": action, "params": parameters}
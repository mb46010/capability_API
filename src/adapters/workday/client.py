import asyncio
import random
import time
from typing import Dict, Any, Optional
from src.domain.ports.connector import ConnectorPort
from src.adapters.workday.config import WorkdaySimulationConfig
from src.adapters.workday.loader import FixtureLoader
from src.adapters.workday.exceptions import (
    WorkdayError, ConnectorTimeoutError, ConnectorUnavailableError, RateLimitedError
)

from src.adapters.workday.services.hcm import WorkdayHCMService
from src.adapters.workday.services.time import WorkdayTimeService
from src.adapters.workday.services.payroll import WorkdayPayrollService

class WorkdaySimulator(ConnectorPort):
    def __init__(self, config: Optional[WorkdaySimulationConfig] = None):
        self.config = config or WorkdaySimulationConfig()
        self.loader = FixtureLoader(self.config.fixture_path)
        # We store mutable state in memory as requested
        self.employees = self.loader.employees
        self.departments = self.loader.departments
        self.balances = self.loader.balances
        self.requests = self.loader.requests
        self.compensation = self.loader.compensation
        self.statements = self.loader.statements
        
        # Services
        self.hcm_service = WorkdayHCMService(self)
        self.time_service = WorkdayTimeService(self)
        self.payroll_service = WorkdayPayrollService(self)

        # Validate on startup so you catch fixture problems early
        self._validate_fixtures()

    def _validate_fixtures(self):
        """Quick sanity checks"""
        assert len(self.employees) > 0, "No employees in fixtures"
        
        # Check manager references are valid
        for emp in self.employees.values():
            if emp.manager:
                assert emp.manager.employee_id in self.employees, \
                    f"Employee {emp.employee_id} references invalid manager {emp.manager.employee_id}"

    def reload(self):
        """Reload fixtures from disk without restarting."""
        self.loader = FixtureLoader(self.config.fixture_path)
        self.employees = self.loader.employees
        self.departments = self.loader.departments
        self.balances = self.loader.balances
        self.requests = self.loader.requests
        self.compensation = self.loader.compensation
        self.statements = self.loader.statements
        self._validate_fixtures()

    async def execute(self, action: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generic entry point for all Workday operations.
        """
        print(f"DEBUG: [WorkdaySimulator] Executing {action} with params: {parameters}")
        # 1. Failure Injection
        self._inject_failure()
        
        # 2. Latency Simulation
        await self._simulate_latency(action)

        # 3. Dispatch
        method_name = action.split(".")[-1] if "." in action else action
        
        # Try finding the method on services or self
        handler = (
            getattr(self.hcm_service, method_name, None) or
            getattr(self.time_service, method_name, None) or
            getattr(self.payroll_service, method_name, None) or
            getattr(self, f"_{method_name}", None)
        )
            
        if not handler:
            raise WorkdayError(
                message=f"Action '{action}' not implemented in simulator. Check capability mapping.",
                error_code="NOT_IMPLEMENTED",
                details={"hint": f"Try implementing _{method_name} in a service class."}
            )
            
        try:
            result = await handler(parameters)
            print(f"DEBUG: [WorkdaySimulator] {action} returned success")
            return result
        except Exception as e:
            print(f"DEBUG: [WorkdaySimulator] {action} failed: {str(e)}")
            raise

    def _inject_failure(self):
        if self.config.failure_rate > 0 and random.random() < self.config.failure_rate:
            raise ConnectorUnavailableError()
        if self.config.timeout_rate > 0 and random.random() < self.config.timeout_rate:
            raise ConnectorTimeoutError()

    async def _simulate_latency(self, action: str):
        base = self.config.base_latency_ms
        variance = self.config.latency_variance_ms
        
        # Write operations are slower
        is_write = any(kw in action for kw in ["update", "terminate", "request", "approve", "cancel"])
        multiplier = self.config.write_latency_multiplier if is_write else 1.0
        
        delay_ms = (base + random.randint(-variance, variance)) * multiplier
        if delay_ms > 0:
            await asyncio.sleep(delay_ms / 1000.0)

    # Placeholder handlers for dispatch
    async def _get_employee(self, params: Dict[str, Any]) -> Dict[str, Any]:
        # Implementation in US1
        return {}

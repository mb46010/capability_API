import asyncio
import random
import time
import logging
from typing import Dict, Any, Optional
from src.domain.ports.connector import ConnectorPort
from src.adapters.workday.config import WorkdaySimulationConfig
from src.adapters.workday.loader import FixtureLoader
from src.adapters.workday.exceptions import (
    WorkdayError, ConnectorTimeoutError, ConnectorUnavailableError, RateLimitedError
)
from src.adapters.filesystem.logger import JSONLLogger

from src.adapters.workday.services.hcm import WorkdayHCMService
from src.adapters.workday.services.time import WorkdayTimeService
from src.adapters.workday.services.payroll import WorkdayPayrollService

logger = logging.getLogger(__name__)

class WorkdaySimulator(ConnectorPort):
    def __init__(self, config: Optional[WorkdaySimulationConfig] = None):
        self.config = config or WorkdaySimulationConfig()
        self.loader = FixtureLoader(self.config.fixture_path)
        self.audit_logger = JSONLLogger()
        
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

        # Idempotency cache (mapping idempotency_key to previous result)
        self._idempotency_cache: Dict[str, Dict[str, Any]] = {}

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
        logger.info("Fixtures reloaded successfully")

    async def execute(self, action: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generic entry point for all Workday operations.
        """
        logger.debug(f"Executing {action} with params: {parameters}")

        # Idempotency Check
        idempotency_key = parameters.get("idempotency_key")
        is_write = any(kw in action for kw in ["update", "terminate", "request", "approve", "cancel"])
        
        if idempotency_key and is_write:
            if idempotency_key in self._idempotency_cache:
                logger.info(f"Idempotent hit for key {idempotency_key}. Returning cached result.")
                return self._idempotency_cache[idempotency_key]

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
            getattr(self, f"_{method_name}", None)
        )
            
        if not handler:
            # Provide a helpful error message with available methods
            available = {
                "hcm": [m for m in dir(self.hcm_service) if not m.startswith("_")],
                "time": [m for m in dir(self.time_service) if not m.startswith("_")],
                "payroll": [m for m in dir(self.payroll_service) if not m.startswith("_")]
            }
            logger.error(f"Action '{action}' not found. Available methods: {available}")
            raise WorkdayError(
                message=f"Action '{action}' not implemented in simulator. Available methods: {available}",
                error_code="NOT_IMPLEMENTED"
            )
            
        try:
            result = await handler(parameters)
            logger.info(f"{action} execution successful")
            
            # Extract token metadata for audit
            token_claims = parameters.get("token_claims")
            
            # Audit Log
            self.audit_logger.log_event(
                event_type=action,
                payload=parameters, # We log the inputs
                actor=parameters.get("principal_id", "unknown"), # Assuming passed in params or context
                token_claims=token_claims
            )

            # Cache result if idempotency key provided
            if idempotency_key and is_write:
                self._idempotency_cache[idempotency_key] = result
            
            return result
        except Exception as e:
            logger.error(f"{action} failed: {str(e)}")
            raise

    def _inject_failure(self):
        if self.config.failure_rate > 0 and random.random() < self.config.failure_rate:
            logger.warning("Injecting failure: ConnectorUnavailableError")
            raise ConnectorUnavailableError()
        if self.config.timeout_rate > 0 and random.random() < self.config.timeout_rate:
            logger.warning("Injecting failure: ConnectorTimeoutError")
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

    # Note: No placeholder handlers needed as dispatch logic dynamically calls services.
    # The dispatch logic in `execute` handles this:
    # handler = (getattr(self.hcm_service, method_name, None) ...)
    
    # We remove the old placeholder to clean up.


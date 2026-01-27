import uuid
from datetime import datetime, date
from typing import Dict, Any, List, Optional
from src.adapters.workday.domain.time_models import TimeOffBalance, TimeOffRequest, TimeOffRequestHistory
from src.adapters.workday.domain.types import TimeOffRequestStatus
from src.adapters.workday.exceptions import (
    EmployeeNotFoundError, RequestNotFoundError, InsufficientBalanceError, 
    InvalidDateRangeError, InvalidApproverError, AlreadyProcessedError
)

class WorkdayTimeService:
    def __init__(self, simulator_state: Any):
        self.state = simulator_state

    async def get_balance(self, params: Dict[str, Any]) -> Dict[str, Any]:
        employee_id = params.get("employee_id")
        if not employee_id or employee_id not in self.state.employees:
            raise EmployeeNotFoundError(employee_id)
            
        balances = self.state.balances.get(employee_id, [])
        return {
            "employee_id": employee_id,
            "as_of_date": str(params.get("as_of_date", date.today())),
            "balances": [b.model_dump() for b in balances]
        }

    async def list_requests(self, params: Dict[str, Any]) -> Dict[str, Any]:
        employee_id = params.get("employee_id")
        # filter by employee_id if provided
        requests = []
        for req in self.state.requests.values():
            if not employee_id or req.employee_id == employee_id:
                requests.append(req.model_dump())
        
        return {
            "employee_id": employee_id,
            "requests": requests,
            "count": len(requests)
        }

    async def get_request(self, params: Dict[str, Any]) -> Dict[str, Any]:
        request_id = params.get("request_id")
        if not request_id or request_id not in self.state.requests:
            raise RequestNotFoundError(request_id)
            
        return self.state.requests[request_id].model_dump()

    async def request(self, params: Dict[str, Any]) -> Dict[str, Any]:
        employee_id = params.get("employee_id")
        if not employee_id or employee_id not in self.state.employees:
            raise EmployeeNotFoundError(employee_id)
            
        # Basic validation
        start_date = params.get("start_date")
        end_date = params.get("end_date")
        if start_date > end_date:
            raise InvalidDateRangeError()
            
        # Check balance
        requested_hours = params.get("hours", 0)
        leave_type = params.get("type")
        
        balances = self.state.balances.get(employee_id, [])
        target_balance = next((b for b in balances if b.type == leave_type), None)
        
        if self.state.config.enforce_balance_check:
            if not target_balance or target_balance.available_hours < requested_hours:
                raise InsufficientBalanceError(
                    available=target_balance.available_hours if target_balance else 0,
                    requested=requested_hours
                )

        # Create request
        request_id = f"TOR-{uuid.uuid4().hex[:8].upper()}"
        emp = self.state.employees[employee_id]
        
        new_request = TimeOffRequest(
            request_id=request_id,
            employee_id=employee_id,
            employee_name=emp.name.display,
            type=leave_type,
            status=TimeOffRequestStatus.PENDING,
            start_date=start_date,
            end_date=end_date,
            hours=requested_hours,
            notes=params.get("notes"),
            submitted_at=datetime.now(),
            history=[TimeOffRequestHistory(
                action="SUBMITTED",
                timestamp=datetime.now(),
                actor=employee_id
            )]
        )
        
        self.state.requests[request_id] = new_request
        
        # Update pending hours
        if target_balance:
            target_balance.pending_hours += requested_hours
            
        return {
            "request_id": request_id,
            "status": "PENDING",
            "submitted_at": str(new_request.submitted_at),
            "estimated_balance_after": target_balance.available_hours - requested_hours if target_balance else 0
        }

    async def approve(self, params: Dict[str, Any]) -> Dict[str, Any]:
        request_id = params.get("request_id")
        approver_id = params.get("approver_id")
        
        if not request_id or request_id not in self.state.requests:
            raise RequestNotFoundError(request_id)
            
        req = self.state.requests[request_id]
        if req.status != TimeOffRequestStatus.PENDING:
            raise AlreadyProcessedError()
            
        # Manager check
        if self.state.config.enforce_manager_chain:
            # We'd need to verify approver is in employee's manager chain
            pass # Simplified for now

        req.status = TimeOffRequestStatus.APPROVED
        req.approved_at = datetime.now()
        req.approved_by = params.get("approver_id") # Should be ManagerRef but we'll adapt
        
        req.history.append(TimeOffRequestHistory(
            action="APPROVED",
            timestamp=datetime.now(),
            actor=approver_id
        ))
        
        # Update balances
        balances = self.state.balances.get(req.employee_id, [])
        target_balance = next((b for b in balances if b.type == req.type), None)
        if target_balance:
            target_balance.available_hours -= req.hours
            target_balance.pending_hours -= req.hours
            target_balance.used_hours += req.hours
            
        return {
            "request_id": request_id,
            "status": "APPROVED",
            "approved_at": str(req.approved_at),
            "approved_by": approver_id
        }

    async def cancel(self, params: Dict[str, Any]) -> Dict[str, Any]:
        request_id = params.get("request_id")
        if not request_id or request_id not in self.state.requests:
            raise RequestNotFoundError(request_id)
            
        req = self.state.requests[request_id]
        if req.status == TimeOffRequestStatus.CANCELLED:
            raise AlreadyProcessedError()
            
        old_status = req.status
        req.status = TimeOffRequestStatus.CANCELLED
        
        # Restore balances if it was approved or pending
        balances = self.state.balances.get(req.employee_id, [])
        target_balance = next((b for b in balances if b.type == req.type), None)
        
        if target_balance:
            if old_status == TimeOffRequestStatus.APPROVED:
                target_balance.available_hours += req.hours
                target_balance.used_hours -= req.hours
            elif old_status == TimeOffRequestStatus.PENDING:
                target_balance.pending_hours -= req.hours
                
        return {
            "request_id": request_id,
            "status": "CANCELLED",
            "cancelled_at": str(datetime.now()),
            "hours_restored": req.hours
        }

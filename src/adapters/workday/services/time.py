from typing import Dict, Any, List
from datetime import datetime, timezone
import uuid
from src.adapters.workday.exceptions import WorkdayError

class WorkdayTimeService:
    def __init__(self, simulator):
        self.simulator = simulator

    async def get_balance(self, params: Dict[str, Any]) -> Dict[str, Any]:
        employee_id = params.get("employee_id")
        principal_id = params.get("principal_id")
        principal_type = params.get("principal_type")

        if not employee_id:
             raise WorkdayError("Missing employee_id", "INVALID_PARAMS")

        # Own Data Enforcement
        if principal_type == "HUMAN" and principal_id and principal_id != employee_id:
             raise WorkdayError(f"Principal {principal_id} cannot access data for {employee_id}", "UNAUTHORIZED")

        balances = self.simulator.balances.get(employee_id)
        if balances is None:
            if employee_id not in self.simulator.employees:
                 raise WorkdayError(f"Employee {employee_id} not found", "EMPLOYEE_NOT_FOUND")
            balances = []

        return {
            "employee_id": employee_id,
            "balances": [b.model_dump() for b in balances]
        }

    async def request(self, params: Dict[str, Any]) -> Dict[str, Any]:
        employee_id = params.get("employee_id")
        req_type = params.get("type")
        start_date = params.get("start_date")
        end_date = params.get("end_date")
        hours = params.get("hours", 0)
        
        principal_id = params.get("principal_id")
        principal_type = params.get("principal_type")

        # 1. Validation
        if not all([employee_id, req_type, start_date, end_date]):
            raise WorkdayError("Missing required fields", "INVALID_PARAMS")
            
        if principal_type == "HUMAN" and principal_id and principal_id != employee_id:
             raise WorkdayError("Cannot request time off for another employee", "UNAUTHORIZED")

        # 2. Check Balance
        balances = self.simulator.balances.get(employee_id, [])
        balance_entry = next((b for b in balances if b.type == req_type), None)
        
        if not balance_entry:
            raise WorkdayError(f"No balance found for type {req_type}", "INVALID_TYPE")
            
        if (balance_entry.available_hours - balance_entry.pending_hours) < hours:
            raise WorkdayError(f"Insufficient {req_type} balance. Requested: {hours}", "INSUFFICIENT_BALANCE")

        # 3. Create Request
        request_id = f"TOR-{uuid.uuid4().hex[:8].upper()}"
        
        # Determine approver (Manager)
        employee = self.simulator.employees.get(employee_id)
        approver = None
        if employee and employee.manager:
             approver = {
                 "employee_id": employee.manager.employee_id,
                 "display_name": employee.manager.display_name
             }

        # Update Balance (Pending)
        balance_entry.pending_hours += hours
        
        # Create Record
        class SimpleRequest:
            def __init__(self, **kwargs):
                self.__dict__.update(kwargs)
        
        record = SimpleRequest(
            request_id=request_id,
            employee_id=employee_id,
            status="PENDING",
            type=req_type,
            start_date=start_date,
            end_date=end_date,
            hours=hours,
            submitted_at=datetime.now(timezone.utc)
        )
        self.simulator.requests[request_id] = record

        return {
            "request_id": request_id,
            "status": "PENDING",
            "submitted_at": datetime.now(timezone.utc).isoformat(),
            "approver": approver,
            "estimated_balance_after": balance_entry.available_hours - hours 
        }

    async def cancel(self, params: Dict[str, Any]) -> Dict[str, Any]:
        request_id = params.get("request_id")
        reason = params.get("reason")
        
        principal_id = params.get("principal_id")
        principal_type = params.get("principal_type")

        if not request_id:
             raise WorkdayError("Missing request_id", "INVALID_PARAMS")

        request = self.simulator.requests.get(request_id)
        if not request:
            raise WorkdayError(f"Request {request_id} not found", "REQUEST_NOT_FOUND")

        # Auth Check
        if principal_type == "HUMAN" and principal_id and principal_id != request.employee_id:
             raise WorkdayError("Cannot cancel another employee's request", "UNAUTHORIZED")

        if request.status == "CANCELLED":
            return {
                "request_id": request_id,
                "status": "CANCELLED",
                "message": "Already cancelled"
            }
            
        balances = self.simulator.balances.get(request.employee_id, [])
        balance_entry = next((b for b in balances if b.type == request.type), None)
        
        hours_restored = 0
        if balance_entry:
            if request.status == "PENDING":
                balance_entry.pending_hours = max(0, balance_entry.pending_hours - request.hours)
                hours_restored = request.hours
            elif request.status == "APPROVED":
                balance_entry.used_hours = max(0, balance_entry.used_hours - request.hours)
                balance_entry.available_hours += request.hours
                hours_restored = request.hours

        request.status = "CANCELLED"
        
        return {
            "request_id": request_id,
            "status": "CANCELLED",
            "cancelled_at": datetime.now(timezone.utc).isoformat(),
            "cancelled_by": principal_id or "system",
            "hours_restored": hours_restored
        }

    async def approve(self, params: Dict[str, Any]) -> Dict[str, Any]:
        request_id = params.get("request_id")
        principal_id = params.get("principal_id")
        principal_type = params.get("principal_type")

        if not request_id:
             raise WorkdayError("Missing request_id", "INVALID_PARAMS")
             
        request = self.simulator.requests.get(request_id)
        if not request:
            raise WorkdayError(f"Request {request_id} not found", "REQUEST_NOT_FOUND")

        employee = self.simulator.employees.get(request.employee_id)
        if not employee:
             raise WorkdayError("Employee for request not found", "DATA_INTEGRITY_ERROR")
             
        if principal_type == "HUMAN":
            if not employee.manager or employee.manager.employee_id != principal_id:
                raise WorkdayError(f"Principal {principal_id} is not the manager of {request.employee_id}", "UNAUTHORIZED")
        
        if request.status != "PENDING":
             raise WorkdayError(f"Request {request_id} is not PENDING (Status: {request.status})", "INVALID_STATE")

        balances = self.simulator.balances.get(request.employee_id, [])
        balance_entry = next((b for b in balances if b.type == request.type), None)
        
        if balance_entry:
            balance_entry.pending_hours = max(0, balance_entry.pending_hours - request.hours)
            balance_entry.available_hours = max(0, balance_entry.available_hours - request.hours)
            balance_entry.used_hours += request.hours

        request.status = "APPROVED"
        
        return {
            "request_id": request_id,
            "status": "APPROVED",
            "approved_at": datetime.now(timezone.utc).isoformat(),
            "approved_by": principal_id
        }
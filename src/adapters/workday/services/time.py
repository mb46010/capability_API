from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, date
import uuid
from src.adapters.workday.exceptions import (
    WorkdayError, InsufficientBalanceError, InvalidDateRangeError
)
from src.adapters.workday.domain.time_models import TimeOffRequest, ManagerRef

def get_display_name(obj):
    """Helper to extract display name from various object structures (models, dicts, mocks)."""
    if not obj: return None
    if hasattr(obj, "name"):
        name = obj.name
        if hasattr(name, "display"):
            return name.display
        if isinstance(name, dict):
            return name.get("display")
        return str(name)
    if isinstance(obj, dict):
        return obj.get("name", {}).get("display")
    return "Unknown"

class WorkdayTimeService:
    def __init__(self, simulator):
        self.simulator = simulator
        self.state = simulator # Alias for unit tests

    async def get_balance(self, params: Dict[str, Any]) -> Dict[str, Any]:
        employee_id = params.get("employee_id")
        principal_id = params.get("principal_id")
        principal_type = params.get("principal_type")

        if not employee_id:
             raise WorkdayError("Missing employee_id", "INVALID_PARAMS")

        # Own Data Enforcement
        if principal_type == "HUMAN" and principal_id and principal_id != employee_id:
             raise WorkdayError("Access denied", "UNAUTHORIZED")

        balances = self.simulator.balances.get(employee_id)
        if balances is None:
            if employee_id not in self.simulator.employees:
                 raise WorkdayError("Access denied", "UNAUTHORIZED")
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
            
        # Parse dates if they are strings
        if isinstance(start_date, str):
            start_date = date.fromisoformat(start_date)
        if isinstance(end_date, str):
            end_date = date.fromisoformat(end_date)
            
        if start_date > end_date:
            raise InvalidDateRangeError()
            
        if principal_type == "HUMAN" and principal_id and principal_id != employee_id:
             raise WorkdayError("Cannot request time off for another employee", "UNAUTHORIZED")

        # 2. Check Balance
        balances = self.simulator.balances.get(employee_id, [])
        balance_entry = next((b for b in balances if b.type == req_type), None)
        
        if not balance_entry:
            raise WorkdayError("Invalid time off type", "INVALID_TYPE")
            
        if (balance_entry.available_hours - balance_entry.pending_hours) < hours:
            raise InsufficientBalanceError(balance_entry.available_hours - balance_entry.pending_hours, hours)

        # 3. Create Request
        request_id = f"TOR-{uuid.uuid4().hex[:8].upper()}"
        
        # Determine approver (Manager)
        employee = self.simulator.employees.get(employee_id)
        approver = None
        if employee and employee.manager:
             approver = {
                 "employee_id": employee.manager.employee_id,
                 "display_name": employee.manager.display_name if hasattr(employee.manager, "display_name") else employee.manager.get("display_name", "Manager")
             }

        # Update Balance (Pending)
        balance_entry.pending_hours += hours
        
        # Create Record using proper Pydantic model
        record = TimeOffRequest(
            request_id=request_id,
            employee_id=employee_id,
            employee_name=get_display_name(employee),
            status="PENDING",
            type=req_type,
            type_name=getattr(balance_entry, "type_name", req_type),
            start_date=start_date,
            end_date=end_date,
            hours=hours,
            submitted_at=datetime.now(timezone.utc)
        )
        self.simulator.requests[request_id] = record

        return {
            "request_id": request_id,
            "status": "PENDING",
            "submitted_at": record.submitted_at.isoformat(),
            "approver": approver,
            "estimated_balance_after": balance_entry.available_hours - hours 
        }

    async def list_requests(self, params: Dict[str, Any]) -> Dict[str, Any]:
        employee_id = params.get("employee_id")
        
        principal_id = params.get("principal_id")
        principal_type = params.get("principal_type")

        if not employee_id:
            raise WorkdayError("Missing employee_id", "INVALID_PARAMS")
            
        # Auth Check: Self or Manager
        if principal_type == "HUMAN" and principal_id and principal_id != employee_id:
            employee = self.simulator.employees.get(employee_id)
            if not employee or not employee.manager or employee.manager.employee_id != principal_id:
                raise WorkdayError("Access denied", "UNAUTHORIZED")

        requests = [
            r.model_dump() for r in self.simulator.requests.values()
            if r.employee_id == employee_id
        ]
        return {
            "employee_id": employee_id,
            "requests": requests,
            "count": len(requests)
        }

    async def get_request(self, params: Dict[str, Any]) -> Dict[str, Any]:
        request_id = params.get("request_id")
        
        principal_id = params.get("principal_id")
        principal_type = params.get("principal_type")

        if not request_id:
             raise WorkdayError("Missing request_id", "INVALID_PARAMS")
             
        request = self.simulator.requests.get(request_id)
        if not request:
            raise WorkdayError("Access denied", "UNAUTHORIZED")
            
        # Auth Check: Request owner or manager can view
        if principal_type == "HUMAN" and principal_id:
            # Check owner
            if principal_id == request.employee_id:
                pass # OK
            else:
                # Check if manager
                employee = self.simulator.employees.get(request.employee_id)
                if not employee or not employee.manager or employee.manager.employee_id != principal_id:
                    raise WorkdayError("Access denied", "UNAUTHORIZED")

        return request.model_dump()

    async def cancel(self, params: Dict[str, Any]) -> Dict[str, Any]:
        request_id = params.get("request_id")
        reason = params.get("reason")
        
        principal_id = params.get("principal_id")
        principal_type = params.get("principal_type")

        if not request_id:
             raise WorkdayError("Missing request_id", "INVALID_PARAMS")

        request = self.simulator.requests.get(request_id)
        if not request:
            raise WorkdayError("Access denied", "UNAUTHORIZED")

        # Auth Check
        if principal_type == "HUMAN" and principal_id and principal_id != request.employee_id:
             raise WorkdayError("Access denied", "UNAUTHORIZED")

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

        # Update and persist
        request.status = "CANCELLED"
        self.simulator.requests[request_id] = request
        
        return {
            "request_id": request_id,
            "status": "CANCELLED",
            "cancelled_at": datetime.now(timezone.utc).isoformat(),
            "cancelled_by": principal_id or "system",
            "hours_restored": hours_restored
        }

    async def approve(self, params: Dict[str, Any]) -> Dict[str, Any]:
        request_id = params.get("request_id")
        principal_id = params.get("principal_id") or params.get("approver_id")
        principal_type = params.get("principal_type")
        mfa_verified = params.get("mfa_verified", False)

        if not request_id:
             raise WorkdayError("Missing request_id", "INVALID_PARAMS")
             
        # 1. MFA Check (High Sensitivity Manager Action)
        if not mfa_verified and principal_type != "MACHINE":
            raise WorkdayError("MFA required for time-off approval", "MFA_REQUIRED")

        request = self.simulator.requests.get(request_id)

        if not request:
            raise WorkdayError("Access denied", "UNAUTHORIZED")

        employee = self.simulator.employees.get(request.employee_id)
        if not employee:
             raise WorkdayError("Access denied", "UNAUTHORIZED")
             
        if principal_type == "HUMAN" and principal_id:
            if not employee.manager or employee.manager.employee_id != principal_id:
                raise WorkdayError("Access denied", "UNAUTHORIZED")
        
        if request.status != "PENDING":
             raise WorkdayError("Access denied", "UNAUTHORIZED")

        balances = self.simulator.balances.get(request.employee_id, [])
        balance_entry = next((b for b in balances if b.type == request.type), None)
        
        if balance_entry:
            balance_entry.pending_hours = max(0, balance_entry.pending_hours - request.hours)
            balance_entry.available_hours = max(0, balance_entry.available_hours - request.hours)
            balance_entry.used_hours += request.hours

        # Update and persist
        request.status = "APPROVED"
        request.approved_at = datetime.now(timezone.utc)
        request.approved_by = ManagerRef(
            employee_id=principal_id or "UNKNOWN",
            display_name=employee.manager.display_name if (employee.manager and hasattr(employee.manager, "display_name")) else "Manager"
        )
        self.simulator.requests[request_id] = request
        
        return {
            "request_id": request_id,
            "status": "APPROVED",
            "approved_at": request.approved_at.isoformat(),
            "approved_by": principal_id
        }

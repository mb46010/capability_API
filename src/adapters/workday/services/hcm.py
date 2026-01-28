from typing import Dict, Any, List
from datetime import datetime, timezone
import uuid
from src.adapters.workday.exceptions import WorkdayError

class WorkdayHCMService:
    def __init__(self, simulator):
        self.simulator = simulator

    async def get_employee(self, params: Dict[str, Any]) -> Dict[str, Any]:
        employee_id = params.get("employee_id")
        principal_type = params.get("principal_type", "HUMAN") # Default to HUMAN if missing

        if not employee_id:
             raise WorkdayError("Missing employee_id", "INVALID_PARAMS")

        employee = self.simulator.employees.get(employee_id)
        if not employee:
            raise WorkdayError(f"Employee {employee_id} not found", "EMPLOYEE_NOT_FOUND")

        # Convert to dict
        data = employee.model_dump()
        
        # Field Filtering for AI Agents (Plan requirement)
        if principal_type == "AI_AGENT":
            allowed_fields = {"employee_id", "name", "job", "status", "manager"}
            data = {k: v for k, v in data.items() if k in allowed_fields}

        return data

    async def get_employee_full(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Alias for get_employee, as it returns full details by default for non-agents."""
        return await self.get_employee(params)

    async def get_manager_chain(self, params: Dict[str, Any]) -> Dict[str, Any]:
        employee_id = params.get("employee_id")
        if not employee_id:
             raise WorkdayError("Missing employee_id", "INVALID_PARAMS")

        if employee_id not in self.simulator.employees:
            raise WorkdayError(f"Employee {employee_id} not found", "EMPLOYEE_NOT_FOUND")

        chain = []
        current_emp = self.simulator.employees[employee_id]
        level = 1
        
        # Traverse up
        while current_emp.manager:
            mgr_id = current_emp.manager.employee_id
            if mgr_id not in self.simulator.employees:
                break # Broken chain or external manager
            
            manager = self.simulator.employees[mgr_id]
            
            # Extract name/title handling both dict and object
            display_name = manager.name["display"] if isinstance(manager.name, dict) else manager.name.display
            title = manager.job["title"] if isinstance(manager.job, dict) else manager.job.title
            
            chain.append({
                "employee_id": manager.employee_id,
                "display_name": display_name,
                "title": title,
                "level": level
            })
            
            current_emp = manager
            level += 1
            
            # Safety brake for loops
            if level > 20: break

        return {
            "employee_id": employee_id,
            "chain": chain
        }

    async def list_direct_reports(self, params: Dict[str, Any]) -> Dict[str, Any]:
        manager_id = params.get("manager_id")
        # Check authorization if principal is provided (Manager Relationship Enforcement)
        # Spec: "Manager-scoped actions ... must verify that the principal is the immediate manager"
        # However, list_direct_reports input is `manager_id`. 
        # So usually a manager calls this with *their own* ID.
        # So we should enforce: principal_id == manager_id
        
        principal_id = params.get("principal_id")
        principal_type = params.get("principal_type")
        
        if not manager_id:
             raise WorkdayError("Missing manager_id", "INVALID_PARAMS")

        if principal_type == "HUMAN" and principal_id and principal_id != manager_id:
             # Only allow viewing own reports (unless admin/override)
             raise WorkdayError(f"Principal {principal_id} cannot view reports for {manager_id}", "UNAUTHORIZED")
        
        if manager_id not in self.simulator.employees:
             raise WorkdayError(f"Manager {manager_id} not found", "EMPLOYEE_NOT_FOUND")

        reports = []
        for emp in self.simulator.employees.values():
            if emp.manager and emp.manager.employee_id == manager_id:
                display_name = emp.name["display"] if isinstance(emp.name, dict) else emp.name.display
                title = emp.job["title"] if isinstance(emp.job, dict) else emp.job.title
                
                reports.append({
                    "employee_id": emp.employee_id,
                    "display_name": display_name,
                    "title": title,
                    "start_date": "2023-01-01" 
                })

        return {
            "manager_id": manager_id,
            "direct_reports": reports,
            "count": len(reports)
        }

    async def update_contact_info(self, params: Dict[str, Any]) -> Dict[str, Any]:
        employee_id = params.get("employee_id")
        updates = params.get("updates", {})
        
        principal_id = params.get("principal_id")
        principal_type = params.get("principal_type")

        if not employee_id:
             raise WorkdayError("Missing employee_id", "INVALID_PARAMS")

        # Auth Check: Own Data Only (unless admin)
        if principal_type == "HUMAN" and principal_id and principal_id != employee_id:
             raise WorkdayError(f"Principal {principal_id} cannot update data for {employee_id}", "UNAUTHORIZED")

        employee = self.simulator.employees.get(employee_id)
        if not employee:
            raise WorkdayError(f"Employee {employee_id} not found", "EMPLOYEE_NOT_FOUND")

        # Apply Updates
        changes = []
        
        # 1. Personal Email
        if "personal_email" in updates:
            old_val = getattr(employee, "personal_email", None)
            new_val = updates["personal_email"]
            if old_val != new_val:
                setattr(employee, "personal_email", new_val)
                changes.append({
                    "field": "personal_email",
                    "old_value": old_val,
                    "new_value": new_val
                })

        # 2. Phone
        if "phone" in updates and isinstance(updates["phone"], dict):
            # Assumes employee.phone is an object/model
            phone_updates = updates["phone"]
            if not getattr(employee, "phone", None):
                # Init phone object if missing (simplified)
                 class Phone: pass
                 employee.phone = Phone()
            
            for key, val in phone_updates.items():
                old_val = getattr(employee.phone, key, None)
                if old_val != val:
                    setattr(employee.phone, key, val)
                    changes.append({
                        "field": f"phone.{key}",
                        "old_value": old_val,
                        "new_value": val
                    })

        return {
            "employee_id": employee_id,
            "transaction_id": f"TXN-{uuid.uuid4().hex[:8]}",
            "status": "APPLIED",
            "effective_date": datetime.now(timezone.utc).date().isoformat(),
            "changes": changes
        }


    
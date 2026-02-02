from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import uuid
from src.adapters.workday.exceptions import WorkdayError
from src.adapters.workday.domain.hcm_models import EmployeePhone

class WorkdayHCMService:

    def __init__(self, simulator):
        self.simulator = simulator

    async def get_employee(self, params: Dict[str, Any]) -> Dict[str, Any]:
        employee_id = params.get("employee_id")
        principal_id = params.get("principal_id")
        principal_type = params.get("principal_type", "HUMAN") # Default to HUMAN if missing
        principal_groups = params.get("principal_groups", [])

        if not employee_id:
             raise WorkdayError("Missing employee_id", "INVALID_PARAMS")

        # Auth check first (if applicable)
        is_admin = "hr-platform-admins" in principal_groups
        if principal_type == "HUMAN" and principal_id and principal_id != employee_id and not is_admin:
             # According to BUG-006, we should restrict humans to self-only to prevent enumeration
             raise WorkdayError("Access denied", "UNAUTHORIZED")

        employee = self.simulator.employees.get(employee_id)
        if not employee:
            raise WorkdayError("Access denied", "UNAUTHORIZED")

        # Convert to dict
        data = employee.model_dump()
        
        # Field Filtering (Plan requirement)
        if principal_type == "AI_AGENT":
            allowed_fields = {"employee_id", "name", "job", "status", "manager"}
            data = {k: v for k, v in data.items() if k in allowed_fields}
        elif principal_type == "HUMAN" and principal_id != employee_id:
            # This block is now unreachable for HUMANS due to the auth check above,
            # but kept for architectural consistency if we ever allow some humans to see others.
            sensitive_fields = {"personal_email", "phone", "birth_date", "ssn", "emergency_contact"}
            data = {k: v for k, v in data.items() if k not in sensitive_fields}

        return data

    async def get_employee_full(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Alias for get_employee, as it returns full details by default for non-agents."""
        return await self.get_employee(params)

    async def get_org_chart(self, params: Dict[str, Any]) -> Dict[str, Any]:
        root_id = params.get("root_id")
        depth = params.get("depth", 2)
        
        principal_id = params.get("principal_id")
        principal_type = params.get("principal_type")
        principal_groups = params.get("principal_groups", [])
        
        if not root_id:
             raise WorkdayError("Missing root_id", "INVALID_PARAMS")
             
        # Auth Check: Can only view org chart starting from self (unless manager/admin)
        is_admin = "hr-platform-admins" in principal_groups
        if principal_type == "HUMAN" and principal_id and principal_id != root_id and not is_admin:
            # Simple policy for MVP: Self-root only
            raise WorkdayError("Access denied", "UNAUTHORIZED")

        if root_id not in self.simulator.employees:
            raise WorkdayError("Access denied", "UNAUTHORIZED")
            
        async def build_node(emp_id, current_depth):
            if current_depth > depth:
                return None
            
            emp = self.simulator.employees.get(emp_id)
            if not emp: return None
            
            # Helper for name
            def get_display_name(obj):
                if hasattr(obj, "name"):
                    return obj.name.display if hasattr(obj.name, "display") else obj.name.get("display")
                return obj.get("name", {}).get("display", "Unknown")

            node = {
                "employee_id": emp.employee_id,
                "name": get_display_name(emp),
                "title": emp.job["title"] if isinstance(emp.job, dict) else (emp.job.title if hasattr(emp.job, "title") else "Unknown"),
                "reports": []
            }
            
            if current_depth < depth:
                # Find reports
                for report in self.simulator.employees.values():
                    if report.manager and report.manager.employee_id == emp_id:
                        child = await build_node(report.employee_id, current_depth + 1)
                        if child:
                            node["reports"].append(child)
            
            return node

        node = await build_node(root_id, 1)
        
        def count_nodes(n):
            if not n: return 0
            count = 1
            for child in n.get("reports", []):
                count += count_nodes(child);
            return count

        return {
            "root": node,
            "total_count": count_nodes(node)
        }

    async def get_manager_chain(self, params: Dict[str, Any]) -> Dict[str, Any]:
        employee_id = params.get("employee_id")
        
        principal_id = params.get("principal_id")
        principal_type = params.get("principal_type")
        principal_groups = params.get("principal_groups", [])

        if not employee_id:
             raise WorkdayError("Missing employee_id", "INVALID_PARAMS")

        # Auth Check: Self only
        is_admin = "hr-platform-admins" in principal_groups
        if principal_type == "HUMAN" and principal_id and principal_id != employee_id and not is_admin:
            raise WorkdayError("Access denied", "UNAUTHORIZED")

        if employee_id not in self.simulator.employees:
            raise WorkdayError("Access denied", "UNAUTHORIZED")

        chain = []
        visited = {employee_id}
        current_emp = self.simulator.employees[employee_id]
        level = 1
        
        # Traverse up
        while current_emp.manager:
            mgr_id = current_emp.manager.employee_id
            
            if mgr_id in visited:
                raise WorkdayError("Circular manager reference detected", "DATA_INTEGRITY_ERROR")
            
            if mgr_id not in self.simulator.employees:
                break # Broken chain or external manager
            
            manager = self.simulator.employees[mgr_id]
            visited.add(mgr_id)
            
            # Extract name/title handling both dict and object
            display_name = manager.name.display if hasattr(manager.name, "display") else manager.name.get("display")
            title = manager.job.title if hasattr(manager.job, "title") else manager.job.get("title")
            
            chain.append({
                "employee_id": manager.employee_id,
                "display_name": display_name,
                "title": title,
                "level": level
            })
            
            current_emp = manager
            level += 1

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
        principal_groups = params.get("principal_groups", [])
        
        if not manager_id:
             raise WorkdayError("Missing manager_id", "INVALID_PARAMS")

        is_admin = "hr-platform-admins" in principal_groups
        if principal_type == "HUMAN" and principal_id and principal_id != manager_id and not is_admin:
             # Only allow viewing own reports (unless admin/override)
             raise WorkdayError("Access denied", "UNAUTHORIZED")
        
        if manager_id not in self.simulator.employees:
             raise WorkdayError("Access denied", "UNAUTHORIZED")

        reports = []
        for emp in self.simulator.employees.values():
            if emp.manager and emp.manager.employee_id == manager_id:
                display_name = emp.name.display if hasattr(emp.name, "display") else emp.name.get("display")
                title = emp.job.title if hasattr(emp.job, "title") else emp.job.get("title")
                
                # Extract start_date from object if available
                start_date = getattr(emp, "start_date", "2023-01-01")
                if hasattr(start_date, "isoformat"):
                    start_date = start_date.isoformat()
                
                reports.append({
                    "employee_id": emp.employee_id,
                    "display_name": display_name,
                    "title": title,
                    "start_date": start_date
                })

        return {
            "manager_id": manager_id,
            "direct_reports": reports,
            "count": len(reports)
        }

    async def update_employee(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Update core employee fields."""
        employee_id = params.get("employee_id")
        updates = params.get("updates", {})
        
        principal_id = params.get("principal_id")
        principal_type = params.get("principal_type")
        principal_groups = params.get("principal_groups", [])

        if not employee_id:
             raise WorkdayError("Missing employee_id", "INVALID_PARAMS")
             
        # Auth Check: Own Data Only
        is_admin = "hr-platform-admins" in principal_groups
        if principal_type == "HUMAN" and principal_id and principal_id != employee_id and not is_admin:
             raise WorkdayError("Access denied", "UNAUTHORIZED")

        employee = self.simulator.employees.get(employee_id)
        if not employee:
            raise WorkdayError("Access denied", "UNAUTHORIZED")
            
        changes = []
        # Apply updates to the model
        for key, value in updates.items():
            if hasattr(employee, key):
                old_val = getattr(employee, key)
                changes.append({
                    "field": key,
                    "old_value": str(old_val),
                    "new_value": str(value)
                })
                # For HCM core updates, they usually go to PENDING_APPROVAL status
                # but we still track what changed.
                     
        return {
            "employee_id": employee_id,
            "status": "PENDING_APPROVAL",
            "changes": changes,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }

    async def update_contact_info(self, params: Dict[str, Any]) -> Dict[str, Any]:
        employee_id = params.get("employee_id")
        updates = params.get("updates", {})
        
        principal_id = params.get("principal_id")
        principal_type = params.get("principal_type")
        principal_groups = params.get("principal_groups", [])

        if not employee_id:
             raise WorkdayError("Missing employee_id", "INVALID_PARAMS")

        # Auth Check: Own Data Only (unless admin)
        is_admin = "hr-platform-admins" in principal_groups
        if principal_type == "HUMAN" and principal_id and principal_id != employee_id and not is_admin:
             raise WorkdayError("Access denied", "UNAUTHORIZED")

        employee = self.simulator.employees.get(employee_id)
        if not employee:
            raise WorkdayError("Access denied", "UNAUTHORIZED")

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
                employee.phone = EmployeePhone()
            
            for key, val in phone_updates.items():
                if hasattr(employee.phone, key):
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

    async def terminate_employee(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Initiate employee termination workflow."""
        employee_id = params.get("employee_id")
        termination_date = params.get("termination_date")
        reason_code = params.get("reason_code")

        principal_id = params.get("principal_id")
        principal_type = params.get("principal_type")
        principal_groups = params.get("principal_groups", [])
        mfa_verified = params.get("mfa_verified", False)

        if not employee_id:
            raise WorkdayError("Missing employee_id", "INVALID_PARAMS")
        if not termination_date:
            raise WorkdayError("Missing termination_date", "INVALID_PARAMS")
        if not reason_code:
            raise WorkdayError("Missing reason_code", "INVALID_PARAMS")

        # MFA required for termination (high sensitivity)
        if not mfa_verified and principal_type != "MACHINE":
            raise WorkdayError("MFA required for employee termination", "MFA_REQUIRED")

        # Auth Check: Admins only for termination of others
        is_admin = "hr-platform-admins" in principal_groups
        if principal_type == "HUMAN" and principal_id and principal_id != employee_id and not is_admin:
            raise WorkdayError("Access denied", "UNAUTHORIZED")

        employee = self.simulator.employees.get(employee_id)
        if not employee:
            raise WorkdayError("Access denied", "UNAUTHORIZED")

        # Update employee status
        employee.status = "PENDING_TERMINATION"

        return {
            "employee_id": employee_id,
            "transaction_id": f"TERM-{uuid.uuid4().hex[:8]}",
            "status": "PENDING_APPROVAL",
            "termination_date": termination_date,
            "reason_code": reason_code,
            "initiated_by": principal_id,
            "initiated_at": datetime.now(timezone.utc).isoformat()
        }

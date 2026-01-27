import uuid
from datetime import datetime, date
from typing import Dict, Any, List, Optional
from src.adapters.workday.domain.hcm_models import Employee, EmployeeFull, ManagerRef, Department
from src.adapters.workday.domain.types import EmployeeStatus
from src.adapters.workday.exceptions import EmployeeNotFoundError

class WorkdayHCMService:
    def __init__(self, simulator_state: Any):
        self.state = simulator_state

    async def get_employee(self, params: Dict[str, Any]) -> Dict[str, Any]:
        employee_id = params.get("employee_id")
        if not employee_id or employee_id not in self.state.employees:
            raise EmployeeNotFoundError(employee_id)
        
        emp = self.state.employees[employee_id]
        return emp.model_dump()

    async def get_employee_full(self, params: Dict[str, Any]) -> Dict[str, Any]:
        employee_id = params.get("employee_id")
        if not employee_id or employee_id not in self.state.employees:
            raise EmployeeNotFoundError(employee_id)
        
        # In a real simulator we might have a separate store for full records
        # For now we'll just simulate it by returning what we have in the model
        emp = self.state.employees[employee_id]
        
        # We need to return EmployeeFull fields if they exist in fixture
        # Our fixtures currently have them in the same file
        return emp.model_dump()

    async def list_direct_reports(self, params: Dict[str, Any]) -> Dict[str, Any]:
        manager_id = params.get("manager_id")
        reports = []
        for emp in self.state.employees.values():
            if emp.manager and emp.manager.employee_id == manager_id:
                reports.append({
                    "employee_id": emp.employee_id,
                    "display_name": emp.name.display,
                    "title": emp.job.title,
                    "start_date": str(emp.start_date)
                })
        
        return {
            "manager_id": manager_id,
            "direct_reports": reports,
            "count": len(reports)
        }

    async def get_manager_chain(self, params: Dict[str, Any]) -> Dict[str, Any]:
        employee_id = params.get("employee_id")
        if not employee_id or employee_id not in self.state.employees:
            raise EmployeeNotFoundError(employee_id)
            
        chain = []
        current_emp = self.state.employees[employee_id]
        level = 1
        
        while current_emp.manager:
            m_id = current_emp.manager.employee_id
            if m_id not in self.state.employees:
                break
            mgr = self.state.employees[m_id]
            chain.append({
                "employee_id": mgr.employee_id,
                "display_name": mgr.name.display,
                "title": mgr.job.title,
                "level": level
            })
            current_emp = mgr
            level += 1
            
        return {
            "employee_id": employee_id,
            "chain": chain
        }

    async def get_org_chart(self, params: Dict[str, Any]) -> Dict[str, Any]:
        root_id = params.get("root_id")
        depth = params.get("depth", 2)
        
        if not root_id or root_id not in self.state.employees:
            raise EmployeeNotFoundError(root_id)
            
        root_emp = self.state.employees[root_id]
        
        async def build_tree(emp_id, current_depth):
            emp = self.state.employees[emp_id]
            node = {
                "employee_id": emp.employee_id,
                "display_name": emp.name.display,
                "title": emp.job.title,
                "reports": []
            }
            
            if current_depth < depth:
                for report in self.state.employees.values():
                    if report.manager and report.manager.employee_id == emp_id:
                        node["reports"].append(await build_tree(report.employee_id, current_depth + 1))
            return node

        tree = await build_tree(root_id, 0)
        return {
            "root": tree,
            "total_count": self._count_nodes(tree)
        }

    def _count_nodes(self, node):
        count = 1
        for report in node.get("reports", []):
            count += self._count_nodes(report)
        return count

    async def update_employee(self, params: Dict[str, Any]) -> Dict[str, Any]:
        employee_id = params.get("employee_id")
        updates = params.get("updates", {})
        
        if not employee_id or employee_id not in self.state.employees:
            raise EmployeeNotFoundError(employee_id)
            
        emp = self.state.employees[employee_id]
        # In-memory update logic
        # For simulation, we'll just track that it changed
        changes = []
        # Simple implementation: just log changes for now
        for key, value in updates.items():
            changes.append({
                "field": key,
                "old_value": "...", # Simplified
                "new_value": str(value)
            })
            
        return {
            "employee_id": employee_id,
            "transaction_id": f"TXN-{uuid.uuid4().hex[:8].upper()}",
            "status": "PENDING_APPROVAL",
            "effective_date": str(params.get("effective_date", date.today())),
            "changes": changes
        }

    async def terminate_employee(self, params: Dict[str, Any]) -> Dict[str, Any]:
        employee_id = params.get("employee_id")
        if not employee_id or employee_id not in self.state.employees:
            raise EmployeeNotFoundError(employee_id)
            
        return {
            "employee_id": employee_id,
            "transaction_id": f"TXN-{uuid.uuid4().hex[:8].upper()}",
            "status": "PENDING_APPROVAL",
            "termination_date": str(params.get("termination_date")),
            "offboarding_flow_id": f"FLOW-OFF-{uuid.uuid4().hex[:4].upper()}"
        }

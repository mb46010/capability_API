from typing import Dict, Any, List
from src.adapters.workday.exceptions import WorkdayError

class WorkdayPayrollService:
    def __init__(self, simulator):
        self.simulator = simulator

    async def get_compensation(self, params: Dict[str, Any]) -> Dict[str, Any]:
        employee_id = params.get("employee_id")
        
        principal_id = params.get("principal_id")
        principal_type = params.get("principal_type")
        principal_groups = params.get("principal_groups", [])
        mfa_verified = params.get("mfa_verified", False)

        if not employee_id:
             raise WorkdayError("Missing employee_id", "INVALID_PARAMS")

        # 1. Auth Check
        is_admin = "hr-platform-admins" in principal_groups
        if principal_type == "HUMAN" and principal_id and principal_id != employee_id and not is_admin:
             raise WorkdayError("Access denied", "UNAUTHORIZED")

        # 2. MFA Check (High Sensitivity)
        if not mfa_verified and principal_type != "MACHINE":
            raise WorkdayError("MFA required for compensation access", "MFA_REQUIRED")

        # 3. Retrieve Data
        comp = self.simulator.compensation.get(employee_id)
        if not comp:
             raise WorkdayError("Access denied", "UNAUTHORIZED")

        # Return Data
        return {
            "employee_id": employee_id,
            "compensation": {
                "base_salary": {
                    "amount": comp.compensation.base_salary.amount,
                    "currency": comp.compensation.base_salary.currency,
                    "frequency": comp.compensation.base_salary.frequency
                },
                "bonus_target": {
                    "percentage": comp.compensation.bonus_target.percentage if comp.compensation.bonus_target else 0,
                    "amount": comp.compensation.bonus_target.amount if comp.compensation.bonus_target else 0
                },
                "total_compensation": comp.compensation.total_compensation
            },
            "pay_grade": comp.pay_grade,
            "effective_date": comp.effective_date
        }

    async def list_pay_statements(self, params: Dict[str, Any]) -> Dict[str, Any]:
        employee_id = params.get("employee_id")
        year = params.get("year")
        
        principal_id = params.get("principal_id")
        principal_type = params.get("principal_type")
        mfa_verified = params.get("mfa_verified", False)

        if not employee_id:
            raise WorkdayError("Missing employee_id", "INVALID_PARAMS")
            
        # Auth Check
        if principal_type == "HUMAN" and principal_id and principal_id != employee_id:
             raise WorkdayError("Access denied", "UNAUTHORIZED")

        # MFA Check
        if not mfa_verified and principal_type != "MACHINE":
            raise WorkdayError("MFA required for pay statement access", "MFA_REQUIRED")

        statements = [
            s.model_dump() for s in self.simulator.statements.values()
            if s.employee_id == employee_id and (not year or s.pay_date.year == int(year))
        ]
        
        return {
            "employee_id": employee_id,
            "statements": statements,
            "count": len(statements)
        }

    async def get_pay_statement(self, params: Dict[str, Any]) -> Dict[str, Any]:
        statement_id = params.get("statement_id")
        
        principal_id = params.get("principal_id")
        principal_type = params.get("principal_type")
        mfa_verified = params.get("mfa_verified", False)

        if not statement_id:
             raise WorkdayError("Missing statement_id", "INVALID_PARAMS")
             
        statement = self.simulator.statements.get(statement_id)
        
        # Auth Check first (or same error as not found)
        if not statement:
             raise WorkdayError("Access denied", "UNAUTHORIZED")
             
        if principal_type == "HUMAN" and principal_id and principal_id != statement.employee_id:
             raise WorkdayError("Access denied", "UNAUTHORIZED")

        # MFA Check
        if not mfa_verified and principal_type != "MACHINE":
            raise WorkdayError("MFA required for pay statement access", "MFA_REQUIRED")

        return statement.model_dump()
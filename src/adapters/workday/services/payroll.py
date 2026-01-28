from typing import Dict, Any, List
from src.adapters.workday.exceptions import WorkdayError

class WorkdayPayrollService:
    def __init__(self, simulator):
        self.simulator = simulator

    async def get_compensation(self, params: Dict[str, Any]) -> Dict[str, Any]:
        employee_id = params.get("employee_id")
        
        principal_id = params.get("principal_id")
        principal_type = params.get("principal_type")
        mfa_verified = params.get("mfa_verified", False)

        if not employee_id:
             raise WorkdayError("Missing employee_id", "INVALID_PARAMS")

        # 1. Auth Check
        if principal_type == "HUMAN" and principal_id and principal_id != employee_id:
             raise WorkdayError(f"Principal {principal_id} cannot access compensation for {employee_id}", "UNAUTHORIZED")

        # 2. MFA Check (High Sensitivity)
        if not mfa_verified:
             raise WorkdayError("MFA required for compensation access", "MFA_REQUIRED")

        # 3. Retrieve Data
        comp = self.simulator.compensation.get(employee_id)
        if not comp:
             raise WorkdayError(f"Compensation data not found for {employee_id}", "EMPLOYEE_NOT_FOUND")

        # Return Data
        return {
            "employee_id": employee_id,
            "compensation": {
                "base_salary": {
                    "amount": comp.base_salary.amount,
                    "currency": comp.base_salary.currency,
                    "frequency": comp.base_salary.frequency
                },
                "bonus_target": {
                    "percentage": comp.bonus_target.percentage,
                    "amount": comp.bonus_target.amount
                },
                "total_compensation": comp.total_compensation
            },
            "pay_grade": comp.pay_grade,
            "effective_date": comp.effective_date
        }
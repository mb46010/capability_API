from typing import Dict, Any, List, Optional
from src.adapters.workday.domain.payroll_models import Compensation, PayStatement
from src.adapters.workday.exceptions import EmployeeNotFoundError, StatementNotFoundError

class WorkdayPayrollService:
    def __init__(self, simulator_state: Any):
        self.state = simulator_state

    async def get_compensation(self, params: Dict[str, Any]) -> Dict[str, Any]:
        employee_id = params.get("employee_id")
        if not employee_id or employee_id not in self.state.employees:
            raise EmployeeNotFoundError(employee_id)
            
        comp = self.state.compensation.get(employee_id)
        if not comp:
            # Maybe not all employees have compensation data in fixtures
            return {}
            
        return comp.model_dump(mode='json')

    async def get_pay_statement(self, params: Dict[str, Any]) -> Dict[str, Any]:
        statement_id = params.get("statement_id")
        if not statement_id or statement_id not in self.state.statements:
            raise StatementNotFoundError(statement_id)
            
        return self.state.statements[statement_id].model_dump(mode='json')

    async def list_pay_statements(self, params: Dict[str, Any]) -> Dict[str, Any]:
        employee_id = params.get("employee_id")
        year = params.get("year")
        
        statements = []
        for stmt in self.state.statements.values():
            if stmt.employee_id == employee_id:
                if not year or stmt.pay_date.year == year:
                    statements.append({
                        "statement_id": stmt.statement_id,
                        "pay_date": str(stmt.pay_date),
                        "gross": stmt.earnings.gross,
                        "net": stmt.net_pay
                    })
        
        return {
            "employee_id": employee_id,
            "year": year,
            "statements": statements,
            "count": len(statements)
        }

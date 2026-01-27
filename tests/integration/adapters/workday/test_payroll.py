import pytest
from src.adapters.workday.client import WorkdaySimulator

@pytest.mark.asyncio
async def test_payroll_get_compensation():
    simulator = WorkdaySimulator()
    result = await simulator.execute("workday.payroll.get_compensation", {"employee_id": "EMP001"})
    
    assert result["employee_id"] == "EMP001"
    assert result["compensation"]["base_salary"]["amount"] == 185000

@pytest.mark.asyncio
async def test_payroll_list_pay_statements():
    simulator = WorkdaySimulator()
    result = await simulator.execute("workday.payroll.list_pay_statements", {"employee_id": "EMP001", "year": 2026})
    
    assert result["employee_id"] == "EMP001"
    assert len(result["statements"]) >= 1
    assert result["statements"][0]["statement_id"] == "PAY-2026-01"

@pytest.mark.asyncio
async def test_payroll_get_pay_statement():
    simulator = WorkdaySimulator()
    result = await simulator.execute("workday.payroll.get_pay_statement", {"statement_id": "PAY-2026-01"})
    
    assert result["statement_id"] == "PAY-2026-01"
    assert result["net_pay"] == 3546.06

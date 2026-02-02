import pytest

@pytest.mark.asyncio
async def test_payroll_get_compensation(simulator):
    result = await simulator.execute("workday.payroll.get_compensation", {"employee_id": "EMP001", "mfa_verified": True})
    
    assert result["employee_id"] == "EMP001"
    assert result["compensation"]["base_salary"]["amount"] == 185000

@pytest.mark.asyncio
async def test_payroll_list_pay_statements(simulator):
    result = await simulator.execute("workday.payroll.list_pay_statements", {"employee_id": "EMP001", "year": 2026, "mfa_verified": True})
    
    assert result["employee_id"] == "EMP001"
    assert len(result["statements"]) >= 1
    assert result["statements"][0]["statement_id"] == "PAY-2026-01"

@pytest.mark.asyncio
async def test_payroll_get_pay_statement(simulator):
    result = await simulator.execute("workday.payroll.get_pay_statement", {"statement_id": "PAY-2026-01", "mfa_verified": True})
    
    assert result["statement_id"] == "PAY-2026-01"
    assert result["net_pay"] == 3546.06


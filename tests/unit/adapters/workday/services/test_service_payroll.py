import pytest
from unittest.mock import MagicMock
from datetime import date
from src.adapters.workday.services.payroll import WorkdayPayrollService
from src.adapters.workday.domain.payroll_models import Compensation, CompensationDetails, BaseSalary, PayStatement, PayPeriod, Earnings, Deductions, YearToDate
from src.adapters.workday.domain.hcm_models import Employee, EmployeeName, EmployeeJob
from src.adapters.workday.domain.types import EmployeeStatus
from src.adapters.workday.exceptions import EmployeeNotFoundError

@pytest.fixture
def mock_state():
    state = MagicMock()
    # Setup dummy employee
    state.employees = {
        "EMP001": Employee(
            employee_id="EMP001",
            name=EmployeeName(first="Alice", last="Johnson", display="Alice Johnson"),
            email="alice@example.com",
            job=EmployeeJob(title="Engineer", department="Eng", department_id="D1", location="US"),
            status=EmployeeStatus.ACTIVE,
            start_date="2023-01-01"
        )
    }
    # Setup compensation
    state.compensation = {
        "EMP001": Compensation(
            employee_id="EMP001",
            compensation=CompensationDetails(
                base_salary=BaseSalary(amount=100000, currency="USD", frequency="ANNUAL"),
                total_compensation=100000
            ),
            pay_grade="L1",
            effective_date="2023-01-01"
        )
    }
    # Setup statements
    state.statements = {
        "PAY-001": PayStatement(
            statement_id="PAY-001",
            employee_id="EMP001",
            pay_period=PayPeriod(start="2023-01-01", end="2023-01-15"),
            pay_date="2023-01-20",
            earnings=Earnings(regular=4000, gross=4000),
            deductions=Deductions(federal_tax=500, state_tax=200, social_security=300, medicare=100, health_insurance=100, retirement_401k=200, total=1400),
            net_pay=2600,
            ytd=YearToDate(gross=4000, taxes=1100, net=2600)
        )
    }
    return state

@pytest.fixture
def service(mock_state):
    return WorkdayPayrollService(mock_state)

@pytest.mark.asyncio
async def test_get_compensation_success(service):
    result = await service.get_compensation({"employee_id": "EMP001", "mfa_verified": True})
    assert result["employee_id"] == "EMP001"
    assert result["compensation"]["base_salary"]["amount"] == 100000

@pytest.mark.asyncio
async def test_get_compensation_not_found(service):
    with pytest.raises(EmployeeNotFoundError):
        await service.get_compensation({"employee_id": "NON_EXISTENT", "mfa_verified": True})

@pytest.mark.asyncio
async def test_list_pay_statements(service):
    result = await service.list_pay_statements({"employee_id": "EMP001", "year": 2023, "mfa_verified": True})
    assert result["count"] == 1
    assert result["statements"][0]["statement_id"] == "PAY-001"


import pytest

@pytest.mark.asyncio
async def test_hcm_get_employee(simulator):
    result = await simulator.execute("workday.hcm.get_employee", {"employee_id": "EMP001"})
    
    assert result["employee_id"] == "EMP001"
    assert result["name"]["display"] == "Alice Johnson"

@pytest.mark.asyncio
async def test_hcm_get_manager_chain(simulator):
    result = await simulator.execute("workday.hcm.get_manager_chain", {"employee_id": "EMP001"})
    
    assert result["employee_id"] == "EMP001"
    assert len(result["chain"]) >= 2
    assert result["chain"][0]["employee_id"] == "EMP042"
    assert result["chain"][1]["employee_id"] == "EMP100"

@pytest.mark.asyncio
async def test_hcm_list_direct_reports(simulator):
    result = await simulator.execute("workday.hcm.list_direct_reports", {"manager_id": "EMP042"})
    
    assert result["manager_id"] == "EMP042"
    assert any(r["employee_id"] == "EMP001" for r in result["direct_reports"])

@pytest.mark.asyncio
async def test_hcm_get_org_chart(simulator):
    result = await simulator.execute("workday.hcm.get_org_chart", {"root_id": "EMP100", "depth": 2})
    
    assert result["root"]["employee_id"] == "EMP100"
    assert result["total_count"] >= 2

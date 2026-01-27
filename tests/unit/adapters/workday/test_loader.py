import pytest
from src.adapters.workday.loader import FixtureLoader
from src.adapters.workday.config import WorkdaySimulationConfig

def test_fixture_loader_loads_data():
    config = WorkdaySimulationConfig()
    loader = FixtureLoader(config.fixture_path)
    
    assert "EMP001" in loader.employees
    assert loader.employees["EMP001"].name.first == "Alice"
    assert "DEPT-ENG" in loader.departments
    assert "EMP001" in loader.balances
    assert len(loader.balances["EMP001"]) == 2
    assert "TOR-001" in loader.requests
    assert "EMP001" in loader.compensation
    assert "PAY-2026-01" in loader.statements

def test_loader_missing_files_does_not_crash(tmp_path):
    loader = FixtureLoader(str(tmp_path))
    assert loader.employees == {}
    assert loader.departments == {}

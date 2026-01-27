import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any
from src.adapters.workday.domain.hcm_models import Employee, EmployeeFull, Department, ManagerRef
from src.adapters.workday.domain.time_models import TimeOffBalance, TimeOffRequest
from src.adapters.workday.domain.payroll_models import Compensation, PayStatement

class FixtureLoader:
    def __init__(self, fixture_path: str):
        self.path = Path(fixture_path)
        self.employees: Dict[str, EmployeeFull] = {}
        self.departments: Dict[str, Department] = {}
        self.balances: Dict[str, List[TimeOffBalance]] = {}
        self.requests: Dict[str, TimeOffRequest] = {}
        self.compensation: Dict[str, Compensation] = {}
        self.statements: Dict[str, PayStatement] = {}
        self.load_all()

    def load_all(self):
        # We need raw data for two-pass resolution
        self._load_hcm()
        self._load_time()
        self._load_payroll()

    def _load_hcm(self):
        file = self.path / "employees.yaml"
        if not file.exists():
            return
        data = yaml.safe_load(file.read_text())
        
        raw_employees = data.get("employees", {})
        
        # Pass 1: Create EmployeeFull objects without manager
        for eid, edata in raw_employees.items():
            edata_copy = edata.copy()
            edata_copy.pop("manager_id", None)
            self.employees[eid] = EmployeeFull(**edata_copy)
            
        # Pass 2: Resolve manager_id to manager object
        for eid, edata in raw_employees.items():
            mid = edata.get("manager_id")
            if mid and mid in self.employees:
                m = self.employees[mid]
                self.employees[eid].manager = ManagerRef(
                    employee_id=m.employee_id,
                    display_name=m.name.display
                )
            
        for did, ddata in data.get("departments", {}).items():
            self.departments[did] = Department(**ddata)

    def _load_time(self):
        file = self.path / "time_tracking.yaml"
        if not file.exists():
            return
        data = yaml.safe_load(file.read_text())
        
        for eid, bdata_list in data.get("balances", {}).items():
            self.balances[eid] = [TimeOffBalance(**b) for b in bdata_list]
            
        for rid, rdata in data.get("requests", {}).items():
            rdata_copy = rdata.copy()
            mid = rdata_copy.pop("approved_by", None)
            
            # Pydantic will handle string to date/datetime conversion automatically
            req = TimeOffRequest(**rdata_copy)
            
            if mid and mid in self.employees:
                m = self.employees[mid]
                req.approved_by = ManagerRef(
                    employee_id=m.employee_id,
                    display_name=m.name.display
                )
            self.requests[rid] = req

    def _load_payroll(self):
        file = self.path / "payroll.yaml"
        if not file.exists():
            return
        data = yaml.safe_load(file.read_text())
        
        for eid, cdata in data.get("compensation", {}).items():
            self.compensation[eid] = Compensation(**cdata)
            
        for sid, sdata in data.get("statements", {}).items():
            self.statements[sid] = PayStatement(**sdata)
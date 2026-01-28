# scripts/generate_fixtures.py
from src.adapters.workday.domain.hcm_models import Employee
from faker import Faker
import yaml

fake = Faker()

employees = {}
for i in range(100):
    emp_id = f"EMP{i:03d}"
    employees[emp_id] = {
        "employee_id": emp_id,
        "name": {"first": fake.first_name(), "last": fake.last_name(), ...},
        # ... generate realistic test data
    }

with open("fixtures/employees_generated.yaml", "w") as f:
    yaml.dump({"employees": employees}, f)
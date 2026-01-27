import pytest
from pydantic import BaseModel
from src.domain.entities.action import ActionRequest, ActionResponse
from src.domain.entities.flow import FlowStartRequest, FlowStatusResponse
from src.domain.entities.policy import AccessPolicy, PolicyRule, PrincipalDefinition
from src.domain.entities.error import ErrorResponse
from src.adapters.workday.domain.hcm_models import Employee, EmployeeFull, Department
from src.adapters.workday.domain.time_models import TimeOffBalance, TimeOffRequest
from src.adapters.workday.domain.payroll_models import Compensation, PayStatement

def check_field_descriptions(model_class: type[BaseModel]):
    """Helper to check if all fields in a model have descriptions."""
    schema = model_class.model_json_schema()
    properties = schema.get("properties", {})
    for field_name, field_info in properties.items():
        assert "description" in field_info, f"Field '{field_name}' in {model_class.__name__} is missing a description"

@pytest.mark.parametrize("model", [
    ActionRequest, ActionResponse,
    FlowStartRequest, FlowStatusResponse,
    AccessPolicy, PolicyRule, PrincipalDefinition,
    ErrorResponse,
    Employee, EmployeeFull, Department,
    TimeOffBalance, TimeOffRequest,
    Compensation, PayStatement
])
def test_pydantic_models_have_descriptions(model):
    check_field_descriptions(model)

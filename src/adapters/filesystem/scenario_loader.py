import yaml
from pathlib import Path
from typing import List
from src.domain.entities.policy_test import PolicyTestSuite
from src.domain.ports.scenario_loader import ScenarioLoaderPort

class FileScenarioLoaderAdapter(ScenarioLoaderPort):
    def load_test_suite(self, scenario_path: str) -> PolicyTestSuite:
        with open(scenario_path, "r") as f:
            data = yaml.safe_load(f)
        return PolicyTestSuite(**data)

    def load_all_test_suites(self, scenarios_dir: str) -> List[PolicyTestSuite]:
        scenarios_path = Path(scenarios_dir)
        if not scenarios_path.exists() and not scenarios_path.is_absolute():
            # Resolve relative to project root (parent of 'src')
            project_root = Path(__file__).resolve().parent.parent.parent.parent
            scenarios_path = project_root / scenarios_dir
            
        suites = []
        if scenarios_path.is_file():
            suites.append(self.load_test_suite(str(scenarios_path)))
        elif scenarios_path.is_dir():
            for yaml_file in sorted(scenarios_path.glob("*.yaml")):
                suites.append(self.load_test_suite(str(yaml_file)))
        return suites


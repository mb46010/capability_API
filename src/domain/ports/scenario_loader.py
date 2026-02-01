from abc import ABC, abstractmethod
from typing import List
from src.domain.entities.policy_test import PolicyTestSuite

class ScenarioLoaderPort(ABC):
    @abstractmethod
    def load_test_suite(self, scenario_path: str) -> PolicyTestSuite:
        """Load a single test suite from the given path."""
        pass

    @abstractmethod
    def load_all_test_suites(self, scenarios_dir: str) -> List[PolicyTestSuite]:
        """Load all test suites from the specified directory."""
        pass

from abc import ABC, abstractmethod
from src.domain.entities.policy import AccessPolicy

class PolicyLoaderPort(ABC):
    @abstractmethod
    def load_policy(self) -> AccessPolicy:
        """Load and return the parsed AccessPolicy."""
        pass

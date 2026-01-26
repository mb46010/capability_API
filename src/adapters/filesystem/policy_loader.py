import yaml
from pathlib import Path
from src.domain.ports.policy_loader import PolicyLoaderPort
from src.domain.entities.policy import AccessPolicy

class FilePolicyLoaderAdapter(PolicyLoaderPort):
    def __init__(self, policy_path: str):
        self.policy_path = Path(policy_path)

    def load_policy(self) -> AccessPolicy:
        if not self.policy_path.exists():
            raise FileNotFoundError(f"Policy file not found at {self.policy_path}")
        
        with open(self.policy_path, "r") as f:
            data = yaml.safe_load(f)
            
        return AccessPolicy(**data)

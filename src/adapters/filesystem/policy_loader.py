import yaml
from pathlib import Path
from typing import List
from src.domain.ports.policy_loader import PolicyLoaderPort
from src.domain.entities.policy import AccessPolicy
from src.domain.services.capability_registry import get_capability_registry

class FilePolicyLoaderAdapter(PolicyLoaderPort):
    """
    Adapter for loading access policies from the local filesystem.
    Now includes validation against the Capability Registry.
    """
    def __init__(self, policy_path: str, registry_path: str = "config/capabilities/index.yaml"):
        self.policy_path = Path(policy_path)
        self.registry = get_capability_registry(registry_path)

    def load_policy(self) -> AccessPolicy:
        if not self.policy_path.exists():
            raise FileNotFoundError(f"Policy file not found at {self.policy_path}")
        
        with open(self.policy_path, "r") as f:
            data = yaml.safe_load(f)
            
        policy = AccessPolicy(**data)
        
        # 1. Validate internal references (principals, groups)
        validation_errors = policy.validate_references()
        if validation_errors:
            raise ValueError(f"Policy reference validation failed:\n" + "\n".join(validation_errors))
            
        # 2. Validate capability references against the registry
        capability_errors = self._validate_capabilities(policy)
        if capability_errors:
            raise ValueError(
                f"Policy capability validation failed:\n" + "\n".join(capability_errors)
            )
            
        return policy

    def _validate_capabilities(self, policy: AccessPolicy) -> List[str]:
        """Validate all capability references in the policy."""
        errors = []
        
        # Validate capability groups first
        if policy.capability_groups:
            for group_name, capabilities in policy.capability_groups.items():
                group_errors = self.registry.validate_capability_list(capabilities)
                if group_errors:
                    errors.append(f"Capability group '{group_name}':")
                    errors.extend([f"  {err}" for err in group_errors])
        
        # Validate capabilities in policy rules
        for rule in policy.policies:
            if isinstance(rule.capabilities, str):
                # It's a group reference, already validated group content above.
                # Just ensuring the group exists (done in validate_references).
                continue
            
            rule_errors = self.registry.validate_capability_list(rule.capabilities)
            if rule_errors:
                errors.append(f"Policy '{rule.name}':")
                errors.extend([f"  {err}" for err in rule_errors])
                
        return errors

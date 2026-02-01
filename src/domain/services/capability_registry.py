import yaml
import logging
from pathlib import Path
from typing import List, Optional, Set, Dict
from difflib import get_close_matches

from src.domain.entities.capability import CapabilityRegistry, CapabilityEntry, CapabilityType
from src.lib.matching import capability_matches

logger = logging.getLogger(__name__)


class CapabilityRegistryService:
    """
    Service for loading and querying the capability registry.
    Canonical source of truth for all actions and flows.
    """
    def __init__(self, index_path: str = "config/capabilities/index.yaml"):
        path = Path(index_path)
        if not path.exists() and not path.is_absolute():
            # Try resolving relative to project root (parent of 'src')
            project_root = Path(__file__).resolve().parent.parent.parent.parent
            path = project_root / index_path
            
        self.index_path = path
        self._registry: Optional[CapabilityRegistry] = None
        self._capability_map: Dict[str, CapabilityEntry] = {}
        self._load()

    def _load(self) -> None:
        """Load registry from YAML file."""
        if not self.index_path.exists():
            raise FileNotFoundError(f"Capability registry not found: {self.index_path}")
        
        with open(self.index_path, "r") as f:
            data = yaml.safe_load(f)
            
        self._registry = CapabilityRegistry(**data)
        
        # Build lookup map for O(1) access
        self._capability_map = {}
        for cap in self._registry.capabilities:
            if cap.id in self._capability_map:
                raise ValueError(f"Duplicate capability IDs found in registry: {cap.id}")
            self._capability_map[cap.id] = cap
            
        logger.info(f"Capability registry loaded with {len(self._capability_map)} entries from {self.index_path}")

    def exists(self, capability_id: str) -> bool:
        """Check if a capability exists in the registry."""
        return capability_id in self._capability_map

    def get(self, capability_id: str) -> Optional[CapabilityEntry]:
        """Get a capability by ID."""
        return self._capability_map.get(capability_id)

    def get_all(self) -> List[CapabilityEntry]:
        """Get all capabilities."""
        return self._registry.capabilities if self._registry else []

    def get_by_domain(self, domain: str) -> List[CapabilityEntry]:
        """Get all capabilities for a domain."""
        return [cap for cap in self._capability_map.values() if cap.domain == domain]

    def get_by_type(self, cap_type: CapabilityType) -> List[CapabilityEntry]:
        """Get all capabilities of a specific type."""
        return [cap for cap in self._capability_map.values() if cap.type == cap_type]

    def get_by_tag(self, tag: str) -> List[CapabilityEntry]:
        """Get all capabilities with a specific tag."""
        return [cap for cap in self._capability_map.values() if tag in cap.tags]

    def get_mfa_required(self) -> List[CapabilityEntry]:
        """Get all capabilities requiring MFA."""
        return [cap for cap in self._capability_map.values() if cap.requires_mfa]

    def matches_wildcard(self, pattern: str) -> Set[str]:
        """
        Expand wildcard patterns to matching capability IDs.
        Examples: 
          "workday.*" -> all workday capabilities
          "workday.hcm.*" -> all HCM capabilities
          "*" -> all capabilities
        """
        matches = set()
        for cap_id in self._capability_map.keys():
            if capability_matches(pattern, cap_id):
                matches.add(cap_id)
        return matches


    def get_subdomains(self, domain: str) -> Set[str]:
        """Derive subdomains for a given domain from registered capability names."""
        subdomains = set()
        prefix = domain + "."
        for cap_id in self._capability_map.keys():
            if cap_id.startswith(prefix):
                # "workday.hcm.read_employee" -> "hcm"
                remaining = cap_id[len(prefix):]
                if "." in remaining:
                    parts = remaining.split(".", 1)
                    subdomains.add(parts[0])
        return subdomains

    def validate_capability_list(self, capabilities: List[str]) -> List[str]:

        """
        Validate a list of capability strings (from policy).
        Returns list of error messages (empty if valid).
        """
        errors = []
        for cap in capabilities:
            if cap.endswith(".*") or cap == "*":
                # Wildcard - check if it matches anything
                matches = self.matches_wildcard(cap)
                if not matches:
                    errors.append(f"Wildcard pattern '{cap}' matches no capabilities")
            else:
                # Exact match
                if not self.exists(cap):
                    errors.append(f"Unknown capability: '{cap}'")
                    # Suggest similar capabilities (typo detection)
                    similar = self._find_similar(cap)
                    if similar:
                        errors.append(f"  Did you mean: {', '.join(similar[:3])}")
        return errors

    def _find_similar(self, cap_id: str) -> List[str]:
        """Find capabilities with similar names."""
        all_ids = list(self._capability_map.keys())
        return get_close_matches(cap_id, all_ids, n=3, cutoff=0.6)

    def reload(self) -> None:
        """Reload registry from disk."""
        self._load()

_registry_instance: Optional[CapabilityRegistryService] = None

def get_capability_registry(index_path: str = "config/capabilities/index.yaml") -> CapabilityRegistryService:
    """
    Get singleton registry instance.
    Allows for explicit management of the instance.
    """
    global _registry_instance
    
    # If we have an instance but index_path is different, we might need to reload or reset
    # For now, if instance exists, we return it. If it doesn't, we create it.
    if _registry_instance is None:
        _registry_instance = CapabilityRegistryService(index_path)
    return _registry_instance

def reset_capability_registry() -> None:
    """
    Reset the singleton registry instance.
    Primarily used for testing with different configurations.
    """
    global _registry_instance
    _registry_instance = None


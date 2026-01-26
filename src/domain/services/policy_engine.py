from typing import List, Optional, Union
from pydantic import BaseModel
from src.domain.entities.policy import AccessPolicy, PolicyRule, PrincipalDefinition, Environment

class PolicyEvaluationResult(BaseModel):
    allowed: bool
    policy_name: Optional[str] = None
    audit_level: str = "BASIC"
    reason: Optional[str] = None

class PolicyEngine:
    def __init__(self, policy: AccessPolicy):
        self.policy = policy

    def evaluate(
        self,
        principal_id: str,
        principal_groups: List[str],
        principal_type: str,
        capability: str,
        environment: str
    ) -> PolicyEvaluationResult:
        """
        Evaluate if a principal is allowed to perform a capability in an environment.
        Follows 'Most Specific Match Wins' logic implicitly by checking specific bindings first if multiple policies apply.
        However, standard policy engines often iterate and find the FIRST Allow.
        Our spec says: "policies matching the principal (by subject -> group -> type)".
        We will iterate through policies and check matches.
        """
        
        # 1. Filter policies matching the Environment
        env_policies = [p for p in self.policy.policies if environment in p.environments]
        
        # 2. Sort/Prioritize policies by principal match specificity:
        #    Subject Match > Group Match > Type Match
        #    We can implement this by trying to match in that order.
        
        # Strategy: Iterate through policies. If a policy matches Principal AND Capability, return ALLOW.
        # Since we only support ALLOW, the first match grants access.
        # To respect specificity, we could process them in passes, but if the spec implies a hierarchy
        # we should prefer the most specific one.
        # Let's check for Subject Matches first, then Group, then Type.
        
        # Pass 1: Subject Match
        for rule in env_policies:
            if self._matches_principal_subject(rule, principal_id):
                if self._matches_capability(rule, capability):
                    return PolicyEvaluationResult(
                        allowed=True,
                        policy_name=rule.name,
                        audit_level=rule.audit.value
                    )

        # Pass 2: Group Match
        for rule in env_policies:
             if self._matches_principal_group(rule, principal_groups):
                if self._matches_capability(rule, capability):
                    return PolicyEvaluationResult(
                        allowed=True,
                        policy_name=rule.name,
                        audit_level=rule.audit.value
                    )
        
        # Pass 3: Type Match
        for rule in env_policies:
            if self._matches_principal_type(rule, principal_type):
                if self._matches_capability(rule, capability):
                    return PolicyEvaluationResult(
                        allowed=True,
                        policy_name=rule.name,
                        audit_level=rule.audit.value
                    )

        return PolicyEvaluationResult(allowed=False, reason="No matching policy found")

    def _resolve_principal_def(self, rule: PolicyRule) -> Optional[PrincipalDefinition]:
        if isinstance(rule.principal, PrincipalDefinition):
            return rule.principal
        # It's a string reference
        return self.policy.principals.get(rule.principal)

    def _matches_principal_subject(self, rule: PolicyRule, subject: str) -> bool:
        p_def = self._resolve_principal_def(rule)
        if not p_def: return False
        return p_def.okta_subject == subject

    def _matches_principal_group(self, rule: PolicyRule, groups: List[str]) -> bool:
        p_def = self._resolve_principal_def(rule)
        if not p_def: return False
        if not p_def.okta_group: return False
        return p_def.okta_group in groups

    def _matches_principal_type(self, rule: PolicyRule, p_type: str) -> bool:
        p_def = self._resolve_principal_def(rule)
        if not p_def: return False
        # Only match on type if subject and group are NOT defined (generic type policy)
        # Or should it match if type matches?
        # The spec says: "policies matching the principal's type".
        # A principal def usually has a type.
        return p_def.type == p_type

    def _matches_capability(self, rule: PolicyRule, capability: str) -> bool:
        allowed_caps = []
        
        # Resolve capability groups
        if isinstance(rule.capabilities, str):
            # It's a group reference
            allowed_caps = self.policy.capability_groups.get(rule.capabilities, [])
        else:
            allowed_caps = rule.capabilities

        for allowed in allowed_caps:
            if self._check_wildcard_match(allowed, capability):
                return True
        return False

    def _check_wildcard_match(self, pattern: str, target: str) -> bool:
        if pattern == "*": return True
        if pattern == target: return True
        if pattern.endswith(".*"):
            prefix = pattern[:-2]
            return target.startswith(prefix + ".")
        return False

from typing import List, Optional, Union
from datetime import datetime, time as dt_time
import pytz
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
        environment: str,
        # Context for conditions
        mfa_verified: bool = False,
        token_issued_at: Optional[int] = None,
        token_expires_at: Optional[int] = None,
        request_ip: Optional[str] = None
    ) -> PolicyEvaluationResult:
        """
        Evaluate if a principal is allowed to perform a capability in an environment.
        Follows 'Most Specific Match Wins' logic implicitly by checking specific bindings first if multiple policies apply.
        However, standard policy engines often iterate and find the FIRST Allow.
        Our spec says: "policies matching the principal (by subject -> group -> type)".
        We will iterate through policies and check matches.
        """
        
        # 1. Filter policies matching the Environment
        try:
            target_env = Environment(environment)
        except ValueError:
            return PolicyEvaluationResult(allowed=False, reason=f"Invalid environment: {environment}")

        env_policies = [p for p in self.policy.policies if target_env in p.environments]
        
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
                    if self._evaluate_conditions(rule, mfa_verified, token_issued_at, token_expires_at, request_ip):
                        return PolicyEvaluationResult(
                            allowed=True,
                            policy_name=rule.name,
                            audit_level=rule.audit.value
                        )

        # Pass 2: Group Match
        for rule in env_policies:
             if self._matches_principal_group(rule, principal_groups):
                if self._matches_capability(rule, capability):
                    if self._evaluate_conditions(rule, mfa_verified, token_issued_at, token_expires_at, request_ip):
                        return PolicyEvaluationResult(
                            allowed=True,
                            policy_name=rule.name,
                            audit_level=rule.audit.value
                        )
        
        # Pass 3: Type Match
        for rule in env_policies:
            if self._matches_principal_type(rule, principal_type):
                if self._matches_capability(rule, capability):
                    if self._evaluate_conditions(rule, mfa_verified, token_issued_at, token_expires_at, request_ip):
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
        """
        Match on type ONLY if this is a generic type-based policy.
        A policy is type-based if it has no specific subject or group.
        """
        p_def = self._resolve_principal_def(rule)
        if not p_def: 
            return False
        
        # Only match on type if there's no more specific binding
        has_specific_subject = p_def.okta_subject is not None
        has_specific_group = p_def.okta_group is not None
        
        # If this policy has specific subject/group, don't match on type alone
        if has_specific_subject or has_specific_group:
            return False
        
        # This is a generic type-based policy
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

    def _evaluate_conditions(
        self,
        rule: PolicyRule,
        mfa_verified: bool,
        token_issued_at: Optional[int],
        token_expires_at: Optional[int],
        request_ip: Optional[str]
    ) -> bool:
        if not rule.conditions:
            return True

        # MFA Check
        if rule.conditions.require_mfa and not mfa_verified:
            return False

        # TTL Check
        if rule.conditions.max_ttl_seconds:
            if token_issued_at is None or token_expires_at is None:
                # If we can't verify TTL, safe default is to fail if TTL condition exists
                return False
            ttl = token_expires_at - token_issued_at
            if ttl > rule.conditions.max_ttl_seconds:
                return False

        # IP Allowlist
        if rule.conditions.ip_allowlist:
            if not request_ip:
                return False
            if request_ip not in rule.conditions.ip_allowlist:
                return False

        # Time Window
        if rule.conditions.time_window:
            # Simple implementation
            # Assumes time_window keys: start (HH:MM), end (HH:MM), timezone (str)
            # Need to parse and check.
            try:
                tw = rule.conditions.time_window
                start_str = tw.get("start")
                end_str = tw.get("end")
                tz_str = tw.get("timezone", "UTC")
                
                if start_str and end_str:
                    tz = pytz.timezone(tz_str)
                    now = datetime.now(tz)
                    current_time = now.time()
                    
                    start_time = datetime.strptime(start_str, "%H:%M").time()
                    end_time = datetime.strptime(end_str, "%H:%M").time()
                    
                    if not (start_time <= current_time <= end_time):
                        return False
            except Exception:
                # Log error? Fail safe.
                return False

        return True
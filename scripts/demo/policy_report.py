# scripts/policy_report.py

from src.adapters.filesystem.policy_loader import FilePolicyLoaderAdapter
from src.domain.services.policy_engine import PolicyEngine

loader = FilePolicyLoaderAdapter("config/policy-workday.yaml")
policy = loader.load_policy()

print("=== Policy Validation Report ===\n")
print(f"Policy Version: {policy.version}")
print(f"Last Reviewed: {policy.metadata.last_reviewed}")
print(f"Total Policies: {len(policy.policies)}\n")

print("=== Principal Types ===")
for name, principal in policy.principals.items():
    print(f"  {name}: {principal.type.value}")
    if principal.okta_subject:
        print(f"    Bound to: {principal.okta_subject}")
    if principal.okta_group:
        print(f"    Group: {principal.okta_group}")

print("\n=== Capability Coverage ===")
all_capabilities = set()
for rule in policy.policies:
    caps = (
        rule.capabilities
        if isinstance(rule.capabilities, list)
        else policy.capability_groups.get(rule.capabilities, [])
    )
    all_capabilities.update(caps)

for cap in sorted(all_capabilities):
    print(f"  ✓ {cap}")

print("\n=== Environment Safety ===")
prod_policies = [
    p for p in policy.policies if "prod" in [e.value for e in p.environments]
]
print(f"Production policies: {len(prod_policies)}")
for p in prod_policies:
    if p.conditions and p.conditions.require_mfa:
        print(f"  ✓ {p.name} requires MFA")
    else:
        print(f"  ⚠️  {p.name} does NOT require MFA")

#!/usr/bin/env python3
import sys
import os
import argparse
import yaml
import logging
from pathlib import Path
from typing import List, Dict, Set

# Ensure project root is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.domain.services.capability_registry import get_capability_registry
from src.lib.templating import get_jinja_env
from src.lib.matching import capability_matches

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def load_policy_capabilities(policy_path: str = "config/policy-workday.yaml") -> Dict[str, List[str]]:
    """
    Load policy and map capabilities to policy names.
    Returns a dict mapping capability_id to list of policy_names.
    """
    path = Path(policy_path)
    if not path.exists():
        logger.warning(f"Policy file not found: {path}")
        return {}
        
    with open(path, "r") as f:
        data = yaml.safe_load(f)
        
    policies = data.get("policies", [])
    capability_groups = data.get("capability_groups", {})
    
    cap_to_policies = {}
    
    def add_mapping(cap_pattern: str, policy_name: str):
        # We store the raw patterns from policy to match against capabilities later
        if cap_pattern not in cap_to_policies:
            cap_to_policies[cap_pattern] = []
        if policy_name not in cap_to_policies[cap_pattern]:
            cap_to_policies[cap_pattern].append(policy_name)

    for policy in policies:
        name = policy.get("name")
        caps = policy.get("capabilities", [])
        if isinstance(caps, str):
            # It's a group name
            group_caps = capability_groups.get(caps, [])
            for gc in group_caps:
                add_mapping(gc, name)
        else:
            # It's a list of patterns
            for cp in caps:
                add_mapping(cp, name)
                
    return cap_to_policies

def get_governing_policies(cap_id: str, cap_to_policies: Dict[str, List[str]]) -> List[str]:
    """Find all policies that match a specific capability ID."""
    governing = set()
    for pattern, policies in cap_to_policies.items():
        if capability_matches(pattern, cap_id):
            for p in policies:
                governing.add(p)
    return sorted(list(governing))

def validate_mermaid_flow(capability, registry):
    """
    Validate that all capabilities referenced in a Mermaid flow diagram exist in requires_capabilities.
    Returns list of errors.
    """
    errors = []
    if not capability.implementation_flow:
        return errors
        
    # Simple regex-less extraction of capability-like strings from Mermaid edge labels or nodes
    # |workday.hcm.get_employee|
    import re
    matches = re.findall(r'\|([a-z0-9._\*]+)\|', capability.implementation_flow)
    
    required = set(capability.requires_capabilities or [])
    for match in matches:
        if match not in required:
            errors.append(f"Capability '{match}' referenced in Mermaid flow but missing from requires_capabilities")
            
    # Check if all required are in flow
    for req in required:
        if f"|{req}|" not in capability.implementation_flow:
            errors.append(f"Capability '{req}' in requires_capabilities but not referenced in Mermaid flow labels")
            
    return errors

def generate_catalog(output_dir: str = "catalog", check: bool = False):
    """Generate Backstage catalog files."""
    registry = get_capability_registry()
    env = get_jinja_env()
    template = env.get_template("catalog-info.yaml.j2")
    
    cap_to_policies = load_policy_capabilities()
    capabilities = registry.get_all()
    
    output_path = Path(output_dir)
    if not check:
        output_path.mkdir(parents=True, exist_ok=True)
        
    diffs_found = False
    all_errors = []

    for cap in capabilities:
        # T011 & T012: Validation
        errors = validate_mermaid_flow(cap, registry)
        if errors:
            all_errors.extend([f"{cap.id}: {e}" for e in errors])

        # T012: Governing policies
        governing = get_governing_policies(cap.id, cap_to_policies)
        
        # Render template
        content = template.render(
            capability=cap.model_dump(mode='json'), 
            governing_policies=governing
        )
        
        # T013: Main execution loop (directory grouping)
        # workday.hcm.get_employee -> workday-hcm/get_employee.yaml
        parts = cap.id.split('.')
        if len(parts) >= 2:
            domain_dir = f"{parts[0]}-{parts[1]}"
            filename = f"{parts[-1]}.yaml"
        else:
            domain_dir = "misc"
            filename = f"{cap.id}.yaml"
            
        file_path = output_path / domain_dir / filename
        
        if check:
            if not file_path.exists():
                logger.error(f"Missing catalog file: {file_path}")
                diffs_found = True
            else:
                with open(file_path, "r") as f:
                    existing = f.read()
                if existing != content:
                    logger.error(f"Stale catalog file: {file_path}")
                    diffs_found = True
        else:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, "w") as f:
                f.write(content)
            logger.debug(f"Generated {file_path}")

    if all_errors:
        for err in all_errors:
            logger.error(err)
        if check:
            sys.exit(1)

    if check:
        logger.info("Catalog is in sync.")
    else:
        logger.info(f"Generated catalog for {len(capabilities)} capabilities in '{output_dir}/'")

def generate_monolith(output_file: str = "catalog-all.yaml"):
    """Generate all capabilities into a single YAML file."""
    registry = get_capability_registry()
    env = get_jinja_env()
    template = env.get_template("catalog-info.yaml.j2")
    cap_to_policies = load_policy_capabilities()
    capabilities = registry.get_all()
    
    with open(output_file, "w") as f:
        # Write header
        f.write("# Auto-generated monolithic catalog\n")
        
        for i, cap in enumerate(capabilities):
            errors = validate_mermaid_flow(cap, registry)
            if errors:
                for e in errors: logger.error(f"{cap.id}: {e}")
            
            governing = get_governing_policies(cap.id, cap_to_policies)
            content = template.render(
                capability=cap.model_dump(mode='json'), 
                governing_policies=governing
            )
            
            f.write("---\n")
            f.write(content)
            f.write("\n")
            
    logger.info(f"Generated monolithic catalog at {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Backstage catalog from capability registry")
    parser.add_argument("--output", "-o", default="catalog", help="Output directory")
    parser.add_argument("--check", action="store_true", help="Check if catalog is in sync without writing")
    parser.add_argument("--monolith", action="store_true", help="Generate a single catalog-all.yaml file")
    args = parser.parse_args()
    
    try:
        if args.monolith:
            generate_monolith()
        else:
            generate_catalog(args.output, args.check)
    except Exception as e:
        logger.error(f"Failed to generate catalog: {e}")
        sys.exit(1)

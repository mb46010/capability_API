def capability_matches(pattern: str, target: str) -> bool:
    """
    Unified matching logic for capabilities.
    Supports exact match, full wildcard '*', and domain wildcard 'domain.*'.
    """
    if pattern == "*":
        return True
    if not pattern.endswith(".*"):
        return pattern == target
    prefix = pattern[:-2]  # "workday.hcm.*" → "workday.hcm"
    return target == prefix or target.startswith(prefix + ".")

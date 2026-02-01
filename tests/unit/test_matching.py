from src.lib.matching import capability_matches

def test_matching_exact():
    assert capability_matches("workday.hcm.get_employee", "workday.hcm.get_employee") is True
    assert capability_matches("workday.hcm.get_employee", "workday.hcm.list_reports") is False

def test_matching_full_wildcard():
    assert capability_matches("*", "workday.hcm.get_employee") is True
    assert capability_matches("*", "any.capability") is True

def test_matching_domain_wildcard():
    # domain.*
    assert capability_matches("workday.*", "workday.hcm.get_employee") is True
    assert capability_matches("workday.*", "workday.payroll.list") is True
    assert capability_matches("workday.*", "other.domain") is False
    
    # Nested domain.*
    assert capability_matches("workday.hcm.*", "workday.hcm.get_employee") is True
    assert capability_matches("workday.hcm.*", "workday.hcm.nested.op") is True
    assert capability_matches("workday.hcm.*", "workday.payroll.list") is False

def test_matching_boundary_safety():
    # Ensure workday_evil doesn't match workday.*
    assert capability_matches("workday.*", "workday") is True
    assert capability_matches("workday.*", "workday.anything") is True
    assert capability_matches("workday.*", "workday_evil") is False
    assert capability_matches("workday.hcm.*", "workday.hcm_plus") is False

def test_matching_invalid_wildcard_treated_as_exact():
    # Only .* suffix counts as wildcard
    assert capability_matches("workday*", "workday.hcm") is False
    assert capability_matches("workday*", "workday*") is True
    assert capability_matches("workday.", "workday.hcm") is False

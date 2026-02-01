import pytest
from src.domain.services.policy_verifier import VerificationReport, TestResult
from src.domain.services.policy_report_generator import PolicyReportGenerator

def test_generate_html_report():
    report = VerificationReport(
        total_tests=2,
        passed=1,
        failed=1,
        results=[
            TestResult(test_id="T1", test_name="Pass test", passed=True, expected_allowed=True, actual_allowed=True),
            TestResult(test_id="T2", test_name="Fail test", passed=False, expected_allowed=False, actual_allowed=True, error_message="Mismatch")
        ],
        failed_tests=[
            TestResult(test_id="T2", test_name="Fail test", passed=False, expected_allowed=False, actual_allowed=True, error_message="Mismatch")
        ]
    )
    
    generator = PolicyReportGenerator()
    html = generator.generate_html(report)
    
    assert "Policy Verification Report" in html
    assert "Pass Rate" in html
    assert "Pass test" in html
    assert "Fail test" in html
    assert "Mismatch" in html

import time
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from pathlib import Path

from src.domain.entities.policy_test import PolicyTestSuite, PolicyTestCase, TestPrincipal, TestRequest
from src.domain.services.policy_engine import PolicyEngine
from src.domain.ports.policy_loader import PolicyLoaderPort
from src.domain.ports.scenario_loader import ScenarioLoaderPort


@dataclass
class TestResult:

    """Result of a single test case execution."""
    test_id: str
    test_name: str
    passed: bool
    expected_allowed: bool
    actual_allowed: bool
    expected_policy: Optional[str] = None
    actual_policy: Optional[str] = None
    expected_audit: Optional[str] = None
    actual_audit: Optional[str] = None
    error_message: Optional[str] = None
    execution_time_ms: float = 0.0


@dataclass
class VerificationReport:
    """Aggregate report of all test executions."""
    total_tests: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    pass_rate: float = 0.0
    execution_time_ms: float = 0.0
    results: List[TestResult] = field(default_factory=list)
    failed_tests: List[TestResult] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return self.failed == 0


class PolicyVerificationService:
    """
    Service for verifying policies against test scenarios.
    """

    def __init__(self, policy_loader: PolicyLoaderPort, scenario_loader: ScenarioLoaderPort):
        # Load policy
        policy = policy_loader.load_policy()
        self.policy_engine = PolicyEngine(policy)
        self.scenario_loader = scenario_loader


    def run_test_case(self, test: PolicyTestCase, suite_defaults: Optional[Dict[str, Any]] = None) -> TestResult:
        """Execute a single test case."""
        start_time = time.time()
        
        # Merge defaults
        principal_data = (suite_defaults or {}).get("principal", {})
        if test.principal:
            principal_data.update(test.principal.model_dump(exclude_none=True))
        principal = TestPrincipal(**principal_data)

        request_data = (suite_defaults or {}).get("request", {})
        if test.request:
            request_data.update(test.request.model_dump(exclude_none=True))
        request = TestRequest(**request_data)

        # Check environment override
        expected_allowed = test.expected.allowed
        if test.expected.environments and request.environment in test.expected.environments:
            expected_allowed = test.expected.environments[request.environment]

        try:
            # Evaluate policy
            evaluation = self.policy_engine.evaluate(
                principal_id=principal.subject,
                principal_groups=principal.groups,
                principal_type=principal.type,
                capability=request.capability,
                environment=request.environment,
                mfa_verified=principal.mfa_verified,
                token_issued_at=principal.token_issued_at,
                token_expires_at=principal.token_expires_at,
                request_ip=principal.request_ip,
            )

            execution_time = (time.time() - start_time) * 1000

            # Check if result matches expectation
            actual_allowed = evaluation.allowed
            passed = True
            error_message = None

            # 1. Check ALLOW/DENY matches
            if actual_allowed != expected_allowed:
                passed = False
                if expected_allowed:
                    error_message = f"Expected ALLOW but got DENY. Reason: {evaluation.reason}"
                else:
                    error_message = f"Expected DENY but got ALLOW. Policy: {evaluation.policy_name}"

            # 2. Check policy name matches (for positive tests)
            if passed and test.expected.policy_matched and evaluation.policy_name != test.expected.policy_matched:
                # Warning only if result is still allowed, but spec says "MUST verify policy matched"
                # To be strict, we mark as failed if it matched the WRONG policy.
                passed = False
                error_message = f"Policy name mismatch: expected '{test.expected.policy_matched}', got '{evaluation.policy_name}'"

            # 3. Check audit level (FR-005)
            if passed and test.expected.audit_level and evaluation.audit_level != test.expected.audit_level:
                passed = False
                error_message = f"Audit level mismatch: expected '{test.expected.audit_level}', got '{evaluation.audit_level}'"

            # 4. Check denial reason (for negative tests)
            if passed and not expected_allowed and test.expected.reason_contains:
                if not evaluation.reason or test.expected.reason_contains.lower() not in evaluation.reason.lower():
                    passed = False
                    error_message = f"Denial reason doesn't contain '{test.expected.reason_contains}'. Got: {evaluation.reason}"

            return TestResult(
                test_id=test.id,
                test_name=test.name,
                passed=passed,
                expected_allowed=expected_allowed,
                actual_allowed=actual_allowed,
                expected_policy=test.expected.policy_matched,
                actual_policy=evaluation.policy_name,
                expected_audit=test.expected.audit_level,
                actual_audit=evaluation.audit_level,
                error_message=error_message,
                execution_time_ms=execution_time,
            )

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            return TestResult(
                test_id=test.id,
                test_name=test.name,
                passed=False,
                expected_allowed=expected_allowed,
                actual_allowed=False,
                error_message=f"Exception during evaluation: {str(e)}",
                execution_time_ms=execution_time,
            )

    def run_test_suite(self, suite: PolicyTestSuite) -> VerificationReport:
        """Execute all tests in a suite."""
        start_time = time.time()
        results = []
        skipped = 0

        for test in suite.test_cases:
            if test.skip:
                skipped += 1
                continue

            result = self.run_test_case(test, suite.defaults)
            results.append(result)

        execution_time = (time.time() - start_time) * 1000
        passed = [r for r in results if r.passed]
        failed = [r for r in results if not r.passed]

        return VerificationReport(
            total_tests=len(results) + skipped,
            passed=len(passed),
            failed=len(failed),
            skipped=skipped,
            pass_rate=(len(passed) / len(results) * 100) if results else 0,
            execution_time_ms=execution_time,
            results=results,
            failed_tests=failed,
        )

    def run_all_tests(self, scenarios_dir: str) -> VerificationReport:
        """Execute all test suites in directory."""
        suites = self.scenario_loader.load_all_test_suites(scenarios_dir)
        all_results = []
        total_skipped = 0
        start_time = time.time()

        for suite in suites:
            report = self.run_test_suite(suite)
            all_results.extend(report.results)
            total_skipped += report.skipped

        execution_time = (time.time() - start_time) * 1000
        passed = [r for r in all_results if r.passed]
        failed = [r for r in all_results if not r.passed]

        return VerificationReport(
            total_tests=len(all_results) + total_skipped,
            passed=len(passed),
            failed=len(failed),
            skipped=total_skipped,
            pass_rate=(len(passed) / len(all_results) * 100) if all_results else 0,
            execution_time_ms=execution_time,
            results=all_results,
            failed_tests=failed,
        )

    def to_json(self, report: VerificationReport) -> str:
        """Export report to JSON string."""
        import json
        data = {
            "summary": {
                "total": report.total_tests,
                "passed": report.passed,
                "failed": report.failed,
                "skipped": report.skipped,
                "pass_rate": report.pass_rate,
                "execution_time_ms": report.execution_time_ms
            },
            "results": [
                {
                    "id": r.test_id,
                    "name": r.test_name,
                    "passed": r.passed,
                    "expected_allowed": r.expected_allowed,
                    "actual_allowed": r.actual_allowed,
                    "error": r.error_message
                } for r in report.results
            ]
        }
        return json.dumps(data, indent=2)

    def to_junit_xml(self, report: VerificationReport) -> str:
        """Export report to JUnit XML string."""
        from xml.etree import ElementTree as ET
        
        testsuites = ET.Element("testsuites", {
            "name": "Policy Verification",
            "tests": str(report.total_tests),
            "failures": str(report.failed),
            "skipped": str(report.skipped),
            "time": str(report.execution_time_ms / 1000)
        })
        
        testsuite = ET.SubElement(testsuites, "testsuite", {
            "name": "All Scenarios",
            "tests": str(report.total_tests),
            "failures": str(report.failed),
            "skipped": str(report.skipped),
            "time": str(report.execution_time_ms / 1000)
        })
        
        for r in report.results:
            testcase = ET.SubElement(testsuite, "testcase", {
                "name": r.test_name,
                "classname": f"policy.{r.test_id}",
                "time": str(r.execution_time_ms / 1000)
            })
            
            if not r.passed:
                failure = ET.SubElement(testcase, "failure", {
                    "message": r.error_message or "Test failed"
                })
                failure.text = f"Expected: {r.expected_allowed}, Got: {r.actual_allowed}"
                
        return ET.tostring(testsuites, encoding="unicode")


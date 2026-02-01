# Policy Verification Framework PRD

**Version**: 1.0  
**Status**: Ready for Implementation  
**Owner**: HR AI Platform Security Team  
**Target**: Pre-Demo Quality Gate / Continuous Compliance  
**Estimated Effort**: 8-12 hours

---

## Executive Summary

**Problem**: The HR AI Platform has sophisticated policy-based authorization, but **no automated way to verify policies enforce intended access**. This creates three critical risks:

1. **Silent Security Holes**: Over-permissive policies grant unintended access without detection
2. **Access Outages**: Missing policies accidentally deny legitimate user access
3. **Regression Risk**: Policy changes can break existing access patterns without warning

**Solution**: Implement a declarative policy verification framework that:
- Defines expected access patterns as test scenarios (YAML)
- Automatically tests policies against scenarios at startup and in CI/CD
- Generates compliance reports for stakeholders
- Prevents deployment of policies that violate security requirements

**Impact**:
- **100% Coverage**: Every policy rule verified with positive and negative test cases
- **Zero Trust Gap**: Policies proven to enforce least-privilege before deployment
- **Audit Trail**: Machine-readable evidence of policy compliance for security reviews

---

## Goals & Non-Goals

### Goals ✅

1. **Declarative Testing**: Security requirements expressed as YAML test scenarios
2. **Automated Verification**: Policies tested on every commit via CI/CD
3. **Comprehensive Coverage**: Both ALLOW and DENY cases for every capability
4. **Regression Prevention**: Existing access patterns preserved across policy changes
5. **Compliance Reporting**: Generate audit-ready reports for stakeholders
6. **Developer Friendly**: Clear error messages when verification fails

### Non-Goals ❌

1. **Runtime Policy Enforcement**: Framework tests policies, doesn't enforce them (that's PolicyEngine's job)
2. **Performance Testing**: Not testing policy evaluation speed (covered by unit tests)
3. **Dynamic Policy Generation**: Not generating policies from scenarios (one-way: scenarios verify policies)
4. **Production Monitoring**: Not monitoring actual access patterns (covered by audit logs)
5. **Policy Recommendation**: Not suggesting policy improvements (human-defined requirements)

---

## Background & Context

### Current State (Gaps)

**Gap 1: No Proof Policies Work**

**Example Scenario**:
```yaml
# config/policy-workday.yaml
policies:
  - name: "ai-agents-limited-access"
    principal: {type: AI_AGENT}
    capabilities: ["workday.*"]  # ❌ Too broad! Should be workday.hcm.* only
    effect: "ALLOW"
```

**Current Behavior**:
- ✅ Policy is syntactically valid (loads successfully)
- ✅ Capability registry validation passes (workday.* is valid)
- ❌ **Security violation**: AI agents can now access compensation data
- ❌ **No detection**: No automated test catches this

**Desired Behavior**:
- ❌ Verification fails with error: `AI agents granted access to workday.payroll.get_compensation (violation of security requirement SEC-003)`

---

**Gap 2: Regression Risk on Policy Changes**

**Scenario**: Developer updates policy to add new capability
```yaml
# Before (working)
capabilities: ["workday.hcm.get_employee", "workday.time.get_balance"]

# After (breaks existing access)
capabilities: ["workday.hcm.*"]  # Forgot to include time domain
```

**Current Behavior**:
- User gets 403 at runtime
- Customer support ticket filed
- Rollback required

**Desired Behavior**:
- CI fails with: `Policy change breaks existing access: employees can no longer access workday.time.get_balance`

---

**Gap 3: No Evidence for Compliance Audits**

**Auditor Question**: "How do you verify AI agents cannot access payroll data?"

**Current Answer**: "We have a policy for that" *(trust us)*

**Desired Answer**: "Here's our test suite showing AI agents denied payroll access across 15 test scenarios, verified on every deployment"

---

### Architecture Context

**Current Testing Approach**:
```
┌─────────────────────┐
│ Policy YAML         │ ← Human writes policy
└──────────┬──────────┘
           │
           ↓ (no verification)
┌─────────────────────┐
│ PolicyEngine        │ ← Enforces at runtime
└──────────┬──────────┘
           │
           ↓
┌─────────────────────┐
│ Production          │ ← Hope it works correctly
└─────────────────────┘
```

**Target Testing Approach**:
```
┌─────────────────────┐
│ Policy YAML         │ ← Human writes policy
└──────────┬──────────┘
           │
           ↓
┌─────────────────────────────────┐
│ Policy Verification Framework   │ ← Tests against scenarios
│ - Loads test scenarios          │
│ - Runs PolicyEngine for each    │
│ - Validates ALLOW/DENY correct  │
└──────────┬──────────────────────┘
           │
           ├──→ ✅ All tests pass → Deploy
           └──→ ❌ Test fails → Block deployment
```

---

## Requirements

### FR-001: Test Scenario Schema

**Specification**: Test scenarios defined in YAML with comprehensive metadata.

**File Structure**:
```
tests/policy/
├── scenarios/
│   ├── ai_agents.yaml           # AI agent access tests
│   ├── employees.yaml           # Employee self-service tests
│   ├── managers.yaml            # Manager-specific tests
│   ├── admin.yaml               # Admin access tests
│   ├── mfa_requirements.yaml    # MFA enforcement tests
│   └── negative_tests.yaml      # Deny cases
└── reports/                     # Generated test reports
    └── latest.html
```

**Scenario Schema** (`tests/policy/scenarios/employees.yaml`):
```yaml
version: "1.0"
metadata:
  name: "Employee Self-Service Access Tests"
  owner: "security-team"
  description: "Verify employees can access own data but not others' data"
  security_requirement: "SEC-001"  # Reference to security requirement doc
  last_updated: "2026-01-31"

test_cases:
  # Positive Test Cases (Expected: ALLOW)
  - id: "EMP-001"
    name: "Employee can view own profile"
    category: "positive"
    principal:
      type: "HUMAN"
      subject: "EMP001"
      groups: ["employees"]
    request:
      capability: "workday.hcm.get_employee"
      parameters:
        employee_id: "EMP001"
      environment: "prod"
    expected:
      allowed: true
      policy_matched: "employee-self-service"
      audit_level: "BASIC"
    
  - id: "EMP-002"
    name: "Employee can view own PTO balance"
    category: "positive"
    principal:
      type: "HUMAN"
      subject: "EMP001"
      groups: ["employees"]
    request:
      capability: "workday.time.get_balance"
      parameters:
        employee_id: "EMP001"
      environment: "prod"
    expected:
      allowed: true
      policy_matched: "employee-self-service"
  
  - id: "EMP-003"
    name: "Employee can request time off"
    category: "positive"
    principal:
      type: "HUMAN"
      subject: "EMP001"
      groups: ["employees"]
    request:
      capability: "workday.time.request"
      parameters:
        employee_id: "EMP001"
        type: "PTO"
        start_date: "2026-02-10"
        end_date: "2026-02-14"
      environment: "prod"
    expected:
      allowed: true
  
  # Negative Test Cases (Expected: DENY)
  - id: "EMP-101"
    name: "Employee CANNOT view other employee's profile"
    category: "negative"
    principal:
      type: "HUMAN"
      subject: "EMP001"
      groups: ["employees"]
    request:
      capability: "workday.hcm.get_employee"
      parameters:
        employee_id: "EMP042"  # Different employee
      environment: "prod"
    expected:
      allowed: false
      reason_contains: "own data only"
    
  - id: "EMP-102"
    name: "Employee CANNOT view compensation without MFA"
    category: "negative"
    principal:
      type: "HUMAN"
      subject: "EMP001"
      groups: ["employees"]
      mfa_verified: false
    request:
      capability: "workday.payroll.get_compensation"
      parameters:
        employee_id: "EMP001"
      environment: "prod"
    expected:
      allowed: false
      reason_contains: "MFA required"
  
  - id: "EMP-103"
    name: "Employee CANNOT approve time off (manager-only)"
    category: "negative"
    principal:
      type: "HUMAN"
      subject: "EMP001"
      groups: ["employees"]
    request:
      capability: "workday.time.approve"
      parameters:
        request_id: "TOR-001"
      environment: "prod"
    expected:
      allowed: false
```

**Pydantic Schema** (`src/domain/entities/policy_test.py`):
```python
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum

class TestCategory(str, Enum):
    POSITIVE = "positive"  # Expected to allow
    NEGATIVE = "negative"  # Expected to deny
    EDGE_CASE = "edge_case"  # Boundary conditions

class TestPrincipal(BaseModel):
    type: str = Field(description="Principal type (HUMAN, MACHINE, AI_AGENT)")
    subject: str = Field(description="Principal subject/ID")
    groups: List[str] = Field(default=[], description="Principal groups")
    mfa_verified: bool = Field(default=False, description="MFA status")
    token_issued_at: Optional[int] = Field(None, description="Token issue timestamp (for TTL tests)")
    token_expires_at: Optional[int] = Field(None, description="Token expiry timestamp")
    request_ip: Optional[str] = Field(None, description="Request IP address")

class TestRequest(BaseModel):
    capability: str = Field(description="Capability being tested")
    parameters: Dict[str, Any] = Field(default={}, description="Request parameters")
    environment: str = Field(description="Environment (local, dev, prod)")

class ExpectedResult(BaseModel):
    allowed: bool = Field(description="Expected allow/deny result")
    policy_matched: Optional[str] = Field(None, description="Expected policy name that grants access")
    audit_level: Optional[str] = Field(None, description="Expected audit level (BASIC, VERBOSE)")
    reason_contains: Optional[str] = Field(None, description="Expected substring in denial reason")

class PolicyTestCase(BaseModel):
    id: str = Field(description="Unique test case ID (e.g., EMP-001)")
    name: str = Field(description="Human-readable test name")
    category: TestCategory = Field(description="Test category")
    principal: TestPrincipal = Field(description="Principal making the request")
    request: TestRequest = Field(description="Request details")
    expected: ExpectedResult = Field(description="Expected outcome")
    skip: bool = Field(default=False, description="Skip this test (with reason in comments)")
    tags: List[str] = Field(default=[], description="Tags for filtering (e.g., ['critical', 'regression'])")

class PolicyTestMetadata(BaseModel):
    name: str
    owner: str
    description: str
    security_requirement: Optional[str] = Field(None, description="Reference to security doc")
    last_updated: str

class PolicyTestSuite(BaseModel):
    version: str
    metadata: PolicyTestMetadata
    test_cases: List[PolicyTestCase]
```

**Acceptance Criteria**:
- ✅ Schema validates all test scenario fields
- ✅ Test cases have unique IDs
- ✅ Both positive and negative cases defined
- ✅ MFA, environment, parameter variations covered
- ✅ Security requirement references tracked

---

### FR-002: Test Runner Service

**Specification**: Service to execute policy verification tests.

**Implementation** (`src/domain/services/policy_verifier.py`):
```python
import time
from typing import List, Dict, Tuple
from dataclasses import dataclass
from pathlib import Path
import yaml

from src.domain.entities.policy_test import PolicyTestSuite, PolicyTestCase
from src.domain.services.policy_engine import PolicyEngine
from src.adapters.filesystem.policy_loader import FilePolicyLoaderAdapter

@dataclass
class TestResult:
    """Result of a single test case execution."""
    test_id: str
    test_name: str
    passed: bool
    expected_allowed: bool
    actual_allowed: bool
    expected_policy: Optional[str]
    actual_policy: Optional[str]
    error_message: Optional[str]
    execution_time_ms: float

@dataclass
class VerificationReport:
    """Aggregate report of all test executions."""
    total_tests: int
    passed: int
    failed: int
    skipped: int
    pass_rate: float
    execution_time_ms: float
    results: List[TestResult]
    failed_tests: List[TestResult]
    
    @property
    def success(self) -> bool:
        return self.failed == 0

class PolicyVerificationService:
    """
    Service for verifying policies against test scenarios.
    
    Usage:
        verifier = PolicyVerificationService("config/policy-workday.yaml")
        report = verifier.run_all_tests("tests/policy/scenarios/")
        
        if not report.success:
            print(f"❌ {report.failed} tests failed")
            for result in report.failed_tests:
                print(f"  - {result.test_name}: {result.error_message}")
    """
    
    def __init__(self, policy_path: str):
        # Load policy
        loader = FilePolicyLoaderAdapter(policy_path)
        policy = loader.load_policy()
        self.policy_engine = PolicyEngine(policy)
    
    def load_test_suite(self, scenario_path: str) -> PolicyTestSuite:
        """Load test scenarios from YAML file."""
        with open(scenario_path, "r") as f:
            data = yaml.safe_load(f)
        return PolicyTestSuite(**data)
    
    def load_all_test_suites(self, scenarios_dir: str) -> List[PolicyTestSuite]:
        """Load all test suites from directory."""
        scenarios_path = Path(scenarios_dir)
        suites = []
        
        for yaml_file in scenarios_path.glob("*.yaml"):
            suite = self.load_test_suite(str(yaml_file))
            suites.append(suite)
        
        return suites
    
    def run_test_case(self, test: PolicyTestCase) -> TestResult:
        """Execute a single test case."""
        start_time = time.time()
        
        try:
            # Evaluate policy
            evaluation = self.policy_engine.evaluate(
                principal_id=test.principal.subject,
                principal_groups=test.principal.groups,
                principal_type=test.principal.type,
                capability=test.request.capability,
                environment=test.request.environment,
                mfa_verified=test.principal.mfa_verified,
                token_issued_at=test.principal.token_issued_at,
                token_expires_at=test.principal.token_expires_at,
                request_ip=test.principal.request_ip,
            )
            
            execution_time = (time.time() - start_time) * 1000
            
            # Check if result matches expectation
            actual_allowed = evaluation.allowed
            expected_allowed = test.expected.allowed
            
            passed = True
            error_message = None
            
            # Check ALLOW/DENY matches
            if actual_allowed != expected_allowed:
                passed = False
                if expected_allowed:
                    error_message = f"Expected ALLOW but got DENY. Reason: {evaluation.reason}"
                else:
                    error_message = f"Expected DENY but got ALLOW. Policy: {evaluation.policy_name}"
            
            # Check policy name matches (for positive tests)
            if passed and test.expected.policy_matched and evaluation.policy_name != test.expected.policy_matched:
                # Warning only, not failure (policy name might change)
                error_message = f"Policy name mismatch: expected '{test.expected.policy_matched}', got '{evaluation.policy_name}'"
            
            # Check denial reason contains expected substring (for negative tests)
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
                error_message=error_message,
                execution_time_ms=execution_time,
            )
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            return TestResult(
                test_id=test.id,
                test_name=test.name,
                passed=False,
                expected_allowed=test.expected.allowed,
                actual_allowed=False,
                expected_policy=None,
                actual_policy=None,
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
            
            result = self.run_test_case(test)
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
        suites = self.load_all_test_suites(scenarios_dir)
        
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
```

**Acceptance Criteria**:
- ✅ Test runner loads YAML scenarios
- ✅ Each test case executed against PolicyEngine
- ✅ ALLOW/DENY results validated
- ✅ Execution time tracked
- ✅ Aggregate report generated

---

### FR-003: CLI Test Runner

**Specification**: Command-line tool for running policy verification.

**Implementation** (`scripts/verify-policy`):
```bash
#!/usr/bin/env python3
"""
Policy Verification CLI

Usage:
    ./scripts/verify-policy run [--scenarios=<dir>] [--format=<format>]
    ./scripts/verify-policy run-single <scenario-file>
    ./scripts/verify-policy report [--output=<file>]
    ./scripts/verify-policy list-scenarios
"""

import sys
import argparse
from pathlib import Path
from tabulate import tabulate
import json

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.domain.services.policy_verifier import PolicyVerificationService

def cmd_run(args):
    """Run all policy verification tests."""
    verifier = PolicyVerificationService(args.policy)
    report = verifier.run_all_tests(args.scenarios)
    
    # Print summary
    print("=" * 60)
    print("Policy Verification Report")
    print("=" * 60)
    print(f"Total Tests:  {report.total_tests}")
    print(f"Passed:       {report.passed} ✅")
    print(f"Failed:       {report.failed} ❌")
    print(f"Skipped:      {report.skipped} ⏭️")
    print(f"Pass Rate:    {report.pass_rate:.1f}%")
    print(f"Execution:    {report.execution_time_ms:.0f}ms")
    print("=" * 60)
    
    # Format output
    if args.format == "table":
        if report.failed_tests:
            print("\n❌ Failed Tests:")
            headers = ["ID", "Test Name", "Expected", "Actual", "Error"]
            rows = []
            for result in report.failed_tests:
                rows.append([
                    result.test_id,
                    result.test_name[:40],
                    "ALLOW" if result.expected_allowed else "DENY",
                    "ALLOW" if result.actual_allowed else "DENY",
                    result.error_message[:60] if result.error_message else ""
                ])
            print(tabulate(rows, headers=headers, tablefmt="grid"))
        else:
            print("\n✅ All tests passed!")
    
    elif args.format == "json":
        output = {
            "summary": {
                "total": report.total_tests,
                "passed": report.passed,
                "failed": report.failed,
                "skipped": report.skipped,
                "pass_rate": report.pass_rate,
            },
            "failed_tests": [
                {
                    "id": r.test_id,
                    "name": r.test_name,
                    "error": r.error_message,
                }
                for r in report.failed_tests
            ]
        }
        print(json.dumps(output, indent=2))
    
    elif args.format == "junit":
        # Generate JUnit XML for CI integration
        generate_junit_xml(report, args.output or "test-results.xml")
        print(f"JUnit XML written to {args.output or 'test-results.xml'}")
    
    # Exit code: 0 if all passed, 1 if any failed
    sys.exit(0 if report.success else 1)

def cmd_run_single(args):
    """Run tests from a single scenario file."""
    verifier = PolicyVerificationService(args.policy)
    suite = verifier.load_test_suite(args.scenario_file)
    report = verifier.run_test_suite(suite)
    
    print(f"\nTest Suite: {suite.metadata.name}")
    print(f"Passed: {report.passed}/{report.total_tests}")
    
    for result in report.failed_tests:
        print(f"  ❌ {result.test_name}: {result.error_message}")
    
    sys.exit(0 if report.success else 1)

def cmd_list_scenarios(args):
    """List all available test scenarios."""
    scenarios_path = Path(args.scenarios)
    
    print("Available Test Scenarios:")
    for yaml_file in sorted(scenarios_path.glob("*.yaml")):
        verifier = PolicyVerificationService(args.policy)
        suite = verifier.load_test_suite(str(yaml_file))
        print(f"  📄 {yaml_file.name}")
        print(f"     {suite.metadata.description}")
        print(f"     Tests: {len(suite.test_cases)}")

def generate_junit_xml(report, output_path):
    """Generate JUnit XML format for CI integration."""
    from xml.etree import ElementTree as ET
    
    testsuites = ET.Element("testsuites")
    testsuite = ET.SubElement(testsuites, "testsuite", {
        "name": "Policy Verification",
        "tests": str(report.total_tests),
        "failures": str(report.failed),
        "skipped": str(report.skipped),
        "time": str(report.execution_time_ms / 1000),
    })
    
    for result in report.results:
        testcase = ET.SubElement(testsuite, "testcase", {
            "name": result.test_name,
            "classname": f"policy.{result.test_id}",
            "time": str(result.execution_time_ms / 1000),
        })
        
        if not result.passed:
            failure = ET.SubElement(testcase, "failure", {
                "message": result.error_message or "Test failed"
            })
            failure.text = f"Expected: {result.expected_allowed}, Got: {result.actual_allowed}"
    
    tree = ET.ElementTree(testsuites)
    tree.write(output_path, encoding="utf-8", xml_declaration=True)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Policy Verification CLI")
    parser.add_argument(
        "--policy",
        default="config/policy-workday.yaml",
        help="Path to policy YAML"
    )
    parser.add_argument(
        "--scenarios",
        default="tests/policy/scenarios/",
        help="Path to test scenarios directory"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # run command
    run_parser = subparsers.add_parser("run", help="Run all verification tests")
    run_parser.add_argument(
        "--format",
        choices=["table", "json", "junit"],
        default="table",
        help="Output format"
    )
    run_parser.add_argument("--output", help="Output file for junit format")
    
    # run-single command
    single_parser = subparsers.add_parser("run-single", help="Run single scenario file")
    single_parser.add_argument("scenario_file", help="Path to scenario YAML")
    
    # list-scenarios command
    list_parser = subparsers.add_parser("list-scenarios", help="List available scenarios")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    {
        "run": cmd_run,
        "run-single": cmd_run_single,
        "list-scenarios": cmd_list_scenarios,
    }[args.command](args)
```

**Usage Examples**:
```bash
# Run all tests
./scripts/verify-policy run

# Run with JSON output
./scripts/verify-policy run --format json

# Generate JUnit XML for CI
./scripts/verify-policy run --format junit --output results.xml

# Run single scenario file
./scripts/verify-policy run-single tests/policy/scenarios/ai_agents.yaml

# List all scenarios
./scripts/verify-policy list-scenarios
```

**Acceptance Criteria**:
- ✅ CLI runs all test scenarios
- ✅ Failed tests displayed with details
- ✅ Exit code 0 if passed, 1 if failed
- ✅ JUnit XML format for CI integration
- ✅ Progress indicators for long test runs

---

### FR-004: CI/CD Integration

**Specification**: Policy verification runs automatically in CI pipeline.

**GitHub Actions Workflow** (`.github/workflows/policy-verification.yml`):
```yaml
name: Policy Verification

on:
  pull_request:
    paths:
      - 'config/policy-*.yaml'
      - 'tests/policy/scenarios/**'
      - 'src/domain/services/policy_engine.py'
  push:
    branches: [main]

jobs:
  verify-policy:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      
      - name: Run policy verification
        id: verify
        run: |
          ./scripts/verify-policy run --format junit --output test-results.xml
        continue-on-error: true
      
      - name: Publish test results
        uses: EnricoMi/publish-unit-test-result-action@v2
        if: always()
        with:
          files: test-results.xml
      
      - name: Comment on PR (if failures)
        if: steps.verify.outcome == 'failure' && github.event_name == 'pull_request'
        uses: actions/github-script@v6
        with:
          script: |
            const fs = require('fs');
            const results = fs.readFileSync('test-results.xml', 'utf8');
            
            // Parse failures from JUnit XML
            const failureMatch = results.match(/failures="(\d+)"/);
            const failures = failureMatch ? failureMatch[1] : '0';
            
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: `## ❌ Policy Verification Failed\n\n${failures} test(s) failed. Please review the test results.`
            });
      
      - name: Fail if verification failed
        if: steps.verify.outcome == 'failure'
        run: exit 1
```

**Pre-Commit Hook** (`.git/hooks/pre-commit`):
```bash
#!/bin/bash
# Verify policy before commit

# Only run if policy or scenarios changed
if git diff --cached --name-only | grep -qE '^(config/policy|tests/policy/scenarios)'; then
    echo "Running policy verification..."
    ./scripts/verify-policy run --format table || {
        echo ""
        echo "❌ Policy verification failed - commit rejected"
        echo "Run './scripts/verify-policy run' to see details"
        exit 1
    }
    echo "✅ Policy verification passed"
fi
```

**Acceptance Criteria**:
- ✅ CI runs on policy/scenario changes
- ✅ PR blocked if tests fail
- ✅ Test results published to PR
- ✅ Pre-commit hook prevents bad commits
- ✅ JUnit XML uploaded as artifact

---

### FR-005: Comprehensive Test Scenarios

**Specification**: Test scenarios cover all security requirements.

**Test Coverage Requirements**:

| Domain | Positive Tests | Negative Tests | Total |
|--------|---------------|----------------|-------|
| **AI Agents** | 5 (can access HCM basic) | 10 (cannot access payroll, manager-only, write ops) | 15 |
| **Employees** | 8 (self-service CRUD) | 12 (cannot access others' data, manager ops) | 20 |
| **Managers** | 10 (team visibility, approvals) | 8 (cannot access other teams, HR admin ops) | 18 |
| **Admins** | 12 (full access) | 5 (MFA requirements, environment restrictions) | 17 |
| **MFA Requirements** | 6 (compensation with MFA) | 6 (compensation without MFA) | 12 |
| **Environment Isolation** | 5 (prod restrictions) | 5 (dev/local relaxed) | 10 |
| **Edge Cases** | 8 (token expiry, wildcards) | 7 (malformed requests) | 15 |
| **TOTAL** | **54** | **53** | **107** |

**AI Agent Tests** (`tests/policy/scenarios/ai_agents.yaml`):
```yaml
version: "1.0"
metadata:
  name: "AI Agent Access Control Tests"
  owner: "security-team"
  description: "Verify AI agents have limited, read-only access"
  security_requirement: "SEC-003"

test_cases:
  # Positive: What AI agents CAN do
  - id: "AI-001"
    name: "AI can read employee profiles (filtered)"
    category: "positive"
    principal:
      type: "AI_AGENT"
      subject: "agent-assistant@local.test"
    request:
      capability: "workday.hcm.get_employee"
      parameters: {"employee_id": "EMP001"}
      environment: "prod"
    expected:
      allowed: true
      policy_matched: "ai-agents-limited-access"
  
  - id: "AI-002"
    name: "AI can view org chart"
    category: "positive"
    principal:
      type: "AI_AGENT"
      subject: "agent-assistant@local.test"
    request:
      capability: "workday.hcm.get_org_chart"
      parameters: {"root_id": "EMP100"}
      environment: "prod"
    expected:
      allowed: true
  
  - id: "AI-003"
    name: "AI can view manager chain"
    category: "positive"
    principal:
      type: "AI_AGENT"
      subject: "agent-assistant@local.test"
    request:
      capability: "workday.hcm.get_manager_chain"
      parameters: {"employee_id": "EMP001"}
      environment: "prod"
    expected:
      allowed: true
  
  - id: "AI-004"
    name: "AI can view PTO balances"
    category: "positive"
    principal:
      type: "AI_AGENT"
      subject: "agent-assistant@local.test"
    request:
      capability: "workday.time.get_balance"
      parameters: {"employee_id": "EMP001"}
      environment: "prod"
    expected:
      allowed: true
  
  - id: "AI-005"
    name: "AI can update contact info (no-MFA write)"
    category: "positive"
    principal:
      type: "AI_AGENT"
      subject: "agent-assistant@local.test"
    request:
      capability: "workday.hcm.update_contact_info"
      parameters: 
        employee_id: "EMP001"
        updates: {"personal_email": "new@example.com"}
      environment: "prod"
    expected:
      allowed: true

  # Negative: What AI agents CANNOT do
  - id: "AI-101"
    name: "AI CANNOT access compensation data"
    category: "negative"
    principal:
      type: "AI_AGENT"
      subject: "agent-assistant@local.test"
    request:
      capability: "workday.payroll.get_compensation"
      parameters: {"employee_id": "EMP001"}
      environment: "prod"
    expected:
      allowed: false
      reason_contains: "not authorized"
  
  - id: "AI-102"
    name: "AI CANNOT access pay statements"
    category: "negative"
    principal:
      type: "AI_AGENT"
      subject: "agent-assistant@local.test"
    request:
      capability: "workday.payroll.get_pay_statement"
      parameters: {"statement_id": "PAY-2026-01"}
      environment: "prod"
    expected:
      allowed: false
  
  - id: "AI-103"
    name: "AI CANNOT approve time off requests"
    category: "negative"
    principal:
      type: "AI_AGENT"
      subject: "agent-assistant@local.test"
    request:
      capability: "workday.time.approve"
      parameters: {"request_id": "TOR-001"}
      environment: "prod"
    expected:
      allowed: false
  
  - id: "AI-104"
    name: "AI CANNOT list direct reports (manager-only)"
    category: "negative"
    principal:
      type: "AI_AGENT"
      subject: "agent-assistant@local.test"
    request:
      capability: "workday.hcm.list_direct_reports"
      parameters: {"manager_id": "EMP042"}
      environment: "prod"
    expected:
      allowed: false
  
  - id: "AI-105"
    name: "AI CANNOT request time off (even own behalf)"
    category: "negative"
    principal:
      type: "AI_AGENT"
      subject: "agent-assistant@local.test"
    request:
      capability: "workday.time.request"
      parameters:
        employee_id: "EMP001"
        type: "PTO"
        start_date: "2026-02-10"
        end_date: "2026-02-14"
      environment: "prod"
    expected:
      allowed: false
  
  - id: "AI-106"
    name: "AI CANNOT trigger onboarding flow"
    category: "negative"
    principal:
      type: "AI_AGENT"
      subject: "agent-assistant@local.test"
    request:
      capability: "hr.onboarding"
      parameters: {"employee_id": "EMP999"}
      environment: "prod"
    expected:
      allowed: false
  
  - id: "AI-107"
    name: "AI token TTL exceeds maximum (should deny)"
    category: "negative"
    principal:
      type: "AI_AGENT"
      subject: "agent-assistant@local.test"
      token_issued_at: 1706445600
      token_expires_at: 1706449200  # 1 hour (exceeds 5-min max)
    request:
      capability: "workday.hcm.get_employee"
      parameters: {"employee_id": "EMP001"}
      environment: "prod"
    expected:
      allowed: false
      reason_contains: "TTL"
```

**MFA Requirement Tests** (`tests/policy/scenarios/mfa_requirements.yaml`):
```yaml
version: "1.0"
metadata:
  name: "MFA Enforcement Tests"
  owner: "security-team"
  description: "Verify MFA required for sensitive capabilities"
  security_requirement: "SEC-005"

test_cases:
  # Positive: With MFA
  - id: "MFA-001"
    name: "Employee can access compensation WITH MFA"
    category: "positive"
    principal:
      type: "HUMAN"
      subject: "EMP001"
      groups: ["employees"]
      mfa_verified: true
    request:
      capability: "workday.payroll.get_compensation"
      parameters: {"employee_id": "EMP001"}
      environment: "prod"
    expected:
      allowed: true
  
  - id: "MFA-002"
    name: "Employee can access pay statement WITH MFA"
    category: "positive"
    principal:
      type: "HUMAN"
      subject: "EMP001"
      groups: ["employees"]
      mfa_verified: true
    request:
      capability: "workday.payroll.get_pay_statement"
      parameters: {"statement_id": "PAY-2026-01"}
      environment: "prod"
    expected:
      allowed: true
  
  # Negative: Without MFA
  - id: "MFA-101"
    name: "Employee CANNOT access compensation WITHOUT MFA"
    category: "negative"
    principal:
      type: "HUMAN"
      subject: "EMP001"
      groups: ["employees"]
      mfa_verified: false
    request:
      capability: "workday.payroll.get_compensation"
      parameters: {"employee_id": "EMP001"}
      environment: "prod"
    expected:
      allowed: false
      reason_contains: "MFA"
  
  - id: "MFA-102"
    name: "Employee CANNOT access pay statement WITHOUT MFA"
    category: "negative"
    principal:
      type: "HUMAN"
      subject: "EMP001"
      groups: ["employees"]
      mfa_verified: false
    request:
      capability: "workday.payroll.get_pay_statement"
      parameters: {"statement_id": "PAY-2026-01"}
      environment: "prod"
    expected:
      allowed: false
      reason_contains: "MFA"
  
  - id: "MFA-103"
    name: "Admin CANNOT access others' compensation WITHOUT MFA"
    category: "negative"
    principal:
      type: "HUMAN"
      subject: "admin@local.test"
      groups: ["hr-platform-admins"]
      mfa_verified: false
    request:
      capability: "workday.payroll.get_compensation"
      parameters: {"employee_id": "EMP001"}
      environment: "prod"
    expected:
      allowed: false
```

**Acceptance Criteria**:
- ✅ 107+ test scenarios defined
- ✅ All principal types covered (AI_AGENT, HUMAN, MACHINE)
- ✅ All capabilities covered (11 actions + 2 flows)
- ✅ Both positive and negative cases for each capability
- ✅ MFA, TTL, environment variations tested
- ✅ Edge cases included (token expiry, wildcards)

---

### FR-006: HTML Report Generation

**Specification**: Generate stakeholder-friendly HTML report.

**Implementation** (`src/domain/services/policy_report_generator.py`):
```python
from jinja2 import Template
from datetime import datetime
from src.domain.services.policy_verifier import VerificationReport

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Policy Verification Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        h1 { color: #333; border-bottom: 3px solid #4CAF50; padding-bottom: 10px; }
        .summary { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin: 30px 0; }
        .metric { background: #f9f9f9; padding: 20px; border-radius: 4px; text-align: center; border-left: 4px solid #4CAF50; }
        .metric.failed { border-left-color: #f44336; }
        .metric-value { font-size: 36px; font-weight: bold; color: #333; }
        .metric-label { color: #666; margin-top: 5px; }
        .pass-rate { font-size: 48px; font-weight: bold; color: {{ '#4CAF50' if report.success else '#f44336' }}; }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        th { background: #333; color: white; padding: 12px; text-align: left; }
        td { padding: 10px; border-bottom: 1px solid #ddd; }
        tr:hover { background: #f5f5f5; }
        .badge { padding: 4px 8px; border-radius: 3px; font-size: 12px; font-weight: bold; }
        .badge-pass { background: #4CAF50; color: white; }
        .badge-fail { background: #f44336; color: white; }
        .badge-positive { background: #2196F3; color: white; }
        .badge-negative { background: #FF9800; color: white; }
        .timestamp { color: #999; font-size: 14px; }
        .footer { margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; color: #666; text-align: center; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Policy Verification Report</h1>
        <div class="timestamp">Generated: {{ timestamp }}</div>
        
        <div class="summary">
            <div class="metric">
                <div class="metric-value">{{ report.total_tests }}</div>
                <div class="metric-label">Total Tests</div>
            </div>
            <div class="metric">
                <div class="metric-value">{{ report.passed }}</div>
                <div class="metric-label">Passed</div>
            </div>
            <div class="metric failed">
                <div class="metric-value">{{ report.failed }}</div>
                <div class="metric-label">Failed</div>
            </div>
            <div class="metric">
                <div class="pass-rate">{{ "%.1f"|format(report.pass_rate) }}%</div>
                <div class="metric-label">Pass Rate</div>
            </div>
        </div>
        
        {% if report.failed_tests %}
        <h2>❌ Failed Tests ({{ report.failed }})</h2>
        <table>
            <thead>
                <tr>
                    <th>Test ID</th>
                    <th>Test Name</th>
                    <th>Expected</th>
                    <th>Actual</th>
                    <th>Error</th>
                </tr>
            </thead>
            <tbody>
                {% for result in report.failed_tests %}
                <tr>
                    <td><code>{{ result.test_id }}</code></td>
                    <td>{{ result.test_name }}</td>
                    <td><span class="badge badge-{{ 'positive' if result.expected_allowed else 'negative' }}">
                        {{ 'ALLOW' if result.expected_allowed else 'DENY' }}
                    </span></td>
                    <td><span class="badge badge-{{ 'positive' if result.actual_allowed else 'negative' }}">
                        {{ 'ALLOW' if result.actual_allowed else 'DENY' }}
                    </span></td>
                    <td>{{ result.error_message }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        {% else %}
        <h2>✅ All Tests Passed!</h2>
        <p>All {{ report.passed }} test cases executed successfully.</p>
        {% endif %}
        
        <h2>Test Results Summary</h2>
        <table>
            <thead>
                <tr>
                    <th>Test ID</th>
                    <th>Test Name</th>
                    <th>Result</th>
                    <th>Policy Matched</th>
                    <th>Execution Time</th>
                </tr>
            </thead>
            <tbody>
                {% for result in report.results %}
                <tr>
                    <td><code>{{ result.test_id }}</code></td>
                    <td>{{ result.test_name }}</td>
                    <td><span class="badge badge-{{ 'pass' if result.passed else 'fail' }}">
                        {{ '✓ PASS' if result.passed else '✗ FAIL' }}
                    </span></td>
                    <td>{{ result.actual_policy or '-' }}</td>
                    <td>{{ "%.1f"|format(result.execution_time_ms) }}ms</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        
        <div class="footer">
            <p>Policy Verification Framework v1.0 | HR AI Platform</p>
            <p>Execution Time: {{ "%.0f"|format(report.execution_time_ms) }}ms</p>
        </div>
    </div>
</body>
</html>
"""

def generate_html_report(report: VerificationReport, output_path: str):
    """Generate HTML report from verification results."""
    template = Template(HTML_TEMPLATE)
    
    html = template.render(
        report=report,
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
    
    with open(output_path, "w") as f:
        f.write(html)
```

**Usage**:
```python
verifier = PolicyVerificationService("config/policy-workday.yaml")
report = verifier.run_all_tests("tests/policy/scenarios/")

from src.domain.services.policy_report_generator import generate_html_report
generate_html_report(report, "tests/policy/reports/latest.html")
```

**Acceptance Criteria**:
- ✅ HTML report generated with summary metrics
- ✅ Failed tests highlighted
- ✅ Execution time tracked
- ✅ Stakeholder-friendly formatting
- ✅ Report timestamped

---

## Testing Strategy

### Unit Tests (`tests/unit/domain/test_policy_verifier.py`)

```python
class TestPolicyVerifier:
    def test_load_test_suite(self):
        """Test suite loads from YAML."""
        verifier = PolicyVerificationService("config/policy-workday.yaml")
        suite = verifier.load_test_suite("tests/policy/scenarios/ai_agents.yaml")
        assert len(suite.test_cases) > 0
    
    def test_positive_case_passes(self):
        """Positive test case passes when policy allows."""
        # Create minimal test case
        test = PolicyTestCase(
            id="TEST-001",
            name="Test",
            category="positive",
            principal=TestPrincipal(type="HUMAN", subject="EMP001", groups=["employees"]),
            request=TestRequest(capability="workday.hcm.get_employee", environment="prod"),
            expected=ExpectedResult(allowed=True)
        )
        
        verifier = PolicyVerificationService("config/policy-workday.yaml")
        result = verifier.run_test_case(test)
        
        assert result.passed is True
    
    def test_negative_case_passes(self):
        """Negative test case passes when policy denies."""
        test = PolicyTestCase(
            id="TEST-002",
            name="Test",
            category="negative",
            principal=TestPrincipal(type="AI_AGENT", subject="agent"),
            request=TestRequest(capability="workday.payroll.get_compensation", environment="prod"),
            expected=ExpectedResult(allowed=False)
        )
        
        verifier = PolicyVerificationService("config/policy-workday.yaml")
        result = verifier.run_test_case(test)
        
        assert result.passed is True
    
    def test_failed_positive_case(self):
        """Positive test fails when policy unexpectedly denies."""
        test = PolicyTestCase(
            id="TEST-003",
            name="Test",
            category="positive",
            principal=TestPrincipal(type="HUMAN", subject="nobody", groups=[]),
            request=TestRequest(capability="workday.hcm.get_employee", environment="prod"),
            expected=ExpectedResult(allowed=True)
        )
        
        verifier = PolicyVerificationService("config/policy-workday.yaml")
        result = verifier.run_test_case(test)
        
        assert result.passed is False
        assert "DENY" in result.error_message
```

---

### Integration Tests (`tests/integration/test_policy_verification_e2e.py`)

```python
class TestPolicyVerificationE2E:
    def test_all_scenarios_pass(self):
        """All test scenarios pass against current policy."""
        verifier = PolicyVerificationService("config/policy-workday.yaml")
        report = verifier.run_all_tests("tests/policy/scenarios/")
        
        if not report.success:
            for result in report.failed_tests:
                print(f"FAILED: {result.test_name} - {result.error_message}")
        
        assert report.success, f"{report.failed} tests failed"
    
    def test_html_report_generated(self):
        """HTML report generation works."""
        verifier = PolicyVerificationService("config/policy-workday.yaml")
        report = verifier.run_all_tests("tests/policy/scenarios/")
        
        from src.domain.services.policy_report_generator import generate_html_report
        output = "tests/policy/reports/test-report.html"
        generate_html_report(report, output)
        
        assert Path(output).exists()
```

---

## Migration Plan

### Phase 1: Framework Implementation (Week 1, Day 1-2)
- Create Pydantic schema for test scenarios
- Implement PolicyVerificationService
- Write unit tests for verifier
- **Deliverable**: Working test runner

---

### Phase 2: Test Scenario Creation (Week 1, Day 3-5)
- Write AI agent test scenarios (15 cases)
- Write employee test scenarios (20 cases)
- Write manager test scenarios (18 cases)
- Write admin test scenarios (17 cases)
- Write MFA/edge case scenarios (37 cases)
- **Deliverable**: 107 test scenarios

---

### Phase 3: CLI & Reporting (Week 2, Day 1-2)
- Implement CLI tool
- Add HTML report generation
- Test report formats (table, JSON, JUnit)
- **Deliverable**: Complete CLI tooling

---

### Phase 4: CI/CD Integration (Week 2, Day 3)
- Add GitHub Actions workflow
- Configure pre-commit hook
- Test PR blocking on failures
- **Deliverable**: Automated CI validation

---

### Phase 5: Documentation & Training (Week 2, Day 4-5)
- Write developer guide for adding tests
- Document security requirements mapping
- Train team on verification workflow
- **Deliverable**: Team ready to use framework

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Test Coverage** | 100% of capabilities | All 13 capabilities have ≥2 test cases |
| **False Positive Rate** | <5% | Tests that fail incorrectly |
| **Execution Time** | <10 seconds | Time to run all 107 tests |
| **CI Integration** | 100% | All PRs touching policy validated |
| **Documentation** | 100% | Every security requirement has tests |

---

## Acceptance Criteria

**Must Have** (Blocking for Demo):
- ✅ 107+ test scenarios covering all capabilities
- ✅ CLI tool runs tests and generates reports
- ✅ CI/CD integration blocks bad policies
- ✅ HTML report generated for stakeholders
- ✅ Pre-commit hook validates locally

**Should Have** (Post-Demo):
- ✅ JUnit XML integration for test dashboards
- ✅ Coverage report showing % of policies tested
- ✅ Scenario templates for common patterns

**Nice to Have** (Future):
- ⏳ Auto-generate scenarios from policy changes
- ⏳ Mutation testing (modify policy, ensure tests fail)
- ⏳ Integration with Backstage governance dashboard

---

## Risks & Mitigation

### Risk 1: Test Scenarios Out of Sync with Policy

**Scenario**: Policy changes but tests not updated.

**Mitigation**:
1. PR template requires updating tests for policy changes
2. CI enforces test coverage metrics
3. Quarterly policy review includes test review

### Risk 2: False Negatives (Tests Pass But Policy Wrong)

**Scenario**: Test expects DENY but security requirement needs ALLOW.

**Mitigation**:
1. Security team reviews all test scenarios
2. Map tests to security requirements (SEC-xxx)
3. Annual security audit validates tests

### Risk 3: Test Execution Performance

**Scenario**: 107 tests slow down CI.

**Mitigation**:
1. Current: 107 tests × ~10ms each = ~1 second (acceptable)
2. If needed: Parallelize test execution
3. Cache policy engine instance

---

## Future Enhancements

### Phase 2: Coverage Analysis
```bash
./scripts/verify-policy coverage --show-untested

Output:
  Capabilities with <2 test cases:
    - workday.hcm.update_contact_info (1 test)
  
  Policies with no verification:
    - machine-workflow-permissions
```

### Phase 3: Mutation Testing
Modify policy, ensure tests fail:
```yaml
# Original policy
capabilities: ["workday.hcm.get_employee"]

# Mutated (should fail tests)
capabilities: ["workday.hcm.*"]  # Too broad
```

---

**End of PRD**
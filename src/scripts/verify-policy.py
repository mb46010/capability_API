#!/usr/bin/env python3
import sys
import argparse
import json
from pathlib import Path
from tabulate import tabulate

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.domain.services.policy_verifier import PolicyVerificationService
from src.adapters.filesystem.policy_loader import FilePolicyLoaderAdapter
from src.adapters.filesystem.scenario_loader import FileScenarioLoaderAdapter

def cmd_run(args):
    policy_loader = FilePolicyLoaderAdapter(args.policy)
    scenario_loader = FileScenarioLoaderAdapter()
    verifier = PolicyVerificationService(policy_loader, scenario_loader)
    report = verifier.run_all_tests(args.scenarios)

    
    # Print summary (only for table format)
    if args.format == "table":
        print("=" * 60)
        print("Policy Verification Report")
        print("=" * 60)
        print(f"Total Tests: {report.total_tests}")
        print(f"Passed:      {report.passed} ✅")
        print(f"Failed:      {report.failed} ❌")
        print(f"Skipped:     {report.skipped} ⏭️")
        print(f"Pass Rate:   {report.pass_rate:.1f}%")
        print(f"Execution:   {report.execution_time_ms:.0f}ms")
        print("=" * 60)
    
    if args.format == "table":
        if report.results:
            headers = ["ID", "Test Name", "Expected", "Actual", "Result", "Policy", "Audit"]
            rows = []
            for r in report.results:
                rows.append([
                    r.test_id,
                    r.test_name[:30],
                    "ALLOW" if r.expected_allowed else "DENY",
                    "ALLOW" if r.actual_allowed else "DENY",
                    "PASS" if r.passed else "FAIL",
                    r.actual_policy or "-",
                    r.actual_audit or "-"
                ])
            print(tabulate(rows, headers=headers, tablefmt="grid"))
            
        if report.failed_tests:
            print("\n❌ Errors:")
            for r in report.failed_tests:
                print(f"  [{r.test_id}] {r.test_name}: {r.error_message}")
                
    elif args.format == "json":
        output = {
            "summary": {
                "total": report.total_tests,
                "passed": report.passed,
                "failed": report.failed,
                "skipped": report.skipped,
                "pass_rate": report.pass_rate,
            },
            "results": [
                {
                    "id": r.test_id,
                    "name": r.test_name,
                    "passed": r.passed,
                    "error": r.error_message,
                }
                for r in report.results
            ]
        }
        print(json.dumps(output, indent=2))
        
    elif args.format == "html":
        from src.domain.services.policy_report_generator import PolicyReportGenerator
        generator = PolicyReportGenerator()
        html = generator.generate_html(report)
        print(html)
        
    sys.exit(0 if report.success else 1)

def cmd_list_scenarios(args):
    policy_loader = FilePolicyLoaderAdapter(args.policy)
    scenario_loader = FileScenarioLoaderAdapter()
    verifier = PolicyVerificationService(policy_loader, scenario_loader)
    suites = verifier.scenario_loader.load_all_test_suites(args.scenarios)

    
    print("Available Test Scenarios:")
    for suite in suites:
        print(f"  - {suite.metadata.name} ({len(suite.test_cases)} tests)")
        print(f"    {suite.metadata.description}")

def main():
    parser = argparse.ArgumentParser(description="Policy Verification CLI")
    
    # Common arguments
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
    
    subparsers = parser.add_subparsers(dest="command")
    
    # Run command
    run_parser = subparsers.add_parser("run")
    # Inherit or redefine arguments for the sub-parser
    run_parser.add_argument(
        "--policy",
        help="Path to policy YAML"
    )
    run_parser.add_argument(
        "--scenarios",
        help="Path to test scenarios directory"
    )
    run_parser.add_argument(
        "--format",
        choices=["table", "json", "junit", "html"],
        default="table"
    )
    
    # List command
    list_parser = subparsers.add_parser("list-scenarios")
    list_parser.add_argument(
        "--policy",
        help="Path to policy YAML"
    )
    list_parser.add_argument(
        "--scenarios",
        help="Path to test scenarios directory"
    )
    
    args = parser.parse_args()
    
    # Simple merging of sub-command args into global args
    if hasattr(args, 'command') and args.command:
        # Fallback to global defaults if sub-command args are None
        if not args.policy:
            args.policy = parser.get_default('policy')
        if not args.scenarios:
            args.scenarios = parser.get_default('scenarios')

    if args.command == "run":
        cmd_run(args)
    elif args.command == "list-scenarios":
        cmd_list_scenarios(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
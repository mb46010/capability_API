# Policy Verification Report

**Timestamp**: 2026-02-02 21:32:34
**Policy Version**: `unknown`
**Status**: 🟢 PASS
## Summary

| Metric | Value |
|--------|-------|
| Total Tests | 10 |
| Passed | 10 |
| Failed | 0 |
| Pass Rate | 100.0% |


## Full Results

| ID | Scenario | Outcome | Policy | Duration |
|----|----------|---------|--------|----------|
| ADM-001 | Admin full access with MFA | ✅ | admin-full-access | 0.05ms |
| ADM-002 | Admin denied WITHOUT MFA | ✅ | None | 0.05ms |
| EMP-001 | Employee can read directory | ✅ | employee-self-service-read | 0.03ms |
| EMP-002 | Employee can manage own time off | ✅ | employee-time-self-service | 0.02ms |
| EMP-003 | Employee CANNOT update info WITHOUT MFA | ✅ | None | 0.04ms |
| AI-001 | AI Assistant can read directory | ✅ | ai-assistant-directory | 0.02ms |
| AI-002 | AI Assistant denied if TTL too long | ✅ | None | 0.04ms |
| REG-001 | Admin matches wildcard workday.* | ✅ | admin-full-access | 0.03ms |
| REG-002 | Admin matches wildcard hr.* | ✅ | admin-full-access | 0.02ms |
| REG-003 | Staff matches group-based policy | ✅ | hr-staff-time-management | 0.02ms |

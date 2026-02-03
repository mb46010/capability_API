# BUG-009: Time Off Balance Double Deduction on Approval

## Severity
🟡 MEDIUM

## Location
- **File(s)**: `src/adapters/workday/services/time.py`
- **Line(s)**: 259-265

## Issue Description
When a time off request is approved, the balance calculation appears to deduct hours twice:

```python
# ❌ LOGIC ERROR - Double deduction
if balance_entry:
    balance_entry.pending_hours = max(0, balance_entry.pending_hours - request.hours)
    balance_entry.available_hours = max(0, balance_entry.available_hours - request.hours)  # Deduct from available
    balance_entry.used_hours += request.hours  # Also track as used
```

The issue is that `available_hours` should represent total available balance. When we:
1. Submit a request: `pending_hours += hours` (reserves the time)
2. Approve: `pending_hours -= hours` (removes reservation) AND `available_hours -= hours` (deducts)

But if `available_hours` already excluded `pending_hours` in the balance calculation shown to users, this results in:
- User sees: `available = 80 - 8 pending = 72 hours`
- After approval: `available = 72 - 8 = 64 hours` (incorrect - should be 72)

The correct behavior depends on how `available_hours` is defined, but the current logic is inconsistent with typical PTO systems.

## Impact
- **Incorrect balances**: Employees see wrong PTO balances after approval
- **Over-restriction**: Employees may be prevented from taking legitimate time off
- **Accounting errors**: HR reports may show incorrect accrual data

## Root Cause
The relationship between `available_hours`, `pending_hours`, and `used_hours` is not clearly defined or consistently implemented. Standard semantics are:
- `accrued_hours`: Total hours earned
- `used_hours`: Hours already taken
- `pending_hours`: Hours in pending requests
- `available_hours`: Should equal `accrued_hours - used_hours - pending_hours`

## How to Fix

### Code Changes
Fix the approval logic to correctly update balances:

```python
# ✅ FIXED - Correct balance updates
if balance_entry:
    # Remove from pending (was reserved when submitted)
    balance_entry.pending_hours = max(0, balance_entry.pending_hours - request.hours)

    # Move to used (actually consumed)
    balance_entry.used_hours += request.hours

    # DO NOT deduct from available_hours here if it's already
    # calculated as (accrued - used - pending)

    # OR if available_hours is a raw "remaining" value:
    # balance_entry.available_hours should already have been
    # reduced when request was submitted, not again here
```

### Steps
1. Define clear semantics for balance fields in `time_models.py`
2. Review `request()` function for how `available_hours` is updated on submission
3. Update `approve()` to be consistent with the defined semantics
4. Add unit tests verifying balance consistency through request lifecycle

## Verification

### Test Cases
1. Start with 80 hours available
2. Submit 8-hour request - `available` should reflect pending
3. Approve request - `available` should be 72, not 64
4. Cancel approved request - `available` should return to 80

### Verification Steps
1. Add integration test for full request lifecycle
2. Verify balances at each step
3. Test edge cases (partial hours, multiple requests)

## Related Issues
- Related to balance display logic in `get_balance`

---
*Discovered: 2026-02-03*

from typing import Optional, Dict, Any

class WorkdayError(Exception):
    """Base error for all Workday simulator operations."""
    def __init__(self, message: str, error_code: str, details: Optional[Dict[str, Any]] = None, retry_allowed: bool = False):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.retry_allowed = retry_allowed

class EmployeeNotFoundError(WorkdayError):
    def __init__(self, employee_id: str):
        super().__init__(
            message=f"Employee with ID '{employee_id}' not found",
            error_code="EMPLOYEE_NOT_FOUND",
            details={"employee_id": employee_id}
        )

class RequestNotFoundError(WorkdayError):
    def __init__(self, request_id: str):
        super().__init__(
            message=f"Time off request not found",
            error_code="REQUEST_NOT_FOUND",
            details={"request_id": request_id}
        )

class StatementNotFoundError(WorkdayError):
    def __init__(self, statement_id: str):
        super().__init__(
            message=f"Pay statement not found",
            error_code="STATEMENT_NOT_FOUND",
            details={"statement_id": statement_id}
        )

class InsufficientBalanceError(WorkdayError):
    def __init__(self, available: float, requested: float):
        super().__init__(
            message="Not enough time off balance",
            error_code="INSUFFICIENT_BALANCE",
            details={"available_hours": available, "requested_hours": requested}
        )

class InvalidDateRangeError(WorkdayError):
    def __init__(self):
        super().__init__(
            message="Start date after end date",
            error_code="INVALID_DATE_RANGE"
        )

class InvalidApproverError(WorkdayError):
    def __init__(self, approver_id: str):
        super().__init__(
            message="Approver not in manager chain",
            error_code="INVALID_APPROVER",
            details={"approver_id": approver_id}
        )

class AlreadyProcessedError(WorkdayError):
    def __init__(self):
        super().__init__(
            message="Request already approved/cancelled",
            error_code="ALREADY_PROCESSED"
        )

class ConnectorTimeoutError(WorkdayError):
    def __init__(self):
        super().__init__(
            message="Workday API timeout",
            error_code="CONNECTOR_TIMEOUT",
            retry_allowed=True
        )

class ConnectorUnavailableError(WorkdayError):
    def __init__(self):
        super().__init__(
            message="Workday API down",
            error_code="CONNECTOR_UNAVAILABLE",
            retry_allowed=True
        )

class RateLimitedError(WorkdayError):
    def __init__(self):
        super().__init__(
            message="Too many requests",
            error_code="RATE_LIMITED",
            retry_allowed=True
        )

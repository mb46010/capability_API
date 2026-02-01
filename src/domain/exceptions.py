class ConnectorError(Exception):
    """Raised when an external system operation fails."""
    def __init__(self, message: str, error_code: str = "CONNECTOR_ERROR", details: dict = None, retry_allowed: bool = False):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details
        self.retry_allowed = retry_allowed

"""
ClickUp Framework Exceptions

Custom exception classes for ClickUp API errors.
"""


class ClickUpError(Exception):
    """Base exception for all ClickUp framework errors."""

    pass


class ClickUpAPIError(ClickUpError):
    """Raised when ClickUp API returns an error response."""

    def __init__(self, status_code: int, message: str, response: dict = None):
        self.status_code = status_code
        self.message = message
        self.response = response
        super().__init__(f"ClickUp API Error {status_code}: {message}")


class ClickUpAuthError(ClickUpAPIError):
    """Raised when authentication fails (401)."""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(401, message)


class ClickUpRateLimitError(ClickUpAPIError):
    """Raised when rate limit is exceeded (429)."""

    def __init__(self, retry_after: int = None):
        self.retry_after = retry_after
        message = "Rate limit exceeded"
        if retry_after:
            message += f" (retry after {retry_after}s)"
        super().__init__(429, message)


class ClickUpNotFoundError(ClickUpAPIError):
    """Raised when resource is not found (404)."""

    def __init__(self, resource: str, resource_id: str = None):
        message = f"{resource} not found"
        if resource_id:
            message += f": {resource_id}"
        super().__init__(404, message)


class ClickUpValidationError(ClickUpError):
    """Raised when input validation fails."""

    pass


class ClickUpTimeoutError(ClickUpError):
    """Raised when request times out."""

    pass

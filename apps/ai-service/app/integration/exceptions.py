# app/integration/exceptions.py


class IntegrationException(Exception):
    """Base exception for all integration errors."""

    def __init__(self, message: str, error_code: str):
        super().__init__(message)
        self.message = message
        self.error_code = error_code


class ProviderAuthError(IntegrationException):
    """Raised when authentication with the provider fails."""

    def __init__(self, message: str):
        super().__init__(message, "RY_INTEG_AUTH_001")


class ProviderRateLimitError(IntegrationException):
    """Raised when the provider rate limits are exceeded."""

    def __init__(self, message: str):
        super().__init__(message, "RY_INTEG_RATE_002")


class ProviderTimeoutError(IntegrationException):
    """Raised when provider call times out."""

    def __init__(self, message: str):
        super().__init__(message, "RY_INTEG_TIMEOUT_003")


class ProviderNetworkError(IntegrationException):
    """Raised on network connection errors."""

    def __init__(self, message: str):
        super().__init__(message, "RY_INTEG_NET_004")


class ProviderValidationError(IntegrationException):
    """Raised on invalid request/response schema data."""

    def __init__(self, message: str):
        super().__init__(message, "RY_INTEG_VAL_005")


class ProviderBusinessError(IntegrationException):
    """Raised on downstream provider-level business logic failures."""

    def __init__(self, message: str):
        super().__init__(message, "RY_INTEG_BUS_006")

class LLMException(Exception):
    """Base exception class for all LLM Infrastructure Layer errors."""
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message

class ProviderNotFound(LLMException):
    """Raised when a requested provider is not registered or found in the system."""
    pass

class InvalidConfiguration(LLMException):
    """Raised when a provider is misconfigured or lacks mandatory parameters."""
    pass

class AuthenticationError(InvalidConfiguration):
    """Raised when API keys or authentication credentials fail validation."""
    pass

class UnsupportedCapability(LLMException):
    """Raised when a model is requested to perform a task it does not support (e.g. vision or tools)."""
    pass

class ModelUnavailable(LLMException):
    """Raised when a resolved model is deprecated, missing, or disabled."""
    pass

class RateLimitExceeded(LLMException):
    """Raised when provider API rate limits (RPM/TPM) are hit."""
    pass

class ProviderTimeout(LLMException):
    """Raised when a request to a provider service times out."""
    pass

class ProviderUnavailable(LLMException):
    """Raised when the remote provider service is down or completely unreachable."""
    pass

class ProviderQuotaExceeded(LLMException):
    """Raised when billing limits or usage quotas are exceeded for the provider API."""
    pass

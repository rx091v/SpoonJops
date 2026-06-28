class JobAgentError(Exception):
    """Base exception for domain-level failures."""


class ExternalServiceError(JobAgentError):
    """Raised when an external source or API fails."""


class AutomationPausedError(JobAgentError):
    """Raised when browser automation requires manual intervention."""

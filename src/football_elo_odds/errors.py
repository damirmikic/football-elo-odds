"""Typed application error hierarchy for revamp architecture."""


class AppError(Exception):
    """Base error for expected application failures."""


class ExternalServiceError(AppError):
    """Raised when an external dependency is unavailable or returns invalid data."""


class DataValidationError(AppError):
    """Raised when user or provider payloads fail validation rules."""


class NotFoundError(AppError):
    """Raised when requested entities cannot be found."""


class ConfigurationError(AppError):
    """Raised when required runtime configuration is missing or invalid."""

"""Map internal AppError types to user-safe UI payloads."""

from dataclasses import dataclass

from football_elo_odds.errors import (
    AppError,
    ConfigurationError,
    DataValidationError,
    ExternalServiceError,
    NotFoundError,
)


@dataclass(frozen=True)
class UIErrorMessage:
    level: str
    title: str
    detail: str


def map_error_to_ui(error: Exception) -> UIErrorMessage:
    if isinstance(error, ExternalServiceError):
        return UIErrorMessage(
            level="warning",
            title="External data source unavailable",
            detail="Some providers failed to respond. Try again or continue with limited data.",
        )
    if isinstance(error, DataValidationError):
        return UIErrorMessage(
            level="error",
            title="Invalid input data",
            detail=str(error),
        )
    if isinstance(error, NotFoundError):
        return UIErrorMessage(
            level="info",
            title="Data not found",
            detail=str(error),
        )
    if isinstance(error, ConfigurationError):
        return UIErrorMessage(
            level="error",
            title="Configuration issue",
            detail="Application configuration is invalid. Contact support.",
        )
    if isinstance(error, AppError):
        return UIErrorMessage(level="error", title="Application error", detail=str(error))
    return UIErrorMessage(
        level="error",
        title="Unexpected error",
        detail="An unexpected issue occurred. Please retry.",
    )

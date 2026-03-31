"""Semantic exceptions with exit codes for the Attio CLI."""
import click


class AttioError(click.ClickException):
    """Base Attio exception. Subclasses set specific exit codes."""

    def __init__(
        self,
        message: str,
        exit_code: int = 1,
        hint: str | None = None,
    ) -> None:
        super().__init__(message)
        self.exit_code = exit_code
        self.hint = hint

    def show(self) -> None:
        """Write error (and optional hint) to stderr only."""
        click.echo(f"Error: {self.format_message()}", err=True)
        if self.hint:
            click.echo(f"Hint: {self.hint}", err=True)


class AuthError(AttioError):
    """Exit code 4 — authentication failure."""

    def __init__(
        self,
        message: str = "Authentication failed.",
        hint: str | None = "Run: attio config set api-key <your-key>  or set ATTIO_API_KEY env var",
    ) -> None:
        super().__init__(message, exit_code=4, hint=hint)


class NotFoundError(AttioError):
    """Exit code 3 — resource not found."""

    def __init__(self, resource: str) -> None:
        super().__init__(
            f"Not found: {resource}",
            exit_code=3,
            hint="Use the list command to find valid IDs",
        )


class RateLimitError(AttioError):
    """Exit code 5 — rate limited (handled internally, surfaced if retries exhausted)."""

    def __init__(self, retry_after: float = 1.0) -> None:
        super().__init__(
            f"Rate limited. Retry after {retry_after:.1f}s",
            exit_code=5,
            hint="Attio uses score-based rate limits. Reduce request frequency.",
        )
        self.retry_after = retry_after


class TransientError(AttioError):
    """Exit code 1 — transient server error (500/502/503/504)."""

    def __init__(self, status_code: int) -> None:
        super().__init__(
            f"Server error {status_code}. Request was retried and failed.",
            exit_code=1,
        )
        self.status_code = status_code

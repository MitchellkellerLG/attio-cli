"""Tests for the semantic exception hierarchy."""
import io
from unittest.mock import patch

import pytest
import click
from click.testing import CliRunner


class TestAttioError:
    """Base AttioError behavior."""

    def test_attio_error_default_exit_code(self):
        """AttioError default exit_code is 1."""
        from cli_anything.attio.utils.exceptions import AttioError

        err = AttioError("Something went wrong")
        assert err.exit_code == 1

    def test_attio_error_custom_exit_code(self):
        """AttioError accepts custom exit_code."""
        from cli_anything.attio.utils.exceptions import AttioError

        err = AttioError("msg", exit_code=3)
        assert err.exit_code == 3

    def test_attio_error_hint_default_none(self):
        """AttioError hint defaults to None."""
        from cli_anything.attio.utils.exceptions import AttioError

        err = AttioError("msg")
        assert err.hint is None

    def test_attio_error_with_hint(self):
        """AttioError stores hint."""
        from cli_anything.attio.utils.exceptions import AttioError

        err = AttioError("msg", hint="Run: attio config set api-key")
        assert err.hint == "Run: attio config set api-key"

    def test_attio_error_show_writes_to_stderr(self, capsys):
        """show() writes to stderr, not stdout."""
        from cli_anything.attio.utils.exceptions import AttioError

        err = AttioError("Test error message")
        err.show()
        captured = capsys.readouterr()
        assert "Test error message" in captured.err
        assert "Test error message" not in captured.out

    def test_attio_error_show_hint_to_stderr(self, capsys):
        """show() also writes hint to stderr."""
        from cli_anything.attio.utils.exceptions import AttioError

        err = AttioError("msg", hint="Try this fix")
        err.show()
        captured = capsys.readouterr()
        assert "Try this fix" in captured.err

    def test_attio_error_no_hint_no_extra_output(self, capsys):
        """show() with no hint doesn't output extra blank lines."""
        from cli_anything.attio.utils.exceptions import AttioError

        err = AttioError("msg")
        err.show()
        captured = capsys.readouterr()
        assert "Hint" not in captured.err

    def test_attio_error_is_click_exception(self):
        """AttioError inherits from click.ClickException."""
        from cli_anything.attio.utils.exceptions import AttioError

        err = AttioError("msg")
        assert isinstance(err, click.ClickException)


class TestAuthError:
    """AuthError — exit code 4, auth failure."""

    def test_auth_error_exit_code(self):
        """AuthError has exit_code=4."""
        from cli_anything.attio.utils.exceptions import AuthError

        err = AuthError()
        assert err.exit_code == 4

    def test_auth_error_default_message(self):
        """AuthError has a default message."""
        from cli_anything.attio.utils.exceptions import AuthError

        err = AuthError()
        assert "Authentication" in err.format_message() or len(err.format_message()) > 0

    def test_auth_error_custom_message(self):
        """AuthError accepts custom message."""
        from cli_anything.attio.utils.exceptions import AuthError

        err = AuthError("Custom auth message")
        assert "Custom auth message" in err.format_message()

    def test_auth_error_default_hint_mentions_config_command(self):
        """AuthError default hint includes 'attio config set api-key'."""
        from cli_anything.attio.utils.exceptions import AuthError

        err = AuthError()
        assert err.hint is not None
        assert "attio config set api-key" in err.hint

    def test_auth_error_custom_hint(self):
        """AuthError accepts custom hint."""
        from cli_anything.attio.utils.exceptions import AuthError

        err = AuthError("msg", hint="custom hint")
        assert err.hint == "custom hint"

    def test_auth_error_no_bearer_token_in_message(self):
        """AuthError message never contains 'Authorization' or bearer token."""
        from cli_anything.attio.utils.exceptions import AuthError

        err = AuthError()
        assert "Authorization" not in err.format_message()
        assert "Bearer" not in err.format_message()

    def test_auth_error_no_bearer_token_in_repr(self):
        """AuthError repr never contains bearer token."""
        from cli_anything.attio.utils.exceptions import AuthError

        err = AuthError()
        assert "Authorization" not in repr(err)
        assert "Bearer" not in repr(err)


class TestNotFoundError:
    """NotFoundError — exit code 3, resource not found."""

    def test_not_found_exit_code(self):
        """NotFoundError has exit_code=3."""
        from cli_anything.attio.utils.exceptions import NotFoundError

        err = NotFoundError("people/rec_abc")
        assert err.exit_code == 3

    def test_not_found_message_contains_resource(self):
        """NotFoundError message includes the resource identifier."""
        from cli_anything.attio.utils.exceptions import NotFoundError

        err = NotFoundError("people/rec_abc")
        assert "people/rec_abc" in err.format_message()

    def test_not_found_message_format(self):
        """NotFoundError message contains 'Not found'."""
        from cli_anything.attio.utils.exceptions import NotFoundError

        err = NotFoundError("companies/rec_xyz")
        assert "Not found" in err.format_message()


class TestRateLimitError:
    """RateLimitError — exit code 5, rate limited."""

    def test_rate_limit_exit_code(self):
        """RateLimitError has exit_code=5."""
        from cli_anything.attio.utils.exceptions import RateLimitError

        err = RateLimitError(2.5)
        assert err.exit_code == 5

    def test_rate_limit_message_contains_retry_after(self):
        """RateLimitError message contains the retry_after value."""
        from cli_anything.attio.utils.exceptions import RateLimitError

        err = RateLimitError(2.5)
        assert "2.5" in err.format_message()

    def test_rate_limit_stores_retry_after(self):
        """RateLimitError stores retry_after attribute."""
        from cli_anything.attio.utils.exceptions import RateLimitError

        err = RateLimitError(3.7)
        assert err.retry_after == 3.7

    def test_rate_limit_default_retry_after(self):
        """RateLimitError default retry_after is 1.0."""
        from cli_anything.attio.utils.exceptions import RateLimitError

        err = RateLimitError()
        assert err.retry_after == 1.0


class TestTransientError:
    """TransientError — exit code 1, server error."""

    def test_transient_error_exit_code(self):
        """TransientError has exit_code=1."""
        from cli_anything.attio.utils.exceptions import TransientError

        err = TransientError(503)
        assert err.exit_code == 1

    def test_transient_error_message_contains_status_code(self):
        """TransientError message contains the HTTP status code."""
        from cli_anything.attio.utils.exceptions import TransientError

        err = TransientError(503)
        assert "503" in err.format_message()

    def test_transient_error_stores_status_code(self):
        """TransientError stores status_code attribute."""
        from cli_anything.attio.utils.exceptions import TransientError

        err = TransientError(503)
        assert err.status_code == 503

    def test_transient_error_500(self):
        """TransientError works with 500."""
        from cli_anything.attio.utils.exceptions import TransientError

        err = TransientError(500)
        assert err.exit_code == 1
        assert "500" in err.format_message()


class TestExceptionHierarchy:
    """Test the inheritance structure."""

    def test_auth_error_is_attio_error(self):
        """AuthError inherits from AttioError."""
        from cli_anything.attio.utils.exceptions import AttioError, AuthError

        assert issubclass(AuthError, AttioError)

    def test_not_found_error_is_attio_error(self):
        """NotFoundError inherits from AttioError."""
        from cli_anything.attio.utils.exceptions import AttioError, NotFoundError

        assert issubclass(NotFoundError, AttioError)

    def test_rate_limit_error_is_attio_error(self):
        """RateLimitError inherits from AttioError."""
        from cli_anything.attio.utils.exceptions import AttioError, RateLimitError

        assert issubclass(RateLimitError, AttioError)

    def test_transient_error_is_attio_error(self):
        """TransientError inherits from AttioError."""
        from cli_anything.attio.utils.exceptions import AttioError, TransientError

        assert issubclass(TransientError, AttioError)

    def test_all_are_click_exceptions(self):
        """All exceptions are caught by Click's runner."""
        from cli_anything.attio.utils.exceptions import (
            AttioError,
            AuthError,
            NotFoundError,
            RateLimitError,
            TransientError,
        )

        for cls in (AttioError, AuthError, NotFoundError, RateLimitError, TransientError):
            assert issubclass(cls, click.ClickException), f"{cls.__name__} not ClickException"

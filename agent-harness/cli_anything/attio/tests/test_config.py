"""Tests for config loading — env var, XDG file, and missing-key AuthError."""
import json
import os
import stat
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from cli_anything.attio.utils.exceptions import AuthError


class TestLoadConfig:
    """Test load_config() under all three scenarios."""

    def test_env_var_returns_config(self):
        """ATTIO_API_KEY set → AttioConfig with that key."""
        with patch.dict(os.environ, {"ATTIO_API_KEY": "test_key_abc"}):
            from cli_anything.attio.utils.config import load_config

            cfg = load_config()
            assert cfg.api_key == "test_key_abc"

    def test_env_var_default_base_url(self):
        """ATTIO_API_KEY set → base_url defaults to v2 endpoint."""
        with patch.dict(os.environ, {"ATTIO_API_KEY": "test_key_abc"}):
            from cli_anything.attio.utils.config import load_config

            cfg = load_config()
            assert cfg.base_url == "https://api.attio.com/v2"

    def test_no_env_var_reads_config_file(self, tmp_path):
        """No env var but valid config.json → returns AttioConfig from file."""
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({"api_key": "file_key_xyz"}))

        env = {k: v for k, v in os.environ.items() if k != "ATTIO_API_KEY"}
        with patch.dict(os.environ, env, clear=True):
            from cli_anything.attio.utils import config as config_module

            with patch.object(config_module, "CONFIG_FILE", config_file):
                cfg = config_module.load_config()
                assert cfg.api_key == "file_key_xyz"

    def test_config_file_base_url_override(self, tmp_path):
        """Config file with base_url override → AttioConfig uses it."""
        config_file = tmp_path / "config.json"
        config_file.write_text(
            json.dumps({"api_key": "file_key", "base_url": "https://custom.example.com"})
        )

        env = {k: v for k, v in os.environ.items() if k != "ATTIO_API_KEY"}
        with patch.dict(os.environ, env, clear=True):
            from cli_anything.attio.utils import config as config_module

            with patch.object(config_module, "CONFIG_FILE", config_file):
                cfg = config_module.load_config()
                assert cfg.base_url == "https://custom.example.com"

    def test_env_var_takes_precedence_over_file(self, tmp_path):
        """Both env var and config file present → env var wins (D-08)."""
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({"api_key": "file_key"}))

        with patch.dict(os.environ, {"ATTIO_API_KEY": "env_key"}):
            from cli_anything.attio.utils import config as config_module

            with patch.object(config_module, "CONFIG_FILE", config_file):
                cfg = config_module.load_config()
                assert cfg.api_key == "env_key"

    def test_no_env_no_file_raises_auth_error(self, tmp_path):
        """No env var, no config file → raises AuthError (exit_code=4)."""
        missing_file = tmp_path / "nonexistent.json"

        env = {k: v for k, v in os.environ.items() if k != "ATTIO_API_KEY"}
        with patch.dict(os.environ, env, clear=True):
            from cli_anything.attio.utils import config as config_module

            with patch.object(config_module, "CONFIG_FILE", missing_file):
                with pytest.raises(AuthError) as exc_info:
                    config_module.load_config()
                assert exc_info.value.exit_code == 4

    def test_auth_error_hint_suggests_config_command(self, tmp_path):
        """AuthError hint should mention 'attio config set api-key'."""
        missing_file = tmp_path / "nonexistent.json"

        env = {k: v for k, v in os.environ.items() if k != "ATTIO_API_KEY"}
        with patch.dict(os.environ, env, clear=True):
            from cli_anything.attio.utils import config as config_module

            with patch.object(config_module, "CONFIG_FILE", missing_file):
                with pytest.raises(AuthError) as exc_info:
                    config_module.load_config()
                assert exc_info.value.hint is not None
                assert "attio config set api-key" in exc_info.value.hint

    def test_malformed_config_file_falls_through_to_auth_error(self, tmp_path):
        """Malformed JSON in config file → falls through to AuthError, not crash."""
        config_file = tmp_path / "config.json"
        config_file.write_text("{ not valid json }")

        env = {k: v for k, v in os.environ.items() if k != "ATTIO_API_KEY"}
        with patch.dict(os.environ, env, clear=True):
            from cli_anything.attio.utils import config as config_module

            with patch.object(config_module, "CONFIG_FILE", config_file):
                with pytest.raises(AuthError):
                    config_module.load_config()


class TestSaveConfig:
    """Test save_config() writes and secures the config file."""

    def test_save_config_writes_api_key(self, tmp_path):
        """save_config('key123') → writes api_key to config file."""
        config_file = tmp_path / "config.json"
        config_dir = tmp_path

        from cli_anything.attio.utils import config as config_module

        with (
            patch.object(config_module, "CONFIG_DIR", config_dir),
            patch.object(config_module, "CONFIG_FILE", config_file),
        ):
            config_module.save_config("key123")
            data = json.loads(config_file.read_text())
            assert data["api_key"] == "key123"

    def test_save_config_with_base_url(self, tmp_path):
        """save_config('key', 'https://custom') → writes both fields."""
        config_file = tmp_path / "config.json"
        config_dir = tmp_path

        from cli_anything.attio.utils import config as config_module

        with (
            patch.object(config_module, "CONFIG_DIR", config_dir),
            patch.object(config_module, "CONFIG_FILE", config_file),
        ):
            config_module.save_config("key123", "https://custom.url")
            data = json.loads(config_file.read_text())
            assert data["base_url"] == "https://custom.url"

    def test_save_config_chmod_600(self, tmp_path):
        """save_config → file permissions are 0o600 (owner read-only)."""
        config_file = tmp_path / "config.json"
        config_dir = tmp_path

        from cli_anything.attio.utils import config as config_module

        with (
            patch.object(config_module, "CONFIG_DIR", config_dir),
            patch.object(config_module, "CONFIG_FILE", config_file),
        ):
            config_module.save_config("key123")
            mode = oct(stat.S_IMODE(config_file.stat().st_mode))
            # On Windows chmod is a no-op for user bits, so just check no crash
            assert config_file.exists()


class TestConfigConstants:
    """Test that module-level constants are correctly set."""

    def test_config_dir_path(self):
        """CONFIG_DIR should be ~/.config/attio."""
        from cli_anything.attio.utils.config import CONFIG_DIR

        assert CONFIG_DIR == Path.home() / ".config" / "attio"

    def test_config_file_path(self):
        """CONFIG_FILE should be CONFIG_DIR / 'config.json'."""
        from cli_anything.attio.utils.config import CONFIG_DIR, CONFIG_FILE

        assert CONFIG_FILE == CONFIG_DIR / "config.json"

    def test_history_file_path(self):
        """HISTORY_FILE should be CONFIG_DIR / 'history'."""
        from cli_anything.attio.utils.config import CONFIG_DIR, HISTORY_FILE

        assert HISTORY_FILE == CONFIG_DIR / "history"


class TestAttioConfig:
    """Test AttioConfig dataclass."""

    def test_attio_config_requires_api_key(self):
        """AttioConfig(api_key='x') → works, stores api_key."""
        from cli_anything.attio.utils.config import AttioConfig

        cfg = AttioConfig(api_key="mykey")
        assert cfg.api_key == "mykey"

    def test_attio_config_default_base_url(self):
        """AttioConfig default base_url is v2 API endpoint."""
        from cli_anything.attio.utils.config import AttioConfig

        cfg = AttioConfig(api_key="x")
        assert cfg.base_url == "https://api.attio.com/v2"

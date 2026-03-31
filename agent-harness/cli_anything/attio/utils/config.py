"""Config loading from env and XDG config file."""
import json
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

from .exceptions import AuthError

# Load .env from CWD or parent dirs (no-op if not found)
load_dotenv()

CONFIG_DIR = Path.home() / ".config" / "attio"
CONFIG_FILE = CONFIG_DIR / "config.json"
HISTORY_FILE = CONFIG_DIR / "history"


@dataclass
class AttioConfig:
    api_key: str
    base_url: str = "https://api.attio.com/v2"


def load_config() -> AttioConfig:
    """D-08: ATTIO_API_KEY env var always takes precedence over config file."""
    api_key = os.getenv("ATTIO_API_KEY")
    base_url = "https://api.attio.com/v2"

    if not api_key and CONFIG_FILE.exists():
        try:
            data = json.loads(CONFIG_FILE.read_text())
            api_key = data.get("api_key")
            base_url = data.get("base_url", base_url)
        except (json.JSONDecodeError, OSError):
            pass  # Fall through to missing-key error

    if not api_key:
        raise AuthError(
            "ATTIO_API_KEY not set.",
            hint="Run: attio config set api-key <your-key>  or set ATTIO_API_KEY env var",
        )

    return AttioConfig(api_key=api_key, base_url=base_url)


def save_config(api_key: str, base_url: str | None = None) -> None:
    """Persist API key to XDG config. Chmod 0o600 for security."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    data: dict[str, str] = {"api_key": api_key}
    if base_url:
        data["base_url"] = base_url
    CONFIG_FILE.write_text(json.dumps(data, indent=2))
    CONFIG_FILE.chmod(0o600)

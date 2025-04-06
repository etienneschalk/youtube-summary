import json
from pathlib import Path
import re
from typing import Any


def sanitize_string(input_string: str) -> str:
    # Remove non-alphanumeric characters except spaces
    sanitized = re.sub(r"[^a-zA-Z0-9\s]", "", input_string)

    # Replace multiple spaces with a single space and trim
    sanitized = re.sub(r"\s+", " ", sanitized).strip()

    return sanitized


def train_case_string(input_string: str) -> str:
    clean_string = sanitize_string(input_string)
    return clean_string.lower().replace(" ", "-")


def retrieve_api_key(
    *, secrets_path: Path = Path.home() / Path(".secrets/secrets.json")
):
    if secrets_path.is_file():
        return json.loads(secrets_path.read_text())["openrouter.ai"]["api-key"]
    else:
        raise FileNotFoundError(f"No secrets found for {secrets_path = !s}")


def read_toml(file_path: Path) -> dict[str, Any]:
    """Read and parse a TOML file into a dictionary."""
    try:
        with open(file_path, "rb") as f:
            import tomli

            return tomli.load(f)
    except ImportError:
        raise ImportError("Install 'tomli' first: pip install tomli")

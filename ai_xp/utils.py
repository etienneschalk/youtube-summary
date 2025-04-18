import json
import re
from pathlib import Path
from typing import Any

import pandas as pd
from slugify import slugify


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


def render_title_slug(title: str, *, limit: int = 128) -> str:
    # By default, limit to 128 characters.
    # Indeed a filename can be 255 char max. Keep the rest for language code, video id
    # and other information. The video id is the ultimate primary key.
    slug = slugify(title) or "untitled"
    return slug[:limit] if limit > 0 else slug


def render_timestamp_slug(now: pd.Timestamp) -> str:
    # Do not lowercase so the T-separator remains capitalized
    return slugify(now.isoformat(), lowercase=False)


def render_video_url(video_id: str) -> str:
    return "https://www.youtube.com/watch?v=" + video_id

"""MkDocs hook for dynamic version injection."""

from pathlib import Path
import tomllib
from typing import Any


# Read version once at module load
project_root = Path(__file__).parent.parent
pyproject_path = project_root / "pyproject.toml"

with open(pyproject_path, "rb") as f:
    pyproject_data = tomllib.load(f)

VERSION = pyproject_data["project"]["version"]
USER_AGENT = f"AppImage-Updater/{VERSION}"


def on_page_markdown(markdown: str, **_kwargs: Any) -> str:
    """Replace version placeholders in markdown content."""
    return markdown.replace("{{VERSION}}", VERSION).replace("{{USER_AGENT}}", USER_AGENT)

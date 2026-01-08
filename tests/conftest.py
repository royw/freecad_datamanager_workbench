"""Pytest configuration for the DataManager repository.

Adds the in-repo package path to `sys.path` so unit tests can import the
workbench modules without installation.
"""

from __future__ import annotations

from pathlib import Path
import sys


_repo_root = Path(__file__).resolve().parents[1]
_sys_path_entry = str(_repo_root / "datamanager_wb")
if _sys_path_entry not in sys.path:
    sys.path.insert(0, _sys_path_entry)

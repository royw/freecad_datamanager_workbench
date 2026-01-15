"""Compatibility wrapper for FreeCAD workbench initialization."""

# Import for side effects: FreeCAD workbench registration occurs at import time.
from .entrypoints import init_gui as _init_gui  # noqa: F401

__all__: list[str] = []

"""App port abstraction for FreeCAD-dependent behavior.

This module isolates FreeCAD (App) access behind a small interface so modules can
be imported and tested without a running FreeCAD environment.
"""

from __future__ import annotations

from typing import Protocol


class AppPort(Protocol):
    """Port interface for FreeCAD (App) dependent operations."""

    def translate(self, context: str, text: str) -> str:
        """Translate UI strings."""


class FreeCadAppAdapter:
    """Runtime implementation of `AppPort` using FreeCAD."""

    def translate(self, context: str, text: str) -> str:
        """Translate UI strings via FreeCAD's Qt translation."""

        import FreeCAD as App  # pylint: disable=import-error

        value: object = App.Qt.translate(context, text)
        if isinstance(value, str):
            return value
        return str(value)

"""Ports and adapters for FreeCAD runtime access.

This module defines a small "port" interface that encapsulates the parts of the
FreeCAD runtime needed by UI-facing orchestration code.

The goal is to keep FreeCAD-specific quirks (optional GUI module, duck-typed
objects, and defensive `getattr` usage) localized to a single adapter.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .freecad_context import FreeCadContext


class FreeCadPort(Protocol):
    """Port interface for the small slice of FreeCAD used by controllers."""

    def get_active_document(self) -> object | None:
        """Return the active document, if any."""

    def try_recompute_active_document(self) -> None:
        """Attempt to recompute the active document.

        This method must swallow all exceptions to keep the UI responsive.
        """

    def try_update_gui(self) -> None:
        """Attempt to update the FreeCAD GUI.

        This method must swallow all exceptions to keep the UI responsive.
        """


@dataclass(frozen=True)
class FreeCadContextAdapter:
    """Runtime adapter that implements :class:`FreeCadPort` using `FreeCadContext`."""

    ctx: FreeCadContext

    def get_active_document(self) -> object | None:
        """Return the active document, if any."""
        doc = self.ctx.app.ActiveDocument
        if doc is None:
            return None
        return doc

    def try_recompute_active_document(self) -> None:
        """Attempt to recompute the active document, swallowing exceptions."""
        doc = self.ctx.app.ActiveDocument
        if doc is None:
            return
        try:
            recompute = getattr(doc, "recompute", None)
            if callable(recompute):
                recompute()
        except Exception:  # pylint: disable=broad-exception-caught
            pass

    def try_update_gui(self) -> None:
        """Attempt to update the GUI, swallowing exceptions."""
        try:
            gui = self.ctx.gui
            updater = getattr(gui, "updateGui", None) if gui is not None else None
            if callable(updater):
                updater()
        except Exception:  # pylint: disable=broad-exception-caught
            pass

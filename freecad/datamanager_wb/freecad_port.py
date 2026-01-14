"""Ports and adapters for FreeCAD runtime access.

This module defines a small "port" interface that encapsulates the parts of the
FreeCAD runtime needed by UI-facing orchestration code.

The goal is to keep FreeCAD-specific quirks (optional GUI module, duck-typed
objects, and defensive `getattr` usage) localized to a single adapter.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, cast

from .freecad_context import FreeCadContext


class FreeCadPort(Protocol):
    """Port interface for the small slice of FreeCAD used by controllers."""

    def get_active_document(self) -> object | None:
        """Return the active document, if any."""

    def get_object(self, doc: object, name: str) -> object | None:
        """Return an object by name from the given document, if possible."""

    def get_typed_object(self, doc: object, name: str, *, type_id: str) -> object | None:
        """Return an object by name only if its `TypeId` matches."""

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

    def get_object(self, doc: object, name: str) -> object | None:
        """Return an object by name from the given document, if possible."""
        getter = getattr(doc, "getObject", None)
        if not callable(getter):
            return None
        try:
            return cast(object | None, getter(name))
        except Exception:  # pylint: disable=broad-exception-caught
            return None

    def get_typed_object(self, doc: object, name: str, *, type_id: str) -> object | None:
        """Return an object by name only if its `TypeId` matches."""
        obj = self.get_object(doc, name)
        if obj is None or getattr(obj, "TypeId", None) != type_id:
            return None
        return obj

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

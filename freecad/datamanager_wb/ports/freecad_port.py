"""Ports and adapters for FreeCAD runtime access.

This module defines a small "port" interface that encapsulates the parts of the
FreeCAD runtime needed by UI-facing orchestration code.

The goal is to keep FreeCAD-specific quirks (optional GUI module, duck-typed
objects, and defensive `getattr` usage) localized to a single adapter.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, cast

from .freecad_context import FreeCadContext, get_runtime_context


class FreeCadPort(Protocol):
    """Port interface for the small slice of FreeCAD used by controllers."""

    def get_active_document(self) -> object | None:
        """Return the active document, if any."""

    def get_object(self, doc: object, name: str) -> object | None:
        """Return an object by name from the given document, if possible."""

    def get_typed_object(self, doc: object, name: str, *, type_id: str) -> object | None:
        """Return an object by name only if its `TypeId` matches."""

    def translate(self, context: str, text: str) -> str:
        """Translate the given text for UI display."""

    def log(self, text: str) -> None:
        """Write an informational message to the FreeCAD console/log."""

    def warn(self, text: str) -> None:
        """Write a warning message to the FreeCAD console/log."""

    def message(self, text: str) -> None:
        """Write a normal message to the FreeCAD console/log."""

    def clear_selection(self) -> None:
        """Clear GUI selection if the GUI is available."""

    def add_selection(self, *, doc_name: str, obj_name: str) -> None:
        """Add an object to GUI selection if the GUI is available."""

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

    def translate(self, context: str, text: str) -> str:
        """Translate the given text for UI display."""
        qt = getattr(self.ctx.app, "Qt", None)
        translate = getattr(qt, "translate", None)
        if not callable(translate):
            return text
        try:
            return str(translate(context, text))
        except Exception:  # pylint: disable=broad-exception-caught
            return text

    def log(self, text: str) -> None:
        """Write an informational message to the FreeCAD console/log."""
        console = getattr(self.ctx.app, "Console", None)
        printer = getattr(console, "PrintLog", None)
        if not callable(printer):
            return
        try:
            printer(text)
        except Exception:  # pylint: disable=broad-exception-caught
            return

    def warn(self, text: str) -> None:
        """Write a warning message to the FreeCAD console/log."""
        console = getattr(self.ctx.app, "Console", None)
        printer = getattr(console, "PrintWarning", None)
        if not callable(printer):
            return
        try:
            printer(text)
        except Exception:  # pylint: disable=broad-exception-caught
            return

    def message(self, text: str) -> None:
        """Write a normal message to the FreeCAD console/log."""
        console = getattr(self.ctx.app, "Console", None)
        printer = getattr(console, "PrintMessage", None)
        if not callable(printer):
            return
        try:
            printer(text)
        except Exception:  # pylint: disable=broad-exception-caught
            return

    def clear_selection(self) -> None:
        """Clear GUI selection if the GUI is available."""
        gui = getattr(self.ctx, "gui", None)
        selection = getattr(gui, "Selection", None) if gui is not None else None
        clearer = getattr(selection, "clearSelection", None)
        if not callable(clearer):
            return
        try:
            clearer()
        except Exception:  # pylint: disable=broad-exception-caught
            return

    def add_selection(self, *, doc_name: str, obj_name: str) -> None:
        """Add an object to GUI selection if the GUI is available."""
        gui = getattr(self.ctx, "gui", None)
        selection = getattr(gui, "Selection", None) if gui is not None else None
        adder = getattr(selection, "addSelection", None)
        if not callable(adder):
            return
        try:
            adder(doc_name, obj_name)
        except Exception:  # pylint: disable=broad-exception-caught
            return

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


def get_port(ctx: FreeCadContext | None = None) -> FreeCadPort:
    """Return a :class:`FreeCadPort` backed by the given context.

    When `ctx` is not provided, this function obtains the real FreeCAD runtime
    context via :func:`get_runtime_context`.
    """
    if ctx is None:
        ctx = get_runtime_context()
    return FreeCadContextAdapter(ctx)

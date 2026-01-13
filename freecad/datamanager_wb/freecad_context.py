"""FreeCAD runtime context abstraction.

This module provides small Protocol interfaces for the parts of the FreeCAD API
used by this workbench, plus a `FreeCadContext` wrapper that can be injected
into non-UI code for testing.

Use `get_runtime_context()` to obtain the real runtime bindings.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class QtLike(Protocol):
    def translate(self, context: str, text: str) -> str: ...


class ConsoleLike(Protocol):
    def PrintMessage(self, text: str) -> None: ...


class DocumentLike(Protocol):
    Objects: list[object]

    def getObject(self, name: str) -> object | None: ...


class AppLike(Protocol):
    ActiveDocument: DocumentLike | None
    Qt: QtLike
    Console: ConsoleLike


class GuiLike(Protocol): ...


@dataclass(frozen=True)
class FreeCadContext:
    app: AppLike
    gui: GuiLike | None = None


def get_runtime_context() -> FreeCadContext:
    import FreeCAD as App

    try:
        import FreeCADGui as Gui
    except Exception:  # pylint: disable=broad-exception-caught
        Gui = None

    return FreeCadContext(app=App, gui=Gui)

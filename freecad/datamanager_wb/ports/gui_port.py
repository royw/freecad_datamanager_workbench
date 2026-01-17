# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileNotice: Part of the DataManager addon.

"""GUI port abstraction for FreeCADGui-dependent behavior.

This module isolates FreeCADGui/PySideUic access behind a small interface so the
UI layer can be tested without importing FreeCADGui.
"""

from __future__ import annotations

from typing import Protocol, cast


class _HasFindChild(Protocol):
    def findChild(self, _type: object) -> object | None:  # noqa: ANN401
        """Return the first child matching the given Qt type."""
        ...


class _HasAddSubWindow(Protocol):
    def addSubWindow(self, widget: object) -> object:  # noqa: ANN401
        """Add a widget as an MDI subwindow and return the created subwindow."""
        ...


class GuiPort(Protocol):
    """Port interface for FreeCADGui-dependent operations."""

    def load_ui(self, ui_path: str) -> object:  # noqa: ANN401
        """Load a Qt Designer .ui file and return the root form."""

    def get_main_window(self) -> object:  # noqa: ANN401
        """Return the FreeCAD main window."""

    def get_mdi_area(self) -> object | None:  # noqa: ANN401
        """Return the QMdiArea of the FreeCAD main window when available."""

    def add_subwindow(self, *, mdi_area: object, widget: object) -> object:  # noqa: ANN401
        """Add a widget as a subwindow under the given MDI area."""


class FreeCadGuiAdapter:
    """Runtime implementation of `GuiPort` using FreeCADGui."""

    def load_ui(self, ui_path: str) -> object:  # noqa: ANN401
        """Load a Qt Designer .ui file via FreeCADGui."""
        import FreeCADGui as Gui  # pylint: disable=import-error

        return Gui.PySideUic.loadUi(ui_path)

    def get_main_window(self) -> object:  # noqa: ANN401
        """Return the FreeCAD main window via FreeCADGui."""
        import FreeCADGui as Gui  # pylint: disable=import-error

        return Gui.getMainWindow()

    def get_mdi_area(self) -> object | None:  # noqa: ANN401
        """Return the QMdiArea from the FreeCAD main window, if present."""
        from PySide import QtWidgets

        main_window = self.get_main_window()
        has_find_child = cast(_HasFindChild, main_window)
        mdi = has_find_child.findChild(QtWidgets.QMdiArea)
        return mdi

    def add_subwindow(self, *, mdi_area: object, widget: object) -> object:  # noqa: ANN401
        """Add a widget to an MDI area and return the created subwindow."""
        has_add = cast(_HasAddSubWindow, mdi_area)
        return has_add.addSubWindow(widget)

"""FreeCAD command registrations for the DataManager workbench.

This module defines the toolbar/menu commands and connects them to the
workbench's main panel."""

import os
from collections.abc import Callable
from typing import TYPE_CHECKING

import FreeCAD as App
import FreeCADGui as Gui

from .resources import ICONPATH

translate = App.Qt.translate

if TYPE_CHECKING:
    from .main_panel import MainPanel


GetMainPanel = Callable[[], "MainPanel"]


class _VarsetManagementCommand:
    def __init__(self, get_main_panel: GetMainPanel) -> None:
        self._get_main_panel = get_main_panel

    def GetResources(self) -> dict[str, str]:
        """Return FreeCAD command metadata for UI integration.

        FreeCAD calls this to populate menu text, tooltip, and toolbar icon.
        """
        return {
            "MenuText": translate("Workbench", "Varset Management"),
            "ToolTip": translate("Workbench", "Manage VarSets"),
            "Pixmap": os.path.join(ICONPATH, "Varsets.svg"),
        }

    def IsActive(self) -> bool:
        """Return whether the command should be enabled.

        DataManager commands are always available once the GUI is running.
        """
        return True

    def Activated(self) -> None:
        """Show the DataManager panel focused on the VarSets tab."""
        self._get_main_panel().show(tab_index=0)


class _AliasManagementCommand:
    def __init__(self, get_main_panel: GetMainPanel) -> None:
        self._get_main_panel = get_main_panel

    def GetResources(self) -> dict[str, str]:
        """Return FreeCAD command metadata for UI integration."""
        return {
            "MenuText": translate("Workbench", "Alias Management"),
            "ToolTip": translate("Workbench", "Manage Aliases"),
            "Pixmap": os.path.join(ICONPATH, "Aliases.svg"),
        }

    def IsActive(self) -> bool:
        """Return whether the command should be enabled."""
        return True

    def Activated(self) -> None:
        """Show the DataManager panel focused on the Aliases tab."""
        self._get_main_panel().show(tab_index=1)


def register_commands(get_main_panel: GetMainPanel) -> None:
    """Register the DataManager commands with FreeCAD.

    Args:
        get_main_panel: Factory used by command activation to show/reuse a
            singleton MainPanel.
    """
    Gui.addCommand("DataManagerVarsetManagement", _VarsetManagementCommand(get_main_panel))
    Gui.addCommand("DataManagerAliasManagement", _AliasManagementCommand(get_main_panel))

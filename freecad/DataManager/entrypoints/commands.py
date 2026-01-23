# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileNotice: Part of the DataManager addon.

"""FreeCAD command registrations for the DataManager workbench.

This module defines the toolbar/menu commands and connects them to the
workbench's main panel."""

import os
from collections.abc import Callable
from typing import TYPE_CHECKING

from ..ports.app_port import FreeCadAppAdapter
from ..resources import ICONPATH

if TYPE_CHECKING:
    from ..ui.main_panel import MainPanel


GetMainPanel = Callable[[], "MainPanel"]


class _VarsetManagementCommand:
    def __init__(self, get_main_panel: GetMainPanel) -> None:
        self._get_main_panel = get_main_panel

    def GetResources(self) -> dict[str, str]:
        """Return FreeCAD command metadata for UI integration.

        FreeCAD calls this to populate menu text, tooltip, and toolbar icon.
        """
        translate = FreeCadAppAdapter().translate
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
        translate = FreeCadAppAdapter().translate
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
    import FreeCADGui as Gui  # pylint: disable=import-error

    Gui.addCommand("DataManager_Varsets", _VarsetManagementCommand(get_main_panel))
    Gui.addCommand("DataManager_Aliases", _AliasManagementCommand(get_main_panel))

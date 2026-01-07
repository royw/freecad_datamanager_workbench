import os
from typing import TYPE_CHECKING, Callable

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
        return {
            "MenuText": translate("Workbench", "Varset Management"),
            "ToolTip": translate("Workbench", "Manage VarSets"),
            "Pixmap": os.path.join(ICONPATH, "Varsets.svg"),
        }

    def IsActive(self) -> bool:
        return True

    def Activated(self) -> None:
        self._get_main_panel().show(tab_index=0)


class _AliasManagementCommand:
    def __init__(self, get_main_panel: GetMainPanel) -> None:
        self._get_main_panel = get_main_panel

    def GetResources(self) -> dict[str, str]:
        return {
            "MenuText": translate("Workbench", "Alias Management"),
            "ToolTip": translate("Workbench", "Manage Aliases"),
            "Pixmap": os.path.join(ICONPATH, "Aliases.svg"),
        }

    def IsActive(self) -> bool:
        return True

    def Activated(self) -> None:
        self._get_main_panel().show(tab_index=1)


def register_commands(get_main_panel: GetMainPanel) -> None:
    Gui.addCommand("DataManagerVarsetManagement", _VarsetManagementCommand(get_main_panel))
    Gui.addCommand("DataManagerAliasManagement", _AliasManagementCommand(get_main_panel))

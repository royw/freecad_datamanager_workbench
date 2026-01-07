import os

import FreeCAD as App
import FreeCADGui as Gui

translate = App.Qt.translate

ICONPATH = os.path.join(os.path.dirname(__file__), "resources", "icons")


class _VarsetManagementCommand:
    def GetResources(self) -> dict[str, str]:
        return {
            "MenuText": translate("Workbench", "Varset Management"),
            "ToolTip": translate("Workbench", "Manage VarSets"),
            "Pixmap": os.path.join(ICONPATH, "Varsets.svg"),
        }

    def IsActive(self) -> bool:
        return True

    def Activated(self) -> None:
        from .init_gui import get_main_panel

        get_main_panel().show(tab_index=0)


class _AliasManagementCommand:
    def GetResources(self) -> dict[str, str]:
        return {
            "MenuText": translate("Workbench", "Alias Management"),
            "ToolTip": translate("Workbench", "Manage Aliases"),
            "Pixmap": os.path.join(ICONPATH, "Aliases.svg"),
        }

    def IsActive(self) -> bool:
        return True

    def Activated(self) -> None:
        from .init_gui import get_main_panel

        get_main_panel().show(tab_index=1)


def register_commands() -> None:
    Gui.addCommand("DataManagerVarsetManagement", _VarsetManagementCommand())
    Gui.addCommand("DataManagerAliasManagement", _AliasManagementCommand())

"""FreeCAD workbench registration for DataManager.

Defines the `Gui.Workbench` subclass used by FreeCAD to create menus/toolbars
and activate the workbench.
"""

import os

import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore, QtWidgets

from .resources import ICONPATH

translate = App.Qt.translate
QT_TRANSLATE_NOOP = App.Qt.QT_TRANSLATE_NOOP

_ACTIVE_WORKBENCH: "DataManagerWorkbench | None" = None


def get_active_workbench() -> "DataManagerWorkbench | None":
    return _ACTIVE_WORKBENCH


class DataManagerWorkbench(Gui.Workbench):
    """
    class which gets initiated at startup of the gui
    """

    MenuText = translate("Workbench", "Data Manager")
    ToolTip = translate("Workbench", "a simple data manager workbench")
    Icon = os.path.join(ICONPATH, "datamanager_wb.svg")
    toolbox = [
        "DataManagerVarsetManagement",
        "DataManagerAliasManagement",
    ]

    def GetClassName(self):
        """
        Return the class name of the workbench
        """
        return "Gui::PythonWorkbench"

    def Initialize(self):
        """
        This function is called at the first activation of the workbench.
        here is the place to import all the commands
        """

        App.Console.PrintMessage(translate("Log", "Switching to datamanager_wb") + "\n")

        self.pending_copy: list[str] = []
        self._copy_event_filter = _CopyEventFilter(self)

        # NOTE: Context for this commands must be "Workbench"
        self.appendToolbar(QT_TRANSLATE_NOOP("Workbench", "Data Manager"), self.toolbox)
        self.appendMenu(QT_TRANSLATE_NOOP("Workbench", "Data Manager"), self.toolbox)

    def Activated(self):
        """
        code which should be computed when a user switch to this workbench
        """
        App.Console.PrintMessage(translate("Log", "Workbench datamanager_wb activated. ;-)") + "\n")

        global _ACTIVE_WORKBENCH
        _ACTIVE_WORKBENCH = self

        app = QtWidgets.QApplication.instance()
        if app is not None:
            app.installEventFilter(self._copy_event_filter)

    def Deactivated(self):
        """
        code which should be computed when this workbench is deactivated
        """
        App.Console.PrintMessage(translate("Log", "Workbench datamanager_wb de-activated.") + "\n")

        global _ACTIVE_WORKBENCH
        if _ACTIVE_WORKBENCH is self:
            _ACTIVE_WORKBENCH = None

        app = QtWidgets.QApplication.instance()
        if app is not None and hasattr(self, "_copy_event_filter"):
            app.removeEventFilter(self._copy_event_filter)


class _CopyEventFilter(QtCore.QObject):
    def __init__(self, workbench: DataManagerWorkbench):
        super().__init__()
        self._workbench = workbench

    def eventFilter(self, _watched: QtCore.QObject, event: QtCore.QEvent) -> bool:  # noqa: N802
        if event.type() != QtCore.QEvent.Type.KeyPress:
            return False

        key = getattr(event, "key", None)
        mods = getattr(event, "modifiers", None)
        if not callable(key) or not callable(mods):
            return False

        pressed_key = key()
        pressed_mods = mods()
        is_c = pressed_key in (QtCore.Qt.Key.Key_C,)
        has_ctrl = bool(pressed_mods & QtCore.Qt.KeyboardModifier.ControlModifier)
        has_meta = bool(pressed_mods & QtCore.Qt.KeyboardModifier.MetaModifier)
        if not (is_c and (has_ctrl or has_meta)):
            return False

        pending_copy = getattr(self._workbench, "pending_copy", [])
        if not pending_copy:
            return False

        QtWidgets.QApplication.clipboard().setText("\n".join(pending_copy))
        return True

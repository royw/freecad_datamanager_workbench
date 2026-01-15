"""FreeCAD workbench registration for DataManager.

Defines the `Gui.Workbench` subclass used by FreeCAD to create menus/toolbars
and activate the workbench.
"""

import os

from ..ports.freecad_port import get_port
from ..resources import ICONPATH


def _translate(context: str, text: str) -> str:
    return get_port().translate(context, text)


try:
    import FreeCADGui as Gui  # pylint: disable=import-error
except Exception:  # pylint: disable=broad-exception-caught
    Gui = None


if Gui is not None:

    class DataManagerWorkbench(Gui.Workbench):
        """
        class which gets initiated at startup of the gui
        """

        MenuText = _translate("Workbench", "Data Manager")
        ToolTip = _translate("Workbench", "a simple data manager workbench")
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

            import FreeCAD as App  # pylint: disable=import-error

            get_port().message(_translate("Log", "Switching to datamanager_wb") + "\n")

            qt_translate_noop = App.Qt.QT_TRANSLATE_NOOP

            # NOTE: Context for this commands must be "Workbench"
            self.appendToolbar(qt_translate_noop("Workbench", "Data Manager"), self.toolbox)
            self.appendMenu(qt_translate_noop("Workbench", "Data Manager"), self.toolbox)

        def Activated(self):
            """
            code which should be computed when a user switch to this workbench
            """
            get_port().message(_translate("Log", "Workbench datamanager_wb activated. ;-)") + "\n")

        def Deactivated(self):
            """
            code which should be computed when this workbench is deactivated
            """
            get_port().message(_translate("Log", "Workbench datamanager_wb de-activated.") + "\n")

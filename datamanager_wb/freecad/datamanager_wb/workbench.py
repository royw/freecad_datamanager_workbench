import os

import FreeCAD as App
import FreeCADGui as Gui

from .resources import ICONPATH

translate = App.Qt.translate
QT_TRANSLATE_NOOP = App.Qt.QT_TRANSLATE_NOOP


class DataManagerWorkbench(Gui.Workbench):
    """
    class which gets initiated at startup of the gui
    """

    MenuText = translate("Workbench", "data manager workbench")
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

        # NOTE: Context for this commands must be "Workbench"
        self.appendToolbar(QT_TRANSLATE_NOOP("Workbench", "Data Manager"), self.toolbox)
        self.appendMenu(QT_TRANSLATE_NOOP("Workbench", "Data Manager"), self.toolbox)

    def Activated(self):
        """
        code which should be computed when a user switch to this workbench
        """
        App.Console.PrintMessage(translate("Log", "Workbench datamanager_wb activated. ;-)") + "\n")

    def Deactivated(self):
        """
        code which should be computed when this workbench is deactivated
        """
        App.Console.PrintMessage(translate("Log", "Workbench datamanager_wb de-activated.") + "\n")

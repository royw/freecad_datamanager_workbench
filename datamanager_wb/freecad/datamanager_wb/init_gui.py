"""
FreeCAD datamanager workbench
"""

import functools
import os

import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore, QtWidgets

from .freecad_version_check import check_python_and_freecad_version
from .varset_tools import getVarsetReferences, getVarsets, getVarsetVariableNames

translate = App.Qt.translate
QT_TRANSLATE_NOOP = App.Qt.QT_TRANSLATE_NOOP

ICONPATH = os.path.join(os.path.dirname(__file__), "resources", "icons")
TRANSLATIONSPATH = os.path.join(os.path.dirname(__file__), "resources", "translations")

__dirname__ = os.path.dirname(__file__)

# Add translations path
Gui.addLanguagePath(TRANSLATIONSPATH)
Gui.updateLocale()


check_python_and_freecad_version()


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


@functools.lru_cache(maxsize=1)
def get_main_panel() -> "MainPanel":
    return MainPanel()


class _VarsetManagementCommand:
    def GetResources(self):
        return {
            "MenuText": translate("Workbench", "Varset Management"),
            "ToolTip": translate("Workbench", "Manage VarSets"),
            "Pixmap": os.path.join(ICONPATH, "Varsets.svg"),
        }

    def IsActive(self):
        return True

    def Activated(self):
        get_main_panel().show(tab_index=0)


class _AliasManagementCommand:
    def GetResources(self):
        return {
            "MenuText": translate("Workbench", "Alias Management"),
            "ToolTip": translate("Workbench", "Manage Aliases"),
            "Pixmap": os.path.join(ICONPATH, "Aliases.svg"),
        }

    def IsActive(self):
        return True

    def Activated(self):
        get_main_panel().show(tab_index=1)


Gui.addCommand("DataManagerVarsetManagement", _VarsetManagementCommand())
Gui.addCommand("DataManagerAliasManagement", _AliasManagementCommand())


class MainPanel:
    def __init__(self):
        App.Console.PrintMessage(translate("Log", "Workbench MainPanel initialized.") + "\n")
        self.form = Gui.PySideUic.loadUi(
            os.path.join(__dirname__, "resources", "ui", "main_panel.ui")
        )
        self._mdi_subwindow = None

        if isinstance(self.form, QtWidgets.QMainWindow):
            self._widget = self.form.centralWidget()
        else:
            self._widget = self.form

        self.availableVarsetsListWidget = self._widget.findChild(
            QtWidgets.QListWidget, "avaliableVarsetsListWidget"
        )
        self.varsetVariableNamesListWidget = self._widget.findChild(
            QtWidgets.QListWidget, "varsetVariableNamesListWidget"
        )
        self.varsetExpressionsListWidget = self._widget.findChild(
            QtWidgets.QListWidget, "varsetExpressionsListWidget"
        )
        self.tabWidget = self._widget.findChild(QtWidgets.QTabWidget, "tabWidget")

        if self.availableVarsetsListWidget is not None:
            self.availableVarsetsListWidget.setSelectionMode(
                QtWidgets.QAbstractItemView.ExtendedSelection
            )

        if self.varsetVariableNamesListWidget is not None:
            self.varsetVariableNamesListWidget.setSelectionMode(
                QtWidgets.QAbstractItemView.ExtendedSelection
            )

        if self.varsetExpressionsListWidget is not None:
            self.varsetExpressionsListWidget.setSelectionMode(
                QtWidgets.QAbstractItemView.SingleSelection
            )

        if self.availableVarsetsListWidget is not None:
            for varset in sorted(getVarsets()):
                self.availableVarsetsListWidget.addItem(varset)

            self.availableVarsetsListWidget.itemSelectionChanged.connect(
                self._on_available_varsets_selection_changed
            )
            App.Console.PrintMessage(
                translate(
                    "Log", "Workbench MainPanel: connected available varsets selection handler\n"
                )
            )

        if self.varsetVariableNamesListWidget is not None:
            self.varsetVariableNamesListWidget.itemSelectionChanged.connect(
                self._on_variable_names_selection_changed
            )

        if self.varsetExpressionsListWidget is not None:
            self.varsetExpressionsListWidget.itemSelectionChanged.connect(
                self._on_expressions_selection_changed
            )

    def _on_available_varsets_selection_changed(self):
        if self.availableVarsetsListWidget is None or self.varsetVariableNamesListWidget is None:
            App.Console.PrintMessage(
                translate("Log", "Workbench MainPanel: no varsets or variable names list widget")
                + "\n"
            )
            return

        App.Console.PrintMessage(translate("Log", "Workbench MainPanel: selection changed\n"))

        self.varsetVariableNamesListWidget.clear()
        variable_items: list[str] = []
        for item in self.availableVarsetsListWidget.selectedItems():
            varset_name = item.text()
            App.Console.PrintMessage(
                translate("Log", f"Workbench MainPanel: selected varset {varset_name}") + "\n"
            )
            for var_name in getVarsetVariableNames(varset_name):
                variable_items.append(f"{varset_name}.{var_name}")

        for variable_item in sorted(variable_items):
            self.varsetVariableNamesListWidget.addItem(variable_item)

    def _on_variable_names_selection_changed(self):
        if self.varsetVariableNamesListWidget is None or self.varsetExpressionsListWidget is None:
            return

        App.Console.PrintMessage(
            translate("Log", "Workbench MainPanel: variable selection changed\n")
        )

        self.varsetExpressionsListWidget.clear()
        expression_items: list[str] = []

        for item in self.varsetVariableNamesListWidget.selectedItems():
            text = item.text()
            App.Console.PrintMessage(
                translate("Log", f"Workbench MainPanel: selected variable {text}") + "\n"
            )
            if "." not in text:
                continue
            varset_name, variable_name = text.split(".", 1)
            refs = getVarsetReferences(varset_name, variable_name)
            refs_count = len(refs)
            App.Console.PrintMessage(
                translate(
                    "Log",
                    (
                        f"Workbench MainPanel: found {refs_count} references for "
                        f"{varset_name}.{variable_name}"
                    ),
                )
                + "\n"
            )
            for k, v in refs.items():
                expression_items.append(f"{k} = {v}")

        for expression_item in sorted(expression_items):
            self.varsetExpressionsListWidget.addItem(expression_item)

    def _on_expressions_selection_changed(self):
        if self.varsetExpressionsListWidget is None:
            return

        selected = self.varsetExpressionsListWidget.selectedItems()
        if not selected:
            return

        text = selected[0].text()
        left = text.split("=", 1)[0].strip()
        obj_name = left.split(".", 1)[0].strip()
        if not obj_name:
            return

        doc = App.ActiveDocument
        if doc is None:
            return

        obj = doc.getObject(obj_name)
        if obj is None:
            App.Console.PrintWarning(
                translate("Log", f"Workbench MainPanel: cannot find object '{obj_name}'\n")
            )
            return

        Gui.Selection.clearSelection()
        Gui.Selection.addSelection(doc.Name, obj.Name)

    def _on_subwindow_destroyed(self, _obj=None):
        get_main_panel.cache_clear()

    def accept(self):
        App.Console.PrintMessage(translate("Log", "Workbench MainPanel accepted.") + "\n")
        if self._mdi_subwindow is not None:
            self._mdi_subwindow.close()
        else:
            self.form.close()

    def reject(self):
        App.Console.PrintMessage(translate("Log", "Workbench MainPanel rejected.") + "\n")
        if self._mdi_subwindow is not None:
            self._mdi_subwindow.close()
        else:
            self.form.close()

    def show(self, tab_index: int | None = None):
        App.Console.PrintMessage(translate("Log", "Workbench MainPanel shown.") + "\n")

        if tab_index is not None and self.tabWidget is not None:
            self.tabWidget.setCurrentIndex(tab_index)

        main_window = Gui.getMainWindow()
        mdi = main_window.findChild(QtWidgets.QMdiArea)
        if mdi is None:
            App.Console.PrintWarning(
                translate("Log", "Could not find QMdiArea; showing panel as a standalone window\n")
            )
            self._widget.show()
            return

        if self._mdi_subwindow is not None:
            self._mdi_subwindow.showMaximized()
            self._mdi_subwindow.setFocus()
            return

        self._mdi_subwindow = mdi.addSubWindow(self._widget)
        self._mdi_subwindow.setWindowTitle(translate("Workbench", "Data Manager"))
        self._mdi_subwindow._dm_main_panel = self
        self._mdi_subwindow.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
        self._mdi_subwindow.destroyed.connect(self._on_subwindow_destroyed)
        self._mdi_subwindow.showMaximized()


Gui.addWorkbench(DataManagerWorkbench())

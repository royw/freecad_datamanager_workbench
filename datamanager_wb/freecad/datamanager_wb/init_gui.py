"""
FreeCAD datamanager workbench
"""

import functools
import os

import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore, QtWidgets

from .commands import register_commands
from .document_model import (
    get_expression_items,
    get_sorted_varsets,
    get_varset_variable_items,
    select_object_from_expression_item,
)
from .freecad_version_check import check_python_and_freecad_version

translate = App.Qt.translate
QT_TRANSLATE_NOOP = App.Qt.QT_TRANSLATE_NOOP

ICONPATH = os.path.join(os.path.dirname(__file__), "resources", "icons")
TRANSLATIONSPATH = os.path.join(os.path.dirname(__file__), "resources", "translations")

__dirname__ = os.path.dirname(__file__)

# Add translations path
Gui.addLanguagePath(TRANSLATIONSPATH)
Gui.updateLocale()


check_python_and_freecad_version()


register_commands()


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
            for varset in get_sorted_varsets():
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
        selected_varsets = [item.text() for item in self.availableVarsetsListWidget.selectedItems()]
        for varset_name in selected_varsets:
            App.Console.PrintMessage(
                translate("Log", f"Workbench MainPanel: selected varset {varset_name}") + "\n"
            )

        for variable_item in get_varset_variable_items(selected_varsets):
            self.varsetVariableNamesListWidget.addItem(variable_item)

    def _on_variable_names_selection_changed(self):
        if self.varsetVariableNamesListWidget is None or self.varsetExpressionsListWidget is None:
            return

        App.Console.PrintMessage(
            translate("Log", "Workbench MainPanel: variable selection changed\n")
        )

        self.varsetExpressionsListWidget.clear()
        selected_vars = [item.text() for item in self.varsetVariableNamesListWidget.selectedItems()]
        expression_items, counts = get_expression_items(selected_vars)

        for text in selected_vars:
            App.Console.PrintMessage(
                translate("Log", f"Workbench MainPanel: selected variable {text}") + "\n"
            )
            refs_count = counts.get(text, 0)
            App.Console.PrintMessage(
                translate(
                    "Log",
                    (f"Workbench MainPanel: found {refs_count} references for {text}"),
                )
                + "\n"
            )

        for expression_item in expression_items:
            self.varsetExpressionsListWidget.addItem(expression_item)

    def _on_expressions_selection_changed(self):
        if self.varsetExpressionsListWidget is None:
            return

        selected = self.varsetExpressionsListWidget.selectedItems()
        if not selected:
            return

        select_object_from_expression_item(selected[0].text())

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

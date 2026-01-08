import functools
import fnmatch
import os

import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore, QtWidgets

from .expression_item import ExpressionItem
from .panel_controller import PanelController
from .resources import UIPATH

translate = App.Qt.translate


@functools.lru_cache(maxsize=1)
def get_main_panel() -> "MainPanel":
    return MainPanel()


class MainPanel:
    def __init__(self):
        App.Console.PrintMessage(translate("Log", "Workbench MainPanel initialized.") + "\n")
        self._mdi_subwindow = None
        self._controller = PanelController()

        self.form = self._load_ui()
        self._widget = self._resolve_root_widget()

        self._find_widgets()
        self._configure_widgets()
        self._populate_varsets()
        self._connect_signals()

    def _find_required_widget(self, widget_type: type, object_name: str):
        widget = self._widget.findChild(widget_type, object_name)
        if widget is None:
            raise RuntimeError(
                translate(
                    "Log",
                    f"Workbench MainPanel: required widget not found: {object_name}",
                )
            )
        return widget

    def _load_ui(self):
        return Gui.PySideUic.loadUi(os.path.join(UIPATH, "main_panel.ui"))

    def _resolve_root_widget(self):
        if isinstance(self.form, QtWidgets.QMainWindow):
            return self.form.centralWidget()
        return self.form

    def _find_widgets(self) -> None:
        self.availableVarsetsListWidget = self._find_required_widget(
            QtWidgets.QListWidget, "avaliableVarsetsListWidget"
        )
        self.varsetVariableNamesListWidget = self._find_required_widget(
            QtWidgets.QListWidget, "varsetVariableNamesListWidget"
        )
        self.varsetExpressionsListWidget = self._find_required_widget(
            QtWidgets.QListWidget, "varsetExpressionsListWidget"
        )
        self.tabWidget = self._find_required_widget(QtWidgets.QTabWidget, "tabWidget")

        self.avaliableVarsetsFilterLineEdit = self._find_required_widget(
            QtWidgets.QLineEdit, "avaliableVarsetsFilterLineEdit"
        )
        self.avaliableVarsetsExcludeClonesRadioButton = self._find_required_widget(
            QtWidgets.QRadioButton, "avaliableVarsetsExcludeClonesRadioButton"
        )
        self.varsetVariableNamesFilterLineEdit = self._find_required_widget(
            QtWidgets.QLineEdit, "varsetVariableNamesFilterLineEdit"
        )
        self.varsetVariableNamesOnlyUnusedCheckBox = self._find_required_widget(
            QtWidgets.QCheckBox, "varsetVariableNamesOnlyUnusedCheckBox"
        )
        self.removeUnusedVariablesPushButton = self._find_required_widget(
            QtWidgets.QPushButton, "removeUnusedVariablesPushButton"
        )

    def _configure_widgets(self) -> None:
        if self.availableVarsetsListWidget is not None:
            self.availableVarsetsListWidget.setSelectionMode(
                QtWidgets.QAbstractItemView.ExtendedSelection
            )
            self.availableVarsetsListWidget.setSizeAdjustPolicy(
                QtWidgets.QAbstractScrollArea.AdjustToContents
            )

        if self.varsetVariableNamesListWidget is not None:
            self.varsetVariableNamesListWidget.setSelectionMode(
                QtWidgets.QAbstractItemView.ExtendedSelection
            )
            self.varsetVariableNamesListWidget.setSizeAdjustPolicy(
                QtWidgets.QAbstractScrollArea.AdjustToContents
            )

        if self.varsetExpressionsListWidget is not None:
            self.varsetExpressionsListWidget.setSelectionMode(
                QtWidgets.QAbstractItemView.SingleSelection
            )

        if self.removeUnusedVariablesPushButton is not None:
            self.removeUnusedVariablesPushButton.setEnabled(False)

    def _populate_varsets(self) -> None:
        if self.availableVarsetsListWidget is None:
            return

        self.availableVarsetsListWidget.clear()

        filter_text = ""
        if self.avaliableVarsetsFilterLineEdit is not None:
            filter_text = self.avaliableVarsetsFilterLineEdit.text() or ""

        filter_pattern = self._normalize_glob_pattern(filter_text)

        exclude_copy_on_change = False
        if self.avaliableVarsetsExcludeClonesRadioButton is not None:
            exclude_copy_on_change = self.avaliableVarsetsExcludeClonesRadioButton.isChecked()

        for varset in self._controller.get_sorted_varsets(
            exclude_copy_on_change=exclude_copy_on_change
        ):
            if filter_pattern is not None and not fnmatch.fnmatchcase(varset, filter_pattern):
                continue
            self.availableVarsetsListWidget.addItem(varset)

        self._adjust_list_widget_width_to_contents(self.availableVarsetsListWidget)

    def _adjust_list_widget_width_to_contents(self, widget: QtWidgets.QListWidget) -> None:
        # NOTE: This relies on the list already being populated.
        contents_width = widget.sizeHintForColumn(0)
        if contents_width < 0:
            return

        # Padding for frame and the (potential) vertical scrollbar.
        frame = widget.frameWidth() * 2
        scrollbar = widget.verticalScrollBar().sizeHint().width() + 4
        widget.setMinimumWidth(contents_width + frame + scrollbar)
        widget.updateGeometry()

    def _connect_signals(self) -> None:
        if self.availableVarsetsListWidget is not None:
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

        if self.avaliableVarsetsFilterLineEdit is not None:
            self.avaliableVarsetsFilterLineEdit.textChanged.connect(self._on_varsets_filter_changed)

        if self.avaliableVarsetsExcludeClonesRadioButton is not None:
            self.avaliableVarsetsExcludeClonesRadioButton.toggled.connect(
                self._on_exclude_clones_toggled
            )

        if self.varsetVariableNamesFilterLineEdit is not None:
            self.varsetVariableNamesFilterLineEdit.textChanged.connect(
                self._on_variable_filter_changed
            )

        if self.varsetVariableNamesOnlyUnusedCheckBox is not None:
            self.varsetVariableNamesOnlyUnusedCheckBox.toggled.connect(
                self._on_only_unused_toggled
            )

        if self.removeUnusedVariablesPushButton is not None:
            self.removeUnusedVariablesPushButton.clicked.connect(
                self._on_remove_unused_variables_clicked
            )

    def _normalize_glob_pattern(self, text: str) -> str | None:
        stripped = text.strip()
        if not stripped:
            return None

        # If the user didn't include any glob characters, treat it as a substring match.
        if not any(ch in stripped for ch in "*?[]"):
            return f"*{stripped}*"

        return stripped

    def _get_selected_varsets(self) -> list[str]:
        if self.availableVarsetsListWidget is None:
            return []
        return [item.text() for item in self.availableVarsetsListWidget.selectedItems()]

    def _get_selected_varset_variable_items(self) -> list[str]:
        if self.varsetVariableNamesListWidget is None:
            return []
        return [item.text() for item in self.varsetVariableNamesListWidget.selectedItems()]

    def _populate_variable_names(self, selected_varsets: list[str]) -> None:
        if self.varsetVariableNamesListWidget is None:
            return

        self.varsetVariableNamesListWidget.clear()

        variable_filter_text = ""
        if self.varsetVariableNamesFilterLineEdit is not None:
            variable_filter_text = self.varsetVariableNamesFilterLineEdit.text() or ""
        variable_filter_pattern = self._normalize_glob_pattern(variable_filter_text)

        only_unused = False
        if self.varsetVariableNamesOnlyUnusedCheckBox is not None:
            only_unused = self.varsetVariableNamesOnlyUnusedCheckBox.isChecked()

        items = self._controller.get_varset_variable_items(selected_varsets)

        counts: dict[str, int] = {}
        if only_unused:
            counts = self._controller.get_expression_reference_counts(items)

        for item_text in items:
            # Variable filter matches only the variable name portion (without varset prefix).
            var_name = item_text.split(".", 1)[1] if "." in item_text else item_text
            if variable_filter_pattern is not None and not fnmatch.fnmatchcase(
                var_name, variable_filter_pattern
            ):
                continue
            if only_unused and counts.get(item_text, 0) != 0:
                continue
            self.varsetVariableNamesListWidget.addItem(item_text)

        self._adjust_list_widget_width_to_contents(self.varsetVariableNamesListWidget)
        self._update_remove_unused_button_enabled_state()

    def _update_remove_unused_button_enabled_state(self) -> None:
        if self.removeUnusedVariablesPushButton is None:
            return

        only_unused = False
        if self.varsetVariableNamesOnlyUnusedCheckBox is not None:
            only_unused = self.varsetVariableNamesOnlyUnusedCheckBox.isChecked()

        any_selected = False
        if self.varsetVariableNamesListWidget is not None:
            any_selected = bool(self.varsetVariableNamesListWidget.selectedItems())

        self.removeUnusedVariablesPushButton.setEnabled(only_unused and any_selected)

    def _populate_expressions(self, selected_varset_variable_items: list[str]) -> None:
        if self.varsetExpressionsListWidget is None:
            return

        self.varsetExpressionsListWidget.clear()
        expression_items, _counts = self._controller.get_expression_items(selected_varset_variable_items)
        for expression_item in expression_items:
            item = QtWidgets.QListWidgetItem(expression_item.display_text)
            item.setData(QtCore.Qt.UserRole, expression_item)
            self.varsetExpressionsListWidget.addItem(item)

        self._update_remove_unused_button_enabled_state()

    def _on_available_varsets_selection_changed(self):
        if self.availableVarsetsListWidget is None or self.varsetVariableNamesListWidget is None:
            App.Console.PrintMessage(
                translate("Log", "Workbench MainPanel: no varsets or variable names list widget")
                + "\n"
            )
            return

        App.Console.PrintMessage(translate("Log", "Workbench MainPanel: selection changed\n"))

        selected_varsets = self._get_selected_varsets()
        for varset_name in selected_varsets:
            App.Console.PrintMessage(
                translate("Log", f"Workbench MainPanel: selected varset {varset_name}") + "\n"
            )

        self._populate_variable_names(selected_varsets)

        if self.varsetExpressionsListWidget is not None:
            self.varsetExpressionsListWidget.clear()

    def _on_variable_names_selection_changed(self):
        if self.varsetVariableNamesListWidget is None or self.varsetExpressionsListWidget is None:
            return

        App.Console.PrintMessage(
            translate("Log", "Workbench MainPanel: variable selection changed\n")
        )

        selected_vars = self._get_selected_varset_variable_items()
        expression_items, counts = self._controller.get_expression_items(selected_vars)

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
            item = QtWidgets.QListWidgetItem(expression_item.display_text)
            item.setData(QtCore.Qt.UserRole, expression_item)
            self.varsetExpressionsListWidget.addItem(item)

        self._update_remove_unused_button_enabled_state()

    def _on_varsets_filter_changed(self, _text: str) -> None:
        self._populate_varsets()
        self._on_available_varsets_selection_changed()

    def _on_variable_filter_changed(self, _text: str) -> None:
        selected_varsets = self._get_selected_varsets()
        self._populate_variable_names(selected_varsets)
        self._populate_expressions(self._get_selected_varset_variable_items())

    def _on_only_unused_toggled(self, _checked: bool) -> None:
        selected_varsets = self._get_selected_varsets()
        self._populate_variable_names(selected_varsets)
        self._populate_expressions(self._get_selected_varset_variable_items())

    def _on_remove_unused_variables_clicked(self) -> None:
        if self.varsetVariableNamesListWidget is None:
            return
        if self.varsetVariableNamesOnlyUnusedCheckBox is None:
            return
        if not self.varsetVariableNamesOnlyUnusedCheckBox.isChecked():
            self._update_remove_unused_button_enabled_state()
            return

        selected = self._get_selected_varset_variable_items()
        if not selected:
            self._update_remove_unused_button_enabled_state()
            return

        reply = QtWidgets.QMessageBox.question(
            self._widget,
            translate("Workbench", "Confirm"),
            translate(
                "Workbench",
                "Are you sure you want to remove the selected variables from the varset(s)?",
            ),
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No,
        )
        if reply != QtWidgets.QMessageBox.Yes:
            return

        _removed, still_used, failed = self._controller.remove_unused_varset_variables(selected)

        doc = App.ActiveDocument
        if doc is not None:
            try:
                doc.recompute()
            except Exception:  # pylint: disable=broad-exception-caught
                pass
        try:
            Gui.updateGui()
        except Exception:  # pylint: disable=broad-exception-caught
            pass

        if still_used or failed:
            details = []
            if still_used:
                details.append(translate("Workbench", "Still referenced (not removed):"))
                details.extend(still_used)
            if failed:
                if details:
                    details.append("")
                details.append(translate("Workbench", "Failed to remove:"))
                details.extend(failed)
            QtWidgets.QMessageBox.information(
                self._widget,
                translate("Workbench", "Remove variables"),
                translate(
                    "Workbench",
                    "Some selected variables could not be removed.",
                ),
                QtWidgets.QMessageBox.Ok,
            )

        selected_varsets = self._get_selected_varsets()
        self._populate_variable_names(selected_varsets)
        if self.varsetExpressionsListWidget is not None:
            self.varsetExpressionsListWidget.clear()
        self._update_remove_unused_button_enabled_state()

    def _on_exclude_clones_toggled(self, _checked: bool) -> None:
        self._populate_varsets()
        self._on_available_varsets_selection_changed()

    def _on_expressions_selection_changed(self):
        if self.varsetExpressionsListWidget is None:
            return

        selected = self.varsetExpressionsListWidget.selectedItems()
        if not selected:
            return

        data = selected[0].data(QtCore.Qt.UserRole)
        if isinstance(data, ExpressionItem):
            self._controller.select_expression_item(data)
        else:
            self._controller.select_expression_item(selected[0].text())

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
        self._mdi_subwindow._dm_main_panel = self  # pylint: disable=protected-access
        self._mdi_subwindow.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
        self._mdi_subwindow.destroyed.connect(self._on_subwindow_destroyed)
        self._mdi_subwindow.showMaximized()

import functools
import os

import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore, QtWidgets

from .expression_item import ExpressionItem
from .panel_controller import PanelController
from .parent_child_ref import ParentChildRef
from .parent_child_ref import parse_parent_child_ref
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
        self._populate_spreadsheets()
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

        self.availableSpreadsheetsListWidget = self._find_required_widget(
            QtWidgets.QListWidget, "avaliableSpreadsheetsListWidget"
        )
        self.aliasesVariableNamesListWidget = self._find_required_widget(
            QtWidgets.QListWidget, "aliasesVariableNamesListWidget"
        )
        self.aliasExpressionsListWidget = self._find_required_widget(
            QtWidgets.QListWidget, "aliasExpressionsListWidget"
        )

        self.avaliableSpreadsheetsFilterLineEdit = self._find_required_widget(
            QtWidgets.QLineEdit, "avaliableSpreadsheetsFilterLineEdit"
        )
        self.excludeCopyOnChangeSpreadsheetsRadioButton = self._find_required_widget(
            QtWidgets.QRadioButton, "excludeCopyOnChangeSpreadsheetsRadioButton"
        )
        self.aliasesVariableNamesFilterLineEdit = self._find_required_widget(
            QtWidgets.QLineEdit, "aliasesVariableNamesFilterLineEdit"
        )
        self.aliasesOnlyUnusedCheckBox = self._find_required_widget(
            QtWidgets.QCheckBox, "aliasesOnlyUnusedCheckBox"
        )
        self.removeUnusedAliasesPushButton = self._find_required_widget(
            QtWidgets.QPushButton, "removeUnusedAliasesPushButton"
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

        if self.availableSpreadsheetsListWidget is not None:
            self.availableSpreadsheetsListWidget.setSelectionMode(
                QtWidgets.QAbstractItemView.ExtendedSelection
            )
            self.availableSpreadsheetsListWidget.setSizeAdjustPolicy(
                QtWidgets.QAbstractScrollArea.AdjustToContents
            )

        if self.aliasesVariableNamesListWidget is not None:
            self.aliasesVariableNamesListWidget.setSelectionMode(
                QtWidgets.QAbstractItemView.ExtendedSelection
            )
            self.aliasesVariableNamesListWidget.setSizeAdjustPolicy(
                QtWidgets.QAbstractScrollArea.AdjustToContents
            )

        if self.aliasExpressionsListWidget is not None:
            self.aliasExpressionsListWidget.setSelectionMode(
                QtWidgets.QAbstractItemView.SingleSelection
            )

        if self.removeUnusedAliasesPushButton is not None:
            self.removeUnusedAliasesPushButton.setEnabled(False)

    def _populate_varsets(self) -> None:
        if self.availableVarsetsListWidget is None:
            return

        self.availableVarsetsListWidget.clear()

        filter_text = ""
        if self.avaliableVarsetsFilterLineEdit is not None:
            filter_text = self.avaliableVarsetsFilterLineEdit.text() or ""

        exclude_copy_on_change = False
        if self.avaliableVarsetsExcludeClonesRadioButton is not None:
            exclude_copy_on_change = self.avaliableVarsetsExcludeClonesRadioButton.isChecked()

        for varset in self._controller.get_filtered_varsets(
            filter_text=filter_text,
            exclude_copy_on_change=exclude_copy_on_change,
        ):
            self.availableVarsetsListWidget.addItem(varset)

        self._adjust_list_widget_width_to_contents(self.availableVarsetsListWidget)

    def _populate_spreadsheets(self) -> None:
        if self.availableSpreadsheetsListWidget is None:
            return

        self.availableSpreadsheetsListWidget.clear()

        filter_text = ""
        if self.avaliableSpreadsheetsFilterLineEdit is not None:
            filter_text = self.avaliableSpreadsheetsFilterLineEdit.text() or ""

        exclude_copy_on_change = False
        if self.excludeCopyOnChangeSpreadsheetsRadioButton is not None:
            exclude_copy_on_change = self.excludeCopyOnChangeSpreadsheetsRadioButton.isChecked()

        for sheet in self._controller.get_filtered_spreadsheets(
            filter_text=filter_text,
            exclude_copy_on_change=exclude_copy_on_change,
        ):
            self.availableSpreadsheetsListWidget.addItem(sheet)

        self._adjust_list_widget_width_to_contents(self.availableSpreadsheetsListWidget)

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

        if self.availableSpreadsheetsListWidget is not None:
            self.availableSpreadsheetsListWidget.itemSelectionChanged.connect(
                self._on_available_spreadsheets_selection_changed
            )

        if self.aliasesVariableNamesListWidget is not None:
            self.aliasesVariableNamesListWidget.itemSelectionChanged.connect(
                self._on_alias_names_selection_changed
            )

        if self.aliasExpressionsListWidget is not None:
            self.aliasExpressionsListWidget.itemSelectionChanged.connect(
                self._on_alias_expressions_selection_changed
            )

        if self.avaliableSpreadsheetsFilterLineEdit is not None:
            self.avaliableSpreadsheetsFilterLineEdit.textChanged.connect(
                self._on_spreadsheets_filter_changed
            )

        if self.excludeCopyOnChangeSpreadsheetsRadioButton is not None:
            self.excludeCopyOnChangeSpreadsheetsRadioButton.toggled.connect(
                self._on_exclude_spreadsheet_clones_toggled
            )

        if self.aliasesVariableNamesFilterLineEdit is not None:
            self.aliasesVariableNamesFilterLineEdit.textChanged.connect(
                self._on_alias_filter_changed
            )

        if self.aliasesOnlyUnusedCheckBox is not None:
            self.aliasesOnlyUnusedCheckBox.toggled.connect(
                self._on_alias_only_unused_toggled
            )

        if self.removeUnusedAliasesPushButton is not None:
            self.removeUnusedAliasesPushButton.clicked.connect(
                self._on_remove_unused_aliases_clicked
            )

    def _get_selected_varsets(self) -> list[str]:
        if self.availableVarsetsListWidget is None:
            return []
        return [item.text() for item in self.availableVarsetsListWidget.selectedItems()]

    def _get_selected_spreadsheets(self) -> list[str]:
        if self.availableSpreadsheetsListWidget is None:
            return []
        return [item.text() for item in self.availableSpreadsheetsListWidget.selectedItems()]

    def _get_selected_varset_variable_items(self) -> list[ParentChildRef]:
        if self.varsetVariableNamesListWidget is None:
            return []
        selected: list[ParentChildRef] = []
        for item in self.varsetVariableNamesListWidget.selectedItems():
            data = item.data(QtCore.Qt.UserRole)
            if isinstance(data, ParentChildRef):
                selected.append(data)
            else:
                ref = parse_parent_child_ref(item.text())
                if ref is not None:
                    selected.append(ref)
        return selected

    def _get_selected_alias_items(self) -> list[ParentChildRef]:
        if self.aliasesVariableNamesListWidget is None:
            return []
        selected: list[ParentChildRef] = []
        for item in self.aliasesVariableNamesListWidget.selectedItems():
            data = item.data(QtCore.Qt.UserRole)
            if isinstance(data, ParentChildRef):
                selected.append(data)
            else:
                ref = parse_parent_child_ref(item.text())
                if ref is not None:
                    selected.append(ref)
        return selected

    def _populate_variable_names(self, selected_varsets: list[str]) -> None:
        if self.varsetVariableNamesListWidget is None:
            return

        variable_filter_text = ""
        if self.varsetVariableNamesFilterLineEdit is not None:
            variable_filter_text = self.varsetVariableNamesFilterLineEdit.text() or ""

        only_unused = False
        if self.varsetVariableNamesOnlyUnusedCheckBox is not None:
            only_unused = self.varsetVariableNamesOnlyUnusedCheckBox.isChecked()

        items = self._controller.get_filtered_varset_variable_items(
            selected_varsets=selected_varsets,
            variable_filter_text=variable_filter_text,
            only_unused=only_unused,
        )
        self._render_variable_names(items)

    def _populate_alias_names(self, selected_sheets: list[str]) -> None:
        if self.aliasesVariableNamesListWidget is None:
            return

        alias_filter_text = ""
        if self.aliasesVariableNamesFilterLineEdit is not None:
            alias_filter_text = self.aliasesVariableNamesFilterLineEdit.text() or ""

        only_unused = False
        if self.aliasesOnlyUnusedCheckBox is not None:
            only_unused = self.aliasesOnlyUnusedCheckBox.isChecked()

        items = self._controller.get_filtered_spreadsheet_alias_items(
            selected_spreadsheets=selected_sheets,
            alias_filter_text=alias_filter_text,
            only_unused=only_unused,
        )
        App.Console.PrintMessage(
            translate(
                "Log",
                f"Workbench MainPanel: aliases populate sheets={selected_sheets} items={len(items)}\n",
            )
        )
        self._render_alias_names(items)

    def _render_variable_names(self, items: list[ParentChildRef]) -> None:
        if self.varsetVariableNamesListWidget is None:
            return

        self.varsetVariableNamesListWidget.clear()
        for ref in items:
            item = QtWidgets.QListWidgetItem(ref.text)
            item.setData(QtCore.Qt.UserRole, ref)
            self.varsetVariableNamesListWidget.addItem(item)

        self._adjust_list_widget_width_to_contents(self.varsetVariableNamesListWidget)
        self._update_remove_unused_button_enabled_state()

    def _populate_alias_expressions(self, selected_alias_items: list[ParentChildRef] | list[str]) -> None:
        if self.aliasExpressionsListWidget is None:
            return

        self.aliasExpressionsListWidget.clear()
        expression_items, _counts = self._controller.get_alias_expression_items(selected_alias_items)
        for expression_item in expression_items:
            item = QtWidgets.QListWidgetItem(expression_item.display_text)
            item.setData(QtCore.Qt.UserRole, expression_item)
            self.aliasExpressionsListWidget.addItem(item)

        self._update_remove_unused_aliases_button_enabled_state()

    def _render_alias_names(self, items: list[ParentChildRef]) -> None:
        if self.aliasesVariableNamesListWidget is None:
            return

        self.aliasesVariableNamesListWidget.clear()
        for ref in items:
            item = QtWidgets.QListWidgetItem(ref.text)
            item.setData(QtCore.Qt.UserRole, ref)
            self.aliasesVariableNamesListWidget.addItem(item)

        self._adjust_list_widget_width_to_contents(self.aliasesVariableNamesListWidget)
        self._update_remove_unused_aliases_button_enabled_state()

    def _update_remove_unused_button_enabled_state(self) -> None:
        if self.removeUnusedVariablesPushButton is None:
            return

        only_unused = False
        if self.varsetVariableNamesOnlyUnusedCheckBox is not None:
            only_unused = self.varsetVariableNamesOnlyUnusedCheckBox.isChecked()

        selected_count = 0
        if self.varsetVariableNamesListWidget is not None:
            selected_count = len(self.varsetVariableNamesListWidget.selectedItems())
        self.removeUnusedVariablesPushButton.setEnabled(
            self._controller.should_enable_remove_unused(
                only_unused=only_unused,
                selected_count=selected_count,
            )
        )

    def _update_remove_unused_aliases_button_enabled_state(self) -> None:
        if self.removeUnusedAliasesPushButton is None:
            return

        only_unused = False
        if self.aliasesOnlyUnusedCheckBox is not None:
            only_unused = self.aliasesOnlyUnusedCheckBox.isChecked()

        selected_count = 0
        if self.aliasesVariableNamesListWidget is not None:
            selected_count = len(self.aliasesVariableNamesListWidget.selectedItems())
        self.removeUnusedAliasesPushButton.setEnabled(
            self._controller.should_enable_remove_unused(
                only_unused=only_unused,
                selected_count=selected_count,
            )
        )

    def _populate_expressions(
        self, selected_varset_variable_items: list[ParentChildRef] | list[str]
    ) -> None:
        if self.varsetExpressionsListWidget is None:
            return

        self.varsetExpressionsListWidget.clear()
        expression_items, _counts = self._controller.get_expression_items(selected_varset_variable_items)
        for expression_item in expression_items:
            item = QtWidgets.QListWidgetItem(expression_item.display_text)
            item.setData(QtCore.Qt.UserRole, expression_item)
            self.varsetExpressionsListWidget.addItem(item)

        self._update_remove_unused_button_enabled_state()

    def _on_alias_names_selection_changed(self):
        if self.aliasesVariableNamesListWidget is None or self.aliasExpressionsListWidget is None:
            return

        selected_aliases = self._get_selected_alias_items()
        self._populate_alias_expressions(selected_aliases)

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

    def _on_available_spreadsheets_selection_changed(self):
        if self.availableSpreadsheetsListWidget is None or self.aliasesVariableNamesListWidget is None:
            return

        selected = self._get_selected_spreadsheets()
        App.Console.PrintMessage(
            translate("Log", f"Workbench MainPanel: selected spreadsheets {selected}\n")
        )
        self._populate_alias_names(selected)

        if self.aliasExpressionsListWidget is not None:
            self.aliasExpressionsListWidget.clear()

    def _on_variable_names_selection_changed(self):
        if self.varsetVariableNamesListWidget is None or self.varsetExpressionsListWidget is None:
            return

        App.Console.PrintMessage(
            translate("Log", "Workbench MainPanel: variable selection changed\n")
        )

        selected_vars = self._get_selected_varset_variable_items()
        expression_items, counts = self._controller.get_expression_items(selected_vars)

        for ref in selected_vars:
            text = ref.text
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

    def _on_spreadsheets_filter_changed(self, _text: str) -> None:
        self._populate_spreadsheets()
        self._on_available_spreadsheets_selection_changed()

    def _on_variable_filter_changed(self, _text: str) -> None:
        selected_varsets = self._get_selected_varsets()
        self._populate_variable_names(selected_varsets)
        self._populate_expressions(self._get_selected_varset_variable_items())

    def _on_alias_filter_changed(self, _text: str) -> None:
        selected = self._get_selected_spreadsheets()
        self._populate_alias_names(selected)
        self._populate_alias_expressions(self._get_selected_alias_items())

    def _on_only_unused_toggled(self, _checked: bool) -> None:
        selected_varsets = self._get_selected_varsets()
        self._populate_variable_names(selected_varsets)
        self._populate_expressions(self._get_selected_varset_variable_items())

    def _on_alias_only_unused_toggled(self, _checked: bool) -> None:
        selected = self._get_selected_spreadsheets()
        self._populate_alias_names(selected)
        self._populate_alias_expressions(self._get_selected_alias_items())

    def _get_remove_unused_context(self):
        selected = self._get_selected_varset_variable_items()
        selected_varsets = self._get_selected_varsets()

        variable_filter_text = ""
        if self.varsetVariableNamesFilterLineEdit is not None:
            variable_filter_text = self.varsetVariableNamesFilterLineEdit.text() or ""

        only_unused = False
        if self.varsetVariableNamesOnlyUnusedCheckBox is not None:
            only_unused = self.varsetVariableNamesOnlyUnusedCheckBox.isChecked()

        return selected, selected_varsets, variable_filter_text, only_unused

    def _confirm_remove_unused(self) -> bool:
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
        return reply == QtWidgets.QMessageBox.Yes

    def _show_remove_unused_errors(self, result) -> None:
        if not (result.still_used or result.failed):
            return

        details = []
        if result.still_used:
            details.append(translate("Workbench", "Still referenced (not removed):"))
            details.extend(result.still_used)
        if result.failed:
            if details:
                details.append("")
            details.append(translate("Workbench", "Failed to remove:"))
            details.extend(result.failed)

        QtWidgets.QMessageBox.information(
            self._widget,
            translate("Workbench", "Remove variables"),
            translate(
                "Workbench",
                "Some selected variables could not be removed.",
            ),
            QtWidgets.QMessageBox.Ok,
        )

    def _apply_post_remove_update(self, update) -> None:
        self._render_variable_names(update.variable_items)
        if update.clear_expressions and self.varsetExpressionsListWidget is not None:
            self.varsetExpressionsListWidget.clear()
        self._update_remove_unused_button_enabled_state()

    def _on_remove_unused_variables_clicked(self) -> None:
        if self.varsetVariableNamesListWidget is None:
            return
        if self.varsetVariableNamesOnlyUnusedCheckBox is None:
            return

        selected, selected_varsets, variable_filter_text, only_unused = (
            self._get_remove_unused_context()
        )

        if not self._controller.can_remove_unused(
            only_unused=only_unused,
            selected_items=selected,
        ):
            self._update_remove_unused_button_enabled_state()
            return

        if not self._confirm_remove_unused():
            return

        combined = self._controller.remove_unused_and_get_update(
            selected_varset_variable_items=selected,
            selected_varsets=selected_varsets,
            variable_filter_text=variable_filter_text,
            only_unused=only_unused,
        )

        self._show_remove_unused_errors(combined.remove_result)
        self._apply_post_remove_update(combined.update)

    def _get_remove_unused_aliases_context(self):
        selected = self._get_selected_alias_items()
        selected_sheets = self._get_selected_spreadsheets()

        alias_filter_text = ""
        if self.aliasesVariableNamesFilterLineEdit is not None:
            alias_filter_text = self.aliasesVariableNamesFilterLineEdit.text() or ""

        only_unused = False
        if self.aliasesOnlyUnusedCheckBox is not None:
            only_unused = self.aliasesOnlyUnusedCheckBox.isChecked()

        return selected, selected_sheets, alias_filter_text, only_unused

    def _confirm_remove_unused_aliases(self) -> bool:
        reply = QtWidgets.QMessageBox.question(
            self._widget,
            translate("Workbench", "Confirm"),
            translate(
                "Workbench",
                "Are you sure you want to remove the selected aliases from the spreadsheet(s)?",
            ),
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No,
        )
        return reply == QtWidgets.QMessageBox.Yes

    def _apply_post_remove_aliases_update(self, update) -> None:
        self._render_alias_names(update.variable_items)
        if update.clear_expressions and self.aliasExpressionsListWidget is not None:
            self.aliasExpressionsListWidget.clear()
        self._update_remove_unused_aliases_button_enabled_state()

    def _on_remove_unused_aliases_clicked(self) -> None:
        if self.aliasesVariableNamesListWidget is None:
            return
        if self.aliasesOnlyUnusedCheckBox is None:
            return

        selected, selected_sheets, alias_filter_text, only_unused = (
            self._get_remove_unused_aliases_context()
        )

        if not self._controller.can_remove_unused(
            only_unused=only_unused,
            selected_items=selected,
        ):
            self._update_remove_unused_aliases_button_enabled_state()
            return

        if not self._confirm_remove_unused_aliases():
            return

        combined = self._controller.remove_unused_aliases_and_get_update(
            selected_alias_items=selected,
            selected_spreadsheets=selected_sheets,
            alias_filter_text=alias_filter_text,
            only_unused=only_unused,
        )

        self._show_remove_unused_errors(combined.remove_result)
        self._apply_post_remove_aliases_update(combined.update)

    def _on_exclude_clones_toggled(self, _checked: bool) -> None:
        self._populate_varsets()
        self._on_available_varsets_selection_changed()

    def _on_exclude_spreadsheet_clones_toggled(self, _checked: bool) -> None:
        self._populate_spreadsheets()
        self._on_available_spreadsheets_selection_changed()

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

    def _on_alias_expressions_selection_changed(self):
        if self.aliasExpressionsListWidget is None:
            return

        selected = self.aliasExpressionsListWidget.selectedItems()
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

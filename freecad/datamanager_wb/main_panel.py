"""Main Qt panel for the DataManager workbench.

Loads the `.ui` file, finds widgets, wires signals, and delegates operations to
`PanelController`.
"""

import functools
import os
from collections.abc import Callable

import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore, QtWidgets

from .expression_item import ExpressionItem
from .panel_controller import PanelController
from .parent_child_ref import ParentChildRef, parse_parent_child_ref
from .resources import UIPATH

translate = App.Qt.translate

_SETTINGS_GROUP = "DataManager"
_SETTINGS_APP = "DataManagerWorkbench"
_SETTING_VARSETS_OBJECT_DISPLAY_MODE = "varsets/object_display_mode"
_SETTING_ALIASES_OBJECT_DISPLAY_MODE = "aliases/object_display_mode"
_SETTING_VARSETS_SPLITTER_STATE = "varsets/splitter_state"
_SETTING_ALIASES_SPLITTER_STATE = "aliases/splitter_state"
_DISPLAY_MODE_NAME = "name"
_DISPLAY_MODE_LABEL = "label"


@functools.lru_cache(maxsize=1)
def get_main_panel() -> "MainPanel":
    """Return a cached singleton instance of the workbench main panel.

    The workbench registers FreeCAD commands that open the panel. Using a
    cached factory ensures command activations reuse the same Qt widget instance
    instead of creating multiple panels.
    """
    return MainPanel()


class MainPanel(QtWidgets.QDialog):
    """Main Qt panel for the DataManager workbench.

    Responsibilities:

    - Load the Qt Designer `.ui` file.
    - Find and configure required widgets.
    - Connect UI signals to handler methods.
    - Delegate domain operations to `PanelController`.

    This class is the primary bridge between FreeCAD GUI events and the
    workbench controller/data layers.
    """

    def __init__(self):
        super().__init__()
        App.Console.PrintMessage(translate("Log", "Workbench MainPanel initialized.") + "\n")
        self._mdi_subwindow = None
        self._controller = PanelController()
        self._copy_map: dict[QtWidgets.QListWidget, QtWidgets.QAbstractButton] = {}
        self._active_doc_name: str | None = None
        self._active_doc_timer: QtCore.QTimer | None = None

        self.form = self._load_ui()
        self._widget = self._resolve_root_widget()

        self._find_widgets()
        self._configure_widgets()
        self._populate_varsets()
        self._populate_spreadsheets()
        self._connect_signals()
        self._start_active_document_watch()

    def _start_active_document_watch(self) -> None:
        doc = App.ActiveDocument
        self._active_doc_name = getattr(doc, "Name", None) if doc is not None else None

        timer = QtCore.QTimer(self)
        timer.setInterval(250)
        timer.timeout.connect(self._check_active_document_changed)
        timer.start()
        self._active_doc_timer = timer

    def _stop_active_document_watch(self) -> None:
        if self._active_doc_timer is None:
            return
        self._active_doc_timer.stop()
        self._active_doc_timer.deleteLater()
        self._active_doc_timer = None

    def _check_active_document_changed(self) -> None:
        doc = App.ActiveDocument
        name = getattr(doc, "Name", None) if doc is not None else None
        if name == self._active_doc_name:
            return
        self._active_doc_name = name
        self._refresh_for_active_document_change()

    def _refresh_for_active_document_change(self) -> None:
        if self.availableVarsetsListWidget is not None:
            self.availableVarsetsListWidget.clearSelection()
        if self.availableSpreadsheetsListWidget is not None:
            self.availableSpreadsheetsListWidget.clearSelection()

        self._populate_varsets()
        self._populate_spreadsheets()

        if self.varsetVariableNamesListWidget is not None:
            self.varsetVariableNamesListWidget.clear()
        if self.varsetExpressionsListWidget is not None:
            self.varsetExpressionsListWidget.clear()
        if self.aliasesVariableNamesListWidget is not None:
            self.aliasesVariableNamesListWidget.clear()
        if self.aliasExpressionsListWidget is not None:
            self.aliasExpressionsListWidget.clear()

        self._update_copy_buttons_enabled_state()

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

        self.varsetsSplitter = self._find_required_widget(QtWidgets.QSplitter, "splitter")
        self.aliasesSplitter = self._find_required_widget(QtWidgets.QSplitter, "aliases_splitter")

        self.objectNameRadioButton = self._find_required_widget(
            QtWidgets.QRadioButton, "objectNameRadioButton"
        )
        self.objectLabelRadioButton = self._find_required_widget(
            QtWidgets.QRadioButton, "objectLabelRadioButton"
        )
        self.aliasesObjectNameRadioButton = self._find_required_widget(
            QtWidgets.QRadioButton, "aliasesObjectNameRadioButton"
        )
        self.aliasesObjectLabelRadioButton = self._find_required_widget(
            QtWidgets.QRadioButton, "aliasesObjectLabelRadioButton"
        )

        self.copyAvailableVarsetsPushButton = self._find_required_widget(
            QtWidgets.QToolButton, "copyAvailableVarsetsPushButton"
        )
        self.copyVarsetVariablesPushButton = self._find_required_widget(
            QtWidgets.QToolButton, "copyVarsetVariablesPushButton"
        )
        self.copyVarsetExpressionsPushButton = self._find_required_widget(
            QtWidgets.QToolButton, "copyVarsetExpressionsPushButton"
        )
        self.copyAvailableSpreadsheetsPushButton = self._find_required_widget(
            QtWidgets.QToolButton, "copyAvailableSpreadsheetsPushButton"
        )
        self.copyAliasesPushButton = self._find_required_widget(
            QtWidgets.QToolButton, "copyAliasesPushButton"
        )
        self.copyAliasExpressionsPushButton = self._find_required_widget(
            QtWidgets.QToolButton, "copyAliasExpressionsPushButton"
        )

    def _configure_widgets(self) -> None:
        self._configure_varsets_widgets()
        self._configure_aliases_widgets()
        self._configure_copy_controls()
        self._restore_object_display_mode_radio_state()
        self._restore_splitter_states()

    def _configure_copy_controls(self) -> None:
        self._copy_map = {
            self.availableVarsetsListWidget: self.copyAvailableVarsetsPushButton,
            self.varsetVariableNamesListWidget: self.copyVarsetVariablesPushButton,
            self.varsetExpressionsListWidget: self.copyVarsetExpressionsPushButton,
            self.availableSpreadsheetsListWidget: self.copyAvailableSpreadsheetsPushButton,
            self.aliasesVariableNamesListWidget: self.copyAliasesPushButton,
            self.aliasExpressionsListWidget: self.copyAliasExpressionsPushButton,
        }

        for list_widget, button in self._copy_map.items():
            if list_widget is None or button is None:
                continue

            button.setText("")
            button.setToolTip(translate("Workbench", "Copy selection"))
            if isinstance(button, QtWidgets.QToolButton):
                button.setAutoRaise(True)
                button.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonIconOnly)
            button.setSizePolicy(
                QtWidgets.QSizePolicy.Policy.Fixed,
                QtWidgets.QSizePolicy.Policy.Fixed,
            )
            button.setIconSize(QtCore.QSize(16, 16))
            button.setFixedSize(QtCore.QSize(20, 20))
            button.setEnabled(False)
            list_widget.installEventFilter(self)

    def eventFilter(self, watched: QtCore.QObject, event: QtCore.QEvent) -> bool:  # noqa: N802
        if isinstance(watched, QtWidgets.QListWidget) and watched in self._copy_map:
            if event.type() in (
                QtCore.QEvent.Type.FocusIn,
                QtCore.QEvent.Type.FocusOut,
            ):
                QtCore.QTimer.singleShot(0, self._update_copy_buttons_enabled_state)
        return super().eventFilter(watched, event)

    def _is_copy_enabled_for_list(self, widget: QtWidgets.QListWidget) -> bool:
        if widget is None:
            return False
        if not widget.hasFocus():
            return False
        return len(widget.selectedItems()) > 0

    def _update_copy_buttons_enabled_state(self) -> None:
        for list_widget, button in self._copy_map.items():
            if list_widget is None or button is None:
                continue
            button.setEnabled(self._is_copy_enabled_for_list(list_widget))

    def _copy_list_selection_to_clipboard(self, widget: QtWidgets.QListWidget) -> None:
        items = widget.selectedItems()
        if not items:
            return

        text = "\n".join(i.text() for i in items)
        QtWidgets.QApplication.clipboard().setText(text)

    def _on_list_context_menu_requested(
        self, widget: QtWidgets.QListWidget, pos: QtCore.QPoint
    ) -> None:
        menu = QtWidgets.QMenu(widget)

        can_select_all = widget.selectionMode() in (
            QtWidgets.QAbstractItemView.SelectionMode.MultiSelection,
            QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection,
        )

        select_all_action = menu.addAction(translate("Workbench", "Select All"))
        select_all_action.setEnabled(can_select_all and widget.count() > 0)
        select_all_action.triggered.connect(widget.selectAll)

        copy_action = menu.addAction(translate("Workbench", "Copy"))
        copy_action.setEnabled(len(widget.selectedItems()) > 0)
        copy_action.triggered.connect(lambda _checked=False: self._on_copy_button_clicked(widget))

        menu.exec(widget.mapToGlobal(pos))

    def _on_copy_button_clicked(self, widget: QtWidgets.QListWidget | None) -> None:
        if widget is None:
            return
        # Clicking the copy button moves focus away from the list widget, so we
        # only require a selection here (enablement still depends on focus).
        selected_items = widget.selectedItems()
        if len(selected_items) == 0:
            return
        self._copy_list_selection_to_clipboard(widget)

    def _configure_list_widget(
        self,
        widget: QtWidgets.QListWidget | None,
        *,
        selection_mode: QtWidgets.QAbstractItemView.SelectionMode,
        adjust_to_contents: bool = False,
    ) -> None:
        if widget is None:
            return
        widget.setSelectionMode(selection_mode)
        if adjust_to_contents:
            widget.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)

        widget.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        widget.customContextMenuRequested.connect(
            lambda pos, w=widget: self._on_list_context_menu_requested(w, pos)
        )

    def _disable_button(self, button: QtWidgets.QPushButton | None) -> None:
        if button is not None:
            button.setEnabled(False)

    def _configure_varsets_widgets(self) -> None:
        self._configure_list_widget(
            self.availableVarsetsListWidget,
            selection_mode=QtWidgets.QAbstractItemView.ExtendedSelection,
            adjust_to_contents=True,
        )
        self._configure_list_widget(
            self.varsetVariableNamesListWidget,
            selection_mode=QtWidgets.QAbstractItemView.ExtendedSelection,
            adjust_to_contents=True,
        )
        self._configure_list_widget(
            self.varsetExpressionsListWidget,
            selection_mode=QtWidgets.QAbstractItemView.SingleSelection,
        )
        self._disable_button(self.removeUnusedVariablesPushButton)

    def _configure_aliases_widgets(self) -> None:
        self._configure_list_widget(
            self.availableSpreadsheetsListWidget,
            selection_mode=QtWidgets.QAbstractItemView.ExtendedSelection,
            adjust_to_contents=True,
        )
        self._configure_list_widget(
            self.aliasesVariableNamesListWidget,
            selection_mode=QtWidgets.QAbstractItemView.ExtendedSelection,
            adjust_to_contents=True,
        )
        self._configure_list_widget(
            self.aliasExpressionsListWidget,
            selection_mode=QtWidgets.QAbstractItemView.SingleSelection,
        )
        self._disable_button(self.removeUnusedAliasesPushButton)

    def _get_settings(self) -> QtCore.QSettings:
        return QtCore.QSettings(_SETTINGS_GROUP, _SETTINGS_APP)

    def _get_display_mode_setting(self, *, setting_key: str) -> str:
        settings = self._get_settings()
        mode = settings.value(setting_key, _DISPLAY_MODE_NAME, type=str)
        if mode not in (_DISPLAY_MODE_NAME, _DISPLAY_MODE_LABEL):
            return _DISPLAY_MODE_NAME
        return mode

    def _ensure_one_checked(
        self,
        *,
        name_button: QtWidgets.QRadioButton,
        label_button: QtWidgets.QRadioButton,
        mode: str,
    ) -> None:
        name_button.setChecked(mode == _DISPLAY_MODE_NAME)
        label_button.setChecked(mode == _DISPLAY_MODE_LABEL)
        if not (name_button.isChecked() or label_button.isChecked()):
            name_button.setChecked(True)

    def _restore_object_display_mode_radio_state(self) -> None:
        varsets_mode = self._get_display_mode_setting(
            setting_key=_SETTING_VARSETS_OBJECT_DISPLAY_MODE
        )
        aliases_mode = self._get_display_mode_setting(
            setting_key=_SETTING_ALIASES_OBJECT_DISPLAY_MODE
        )

        if self.objectNameRadioButton is not None and self.objectLabelRadioButton is not None:
            self._ensure_one_checked(
                name_button=self.objectNameRadioButton,
                label_button=self.objectLabelRadioButton,
                mode=varsets_mode,
            )

        if (
            self.aliasesObjectNameRadioButton is not None
            and self.aliasesObjectLabelRadioButton is not None
        ):
            self._ensure_one_checked(
                name_button=self.aliasesObjectNameRadioButton,
                label_button=self.aliasesObjectLabelRadioButton,
                mode=aliases_mode,
            )

    def _restore_splitter_state(self, *, setting_key: str, splitter: QtWidgets.QSplitter) -> None:
        settings = self._get_settings()
        raw = settings.value(setting_key, None)
        state: QtCore.QByteArray | None = None
        if isinstance(raw, QtCore.QByteArray):
            state = raw
        elif isinstance(raw, (bytes, bytearray)):
            state = QtCore.QByteArray(raw)
        if state is not None and not state.isEmpty():
            splitter.restoreState(state)

    def _restore_splitter_states(self) -> None:
        if self.varsetsSplitter is not None:
            self._restore_splitter_state(
                setting_key=_SETTING_VARSETS_SPLITTER_STATE,
                splitter=self.varsetsSplitter,
            )
        if self.aliasesSplitter is not None:
            self._restore_splitter_state(
                setting_key=_SETTING_ALIASES_SPLITTER_STATE,
                splitter=self.aliasesSplitter,
            )

    def _save_splitter_states(self) -> None:
        settings = self._get_settings()
        if self.varsetsSplitter is not None:
            settings.setValue(_SETTING_VARSETS_SPLITTER_STATE, self.varsetsSplitter.saveState())
        if self.aliasesSplitter is not None:
            settings.setValue(_SETTING_ALIASES_SPLITTER_STATE, self.aliasesSplitter.saveState())

    def _is_varsets_display_mode_label(self) -> bool:
        return bool(
            self.objectLabelRadioButton is not None and self.objectLabelRadioButton.isChecked()
        )

    def _is_aliases_display_mode_label(self) -> bool:
        return bool(
            self.aliasesObjectLabelRadioButton is not None
            and self.aliasesObjectLabelRadioButton.isChecked()
        )

    def _format_expression_item_for_display(
        self,
        expression_item: ExpressionItem,
        *,
        use_label: bool,
    ) -> str:
        if not use_label:
            return self._format_expression_item_basic(expression_item)

        obj_label = self._try_get_object_label(expression_item.object_name)
        if not obj_label:
            return self._format_expression_item_basic(expression_item)

        lhs = self._replace_lhs_object_prefix(expression_item.lhs, obj_label)
        return f"{lhs} {expression_item.operator} {expression_item.rhs}"

    def _format_expression_item_basic(self, expression_item: ExpressionItem) -> str:
        return f"{expression_item.lhs} {expression_item.operator} {expression_item.rhs}"

    def _try_get_object_label(self, object_name: str) -> str | None:
        doc = App.ActiveDocument
        if doc is None:
            return None
        obj = doc.getObject(object_name)
        if obj is None:
            return None
        try:
            return str(obj.Label)
        except Exception:  # pylint: disable=broad-exception-caught
            return None

    def _replace_lhs_object_prefix(self, lhs: str, obj_label: str) -> str:
        if "." not in lhs:
            return lhs
        _prefix, rest = lhs.split(".", 1)
        return f"{obj_label}.{rest}"

    def _format_named_object_for_display(self, object_name: str, *, use_label: bool) -> str:
        if not use_label:
            return object_name
        if "." in object_name:
            base_name, suffix = object_name.split(".", 1)
            base_label = self._try_get_object_label(base_name)
            if base_label:
                return f"{base_label}.{suffix}"
            return object_name
        obj_label = self._try_get_object_label(object_name)
        return obj_label if obj_label else object_name

    def _format_parent_child_ref_for_display(self, ref: ParentChildRef, *, use_label: bool) -> str:
        if not use_label:
            return ref.text
        obj_label = self._try_get_object_label(ref.parent)
        if not obj_label:
            return ref.text
        return f"{obj_label}.{ref.child}"

    def _restore_list_selection(
        self, widget: QtWidgets.QListWidget, *, selected_keys: set[str]
    ) -> None:
        if not selected_keys:
            return
        for idx in range(widget.count()):
            item = widget.item(idx)
            if item is None:
                continue
            data = item.data(QtCore.Qt.UserRole)
            key = data if isinstance(data, str) else item.text()
            if key in selected_keys:
                item.setSelected(True)

    def _restore_parent_child_ref_selection(
        self, widget: QtWidgets.QListWidget, *, selected_refs: set[ParentChildRef]
    ) -> None:
        if not selected_refs:
            return
        for idx in range(widget.count()):
            item = widget.item(idx)
            if item is None:
                continue
            data = item.data(QtCore.Qt.UserRole)
            if isinstance(data, ParentChildRef) and data in selected_refs:
                item.setSelected(True)

    def _populate_varsets(self) -> None:
        widget = self.availableVarsetsListWidget
        if widget is None:
            return
        selected = set(self._get_selected_varsets())
        widget.clear()
        filter_text = self._get_line_edit_text(self.avaliableVarsetsFilterLineEdit)
        exclude_copy_on_change = self._is_radio_checked(
            self.avaliableVarsetsExcludeClonesRadioButton
        )
        items = self._controller.get_filtered_varsets(
            filter_text=filter_text,
            exclude_copy_on_change=exclude_copy_on_change,
        )
        self._populate_parent_list_widget(
            widget, items, use_label=self._is_varsets_display_mode_label()
        )
        self._restore_list_selection(widget, selected_keys=selected)

    def _populate_spreadsheets(self) -> None:
        widget = self.availableSpreadsheetsListWidget
        if widget is None:
            return
        selected = set(self._get_selected_spreadsheets())
        widget.clear()
        filter_text = self._get_line_edit_text(self.avaliableSpreadsheetsFilterLineEdit)
        exclude_copy_on_change = self._is_radio_checked(
            self.excludeCopyOnChangeSpreadsheetsRadioButton
        )
        items = self._controller.get_filtered_spreadsheets(
            filter_text=filter_text,
            exclude_copy_on_change=exclude_copy_on_change,
        )
        self._populate_parent_list_widget(
            widget,
            items,
            use_label=self._is_aliases_display_mode_label(),
        )
        self._restore_list_selection(widget, selected_keys=selected)

    def _get_line_edit_text(self, widget: QtWidgets.QLineEdit | None) -> str:
        if widget is None:
            return ""
        return widget.text() or ""

    def _is_radio_checked(self, widget: QtWidgets.QRadioButton | None) -> bool:
        if widget is None:
            return False
        return widget.isChecked()

    def _populate_parent_list_widget(
        self, widget: QtWidgets.QListWidget, items: list[str], *, use_label: bool
    ) -> None:
        for object_name in items:
            display = self._format_named_object_for_display(object_name, use_label=use_label)
            item = QtWidgets.QListWidgetItem(display)
            item.setData(QtCore.Qt.UserRole, object_name)
            widget.addItem(item)
        self._adjust_list_widget_width_to_contents(widget)

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
        connections: list[tuple[object | None, Callable[[object], None]]] = [
            (
                self.availableVarsetsListWidget,
                lambda w: (
                    w.itemSelectionChanged.connect(self._on_available_varsets_selection_changed),
                    w.itemSelectionChanged.connect(self._update_copy_buttons_enabled_state),
                    App.Console.PrintMessage(
                        translate(
                            "Log",
                            "Workbench MainPanel: connected available varsets selection handler\n",
                        )
                    ),
                ),
            ),
            (
                self.availableSpreadsheetsListWidget,
                lambda w: (
                    w.itemSelectionChanged.connect(
                        self._on_available_spreadsheets_selection_changed
                    ),
                    w.itemSelectionChanged.connect(self._update_copy_buttons_enabled_state),
                    App.Console.PrintMessage(
                        translate(
                            "Log",
                            (
                                "Workbench MainPanel: connected available spreadsheets "
                                "selection handler\n"
                            ),
                        )
                    ),
                ),
            ),
            (
                self.varsetVariableNamesListWidget,
                lambda w: (
                    w.itemSelectionChanged.connect(self._on_variable_names_selection_changed),
                    w.itemSelectionChanged.connect(self._update_copy_buttons_enabled_state),
                ),
            ),
            (
                self.aliasesVariableNamesListWidget,
                lambda w: (
                    w.itemSelectionChanged.connect(self._on_alias_names_selection_changed),
                    w.itemSelectionChanged.connect(self._update_copy_buttons_enabled_state),
                ),
            ),
            (
                self.varsetExpressionsListWidget,
                lambda w: (
                    w.itemSelectionChanged.connect(self._on_expressions_selection_changed),
                    w.itemSelectionChanged.connect(self._update_copy_buttons_enabled_state),
                ),
            ),
            (
                self.aliasExpressionsListWidget,
                lambda w: (
                    w.itemSelectionChanged.connect(self._on_alias_expressions_selection_changed),
                    w.itemSelectionChanged.connect(self._update_copy_buttons_enabled_state),
                ),
            ),
            (
                self.avaliableVarsetsFilterLineEdit,
                lambda w: w.textChanged.connect(self._on_varsets_filter_changed),
            ),
            (
                self.avaliableVarsetsExcludeClonesRadioButton,
                lambda w: w.toggled.connect(self._on_exclude_clones_toggled),
            ),
            (
                self.varsetVariableNamesFilterLineEdit,
                lambda w: w.textChanged.connect(self._on_variable_filter_changed),
            ),
            (
                self.varsetVariableNamesOnlyUnusedCheckBox,
                lambda w: w.toggled.connect(self._on_only_unused_toggled),
            ),
            (
                self.removeUnusedVariablesPushButton,
                lambda w: w.clicked.connect(self._on_remove_unused_variables_clicked),
            ),
            (
                self.avaliableSpreadsheetsFilterLineEdit,
                lambda w: w.textChanged.connect(self._on_spreadsheets_filter_changed),
            ),
            (
                self.excludeCopyOnChangeSpreadsheetsRadioButton,
                lambda w: w.toggled.connect(self._on_exclude_spreadsheet_clones_toggled),
            ),
            (
                self.aliasesVariableNamesFilterLineEdit,
                lambda w: w.textChanged.connect(self._on_alias_filter_changed),
            ),
            (
                self.aliasesOnlyUnusedCheckBox,
                lambda w: w.toggled.connect(self._on_alias_only_unused_toggled),
            ),
            (
                self.removeUnusedAliasesPushButton,
                lambda w: w.clicked.connect(self._on_remove_unused_aliases_clicked),
            ),
            (
                self.objectNameRadioButton,
                lambda w: w.toggled.connect(self._on_varsets_object_display_mode_toggled),
            ),
            (
                self.objectLabelRadioButton,
                lambda w: w.toggled.connect(self._on_varsets_object_display_mode_toggled),
            ),
            (
                self.aliasesObjectNameRadioButton,
                lambda w: w.toggled.connect(self._on_aliases_object_display_mode_toggled),
            ),
            (
                self.aliasesObjectLabelRadioButton,
                lambda w: w.toggled.connect(self._on_aliases_object_display_mode_toggled),
            ),
            (
                self.varsetsSplitter,
                lambda w: w.splitterMoved.connect(self._on_varsets_splitter_moved),
            ),
            (
                self.aliasesSplitter,
                lambda w: w.splitterMoved.connect(self._on_aliases_splitter_moved),
            ),
            (
                self.tabWidget,
                lambda w: w.currentChanged.connect(
                    lambda _idx: self._update_copy_buttons_enabled_state()
                ),
            ),
            (
                self.copyAvailableVarsetsPushButton,
                lambda w: (
                    App.Console.PrintMessage(
                        translate(
                            "Log",
                            (
                                f"DataManager(copy): connecting {w.objectName()} "
                                "-> availableVarsetsListWidget\n"
                            ),
                        )
                    ),
                    w.pressed.connect(
                        lambda: self._on_copy_button_clicked(self.availableVarsetsListWidget)
                    ),
                    w.clicked.connect(
                        lambda _checked=False: self._on_copy_button_clicked(
                            self.availableVarsetsListWidget
                        )
                    ),
                ),
            ),
            (
                self.copyVarsetVariablesPushButton,
                lambda w: (
                    App.Console.PrintMessage(
                        translate(
                            "Log",
                            (
                                f"DataManager(copy): connecting {w.objectName()} "
                                "-> varsetVariableNamesListWidget\n"
                            ),
                        )
                    ),
                    w.pressed.connect(
                        lambda: self._on_copy_button_clicked(self.varsetVariableNamesListWidget)
                    ),
                    w.clicked.connect(
                        lambda _checked=False: self._on_copy_button_clicked(
                            self.varsetVariableNamesListWidget
                        )
                    ),
                ),
            ),
            (
                self.copyVarsetExpressionsPushButton,
                lambda w: (
                    App.Console.PrintMessage(
                        translate(
                            "Log",
                            (
                                f"DataManager(copy): connecting {w.objectName()} "
                                "-> varsetExpressionsListWidget\n"
                            ),
                        )
                    ),
                    w.pressed.connect(
                        lambda: self._on_copy_button_clicked(self.varsetExpressionsListWidget)
                    ),
                    w.clicked.connect(
                        lambda _checked=False: self._on_copy_button_clicked(
                            self.varsetExpressionsListWidget
                        )
                    ),
                ),
            ),
            (
                self.copyAvailableSpreadsheetsPushButton,
                lambda w: (
                    App.Console.PrintMessage(
                        translate(
                            "Log",
                            (
                                f"DataManager(copy): connecting {w.objectName()} "
                                "-> availableSpreadsheetsListWidget\n"
                            ),
                        )
                    ),
                    w.pressed.connect(
                        lambda: self._on_copy_button_clicked(self.availableSpreadsheetsListWidget)
                    ),
                    w.clicked.connect(
                        lambda _checked=False: self._on_copy_button_clicked(
                            self.availableSpreadsheetsListWidget
                        )
                    ),
                ),
            ),
            (
                self.copyAliasesPushButton,
                lambda w: (
                    App.Console.PrintMessage(
                        translate(
                            "Log",
                            (
                                f"DataManager(copy): connecting {w.objectName()} "
                                "-> aliasesVariableNamesListWidget\n"
                            ),
                        )
                    ),
                    w.pressed.connect(
                        lambda: self._on_copy_button_clicked(self.aliasesVariableNamesListWidget)
                    ),
                    w.clicked.connect(
                        lambda _checked=False: self._on_copy_button_clicked(
                            self.aliasesVariableNamesListWidget
                        )
                    ),
                ),
            ),
            (
                self.copyAliasExpressionsPushButton,
                lambda w: (
                    App.Console.PrintMessage(
                        translate(
                            "Log",
                            (
                                f"DataManager(copy): connecting {w.objectName()} "
                                "-> aliasExpressionsListWidget\n"
                            ),
                        )
                    ),
                    w.pressed.connect(
                        lambda: self._on_copy_button_clicked(self.aliasExpressionsListWidget)
                    ),
                    w.clicked.connect(
                        lambda _checked=False: self._on_copy_button_clicked(
                            self.aliasExpressionsListWidget
                        )
                    ),
                ),
            ),
        ]

        for widget, connector in connections:
            if widget is None:
                continue
            connector(widget)

    def _on_varsets_splitter_moved(self, _pos: int, _index: int) -> None:
        if self.varsetsSplitter is None:
            return
        settings = self._get_settings()
        settings.setValue(_SETTING_VARSETS_SPLITTER_STATE, self.varsetsSplitter.saveState())

    def _on_aliases_splitter_moved(self, _pos: int, _index: int) -> None:
        if self.aliasesSplitter is None:
            return
        settings = self._get_settings()
        settings.setValue(_SETTING_ALIASES_SPLITTER_STATE, self.aliasesSplitter.saveState())

    def _persist_display_mode(self, *, setting_key: str, mode: str) -> None:
        settings = self._get_settings()
        settings.setValue(setting_key, mode)

    def _on_varsets_object_display_mode_toggled(self, checked: bool) -> None:
        if not checked:
            return

        mode = _DISPLAY_MODE_NAME
        if self.objectLabelRadioButton is not None and self.objectLabelRadioButton.isChecked():
            mode = _DISPLAY_MODE_LABEL
        self._persist_display_mode(setting_key=_SETTING_VARSETS_OBJECT_DISPLAY_MODE, mode=mode)

        selected_varsets = self._get_selected_varsets()
        selected_vars = set(self._get_selected_varset_variable_items())
        self._populate_varsets()
        self._populate_variable_names(selected_varsets)
        if self.varsetVariableNamesListWidget is not None:
            self._restore_parent_child_ref_selection(
                self.varsetVariableNamesListWidget,
                selected_refs=selected_vars,
            )
        self._populate_expressions(self._get_selected_varset_variable_items())

    def _on_aliases_object_display_mode_toggled(self, checked: bool) -> None:
        if not checked:
            return

        mode = _DISPLAY_MODE_NAME
        if (
            self.aliasesObjectLabelRadioButton is not None
            and self.aliasesObjectLabelRadioButton.isChecked()
        ):
            mode = _DISPLAY_MODE_LABEL
        self._persist_display_mode(setting_key=_SETTING_ALIASES_OBJECT_DISPLAY_MODE, mode=mode)

        selected_sheets = self._get_selected_spreadsheets()
        selected_aliases = set(self._get_selected_alias_items())
        self._populate_spreadsheets()
        self._populate_alias_names(selected_sheets)
        if self.aliasesVariableNamesListWidget is not None:
            self._restore_parent_child_ref_selection(
                self.aliasesVariableNamesListWidget,
                selected_refs=selected_aliases,
            )
        self._populate_alias_expressions(self._get_selected_alias_items())

    def _get_selected_varsets(self) -> list[str]:
        if self.availableVarsetsListWidget is None:
            return []
        selected: list[str] = []
        for item in self.availableVarsetsListWidget.selectedItems():
            data = item.data(QtCore.Qt.UserRole)
            if isinstance(data, str) and data:
                selected.append(data)
            else:
                selected.append(item.text())
        return selected

    def _get_selected_spreadsheets(self) -> list[str]:
        if self.availableSpreadsheetsListWidget is None:
            return []
        selected: list[str] = []
        for item in self.availableSpreadsheetsListWidget.selectedItems():
            data = item.data(QtCore.Qt.UserRole)
            if isinstance(data, str) and data:
                selected.append(data)
            else:
                selected.append(item.text())
        return selected

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
                f"Workbench MainPanel: aliases populate sheets={selected_sheets} "
                f"items={len(items)}\n",
            )
        )
        self._render_alias_names(items)

    def _render_variable_names(self, items: list[ParentChildRef]) -> None:
        if self.varsetVariableNamesListWidget is None:
            return

        use_label = self._is_varsets_display_mode_label()
        self.varsetVariableNamesListWidget.clear()
        for ref in items:
            item = QtWidgets.QListWidgetItem(
                self._format_parent_child_ref_for_display(ref, use_label=use_label)
            )
            item.setData(QtCore.Qt.UserRole, ref)
            self.varsetVariableNamesListWidget.addItem(item)

        self._adjust_list_widget_width_to_contents(self.varsetVariableNamesListWidget)
        self._update_remove_unused_button_enabled_state()

    def _populate_alias_expressions(
        self, selected_alias_items: list[ParentChildRef] | list[str]
    ) -> None:
        if self.aliasExpressionsListWidget is None:
            return

        self.aliasExpressionsListWidget.clear()
        expression_items, _counts = self._controller.get_alias_expression_items(
            selected_alias_items
        )
        use_label = self._is_aliases_display_mode_label()
        for expression_item in expression_items:
            item = QtWidgets.QListWidgetItem(
                self._format_expression_item_for_display(expression_item, use_label=use_label)
            )
            item.setData(QtCore.Qt.UserRole, expression_item)
            self.aliasExpressionsListWidget.addItem(item)

        self._update_remove_unused_aliases_button_enabled_state()

    def _render_alias_names(self, items: list[ParentChildRef]) -> None:
        if self.aliasesVariableNamesListWidget is None:
            return

        use_label = self._is_aliases_display_mode_label()
        self.aliasesVariableNamesListWidget.clear()
        for ref in items:
            item = QtWidgets.QListWidgetItem(
                self._format_parent_child_ref_for_display(ref, use_label=use_label)
            )
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
        expression_items, _counts = self._controller.get_expression_items(
            selected_varset_variable_items
        )
        use_label = self._is_varsets_display_mode_label()
        for expression_item in expression_items:
            item = QtWidgets.QListWidgetItem(
                self._format_expression_item_for_display(expression_item, use_label=use_label)
            )
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
        if (
            self.availableSpreadsheetsListWidget is None
            or self.aliasesVariableNamesListWidget is None
        ):
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

        self.varsetExpressionsListWidget.clear()

        use_label = self._is_varsets_display_mode_label()

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
            item = QtWidgets.QListWidgetItem(
                self._format_expression_item_for_display(expression_item, use_label=use_label)
            )
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
        if not self._has_remove_unused_errors(result):
            return
        self._show_remove_unused_message()

    def _has_remove_unused_errors(self, result) -> bool:
        return bool(getattr(result, "still_used", None) or getattr(result, "failed", None))

    def _show_remove_unused_message(self) -> None:
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
        self._render_variable_names(update.child_items)
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
        self._render_alias_names(update.child_items)
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
        """Close the panel (Qt dialog accept semantics).

        When hosted inside FreeCAD's MDI, closes the subwindow; otherwise closes
        the top-level form.
        """
        App.Console.PrintMessage(translate("Log", "Workbench MainPanel accepted.") + "\n")
        self._stop_active_document_watch()
        self._save_splitter_states()
        if self._mdi_subwindow is not None:
            self._mdi_subwindow.close()
        else:
            self.form.close()

    def reject(self):
        """Close the panel (Qt dialog reject semantics)."""
        App.Console.PrintMessage(translate("Log", "Workbench MainPanel rejected.") + "\n")
        self._stop_active_document_watch()
        self._save_splitter_states()
        if self._mdi_subwindow is not None:
            self._mdi_subwindow.close()
        else:
            self.form.close()

    def show(self, tab_index: int | None = None):
        """Show the panel, optionally selecting a tab.

        Args:
            tab_index: When provided, selects the corresponding tab index before
                showing the panel.
        """
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

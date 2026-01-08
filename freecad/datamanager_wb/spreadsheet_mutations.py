"""Mutation helpers for spreadsheet aliases.

Contains operations that modify spreadsheets, such as clearing/removing an
alias definition.
"""

import FreeCAD as App

translate = App.Qt.translate


def _get_alias_map(spreadsheet: object) -> dict[str, str]:
    # Local minimal map extraction for mutations.
    getter = getattr(spreadsheet, "getAliases", None)
    if callable(getter):
        aliases = getter()
        if isinstance(aliases, dict):
            return {str(k): str(v) for k, v in aliases.items()}

    for prop_name in ("Alias", "Aliases"):
        alias_prop = getattr(spreadsheet, prop_name, None)
        if isinstance(alias_prop, dict):
            return {str(k): str(v) for k, v in alias_prop.items()}

    # FreeCAD builds with getAlias(cell) only.
    getter_one = getattr(spreadsheet, "getAlias", None)
    if not callable(getter_one):
        return {}

    aliases: dict[str, str] = {}
    cols = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    max_rows = 200
    max_cols = 52
    for col_idx in range(max_cols):
        a = cols[col_idx % 26]
        prefix = a if col_idx < 26 else f"{cols[(col_idx // 26) - 1]}{a}"
        for row in range(1, max_rows + 1):
            cell = f"{prefix}{row}"
            try:
                alias = getter_one(cell)
            except Exception:  # pylint: disable=broad-exception-caught
                continue
            if alias:
                aliases[str(alias)] = cell
    return aliases


def removeSpreadsheetAlias(spreadsheet_name: str, alias_name: str) -> bool:
    doc = App.ActiveDocument
    if doc is None:
        return False

    sheet = doc.getObject(spreadsheet_name)
    if sheet is None or getattr(sheet, "TypeId", None) != "Spreadsheet::Sheet":
        return False

    cell = None
    getter_cell = getattr(sheet, "getCellFromAlias", None)
    if callable(getter_cell):
        try:
            cell = getter_cell(alias_name)
        except Exception:  # pylint: disable=broad-exception-caught
            cell = None

    if not cell:
        aliases = _get_alias_map(sheet)
        cell = aliases.get(alias_name)
    if not cell:
        return False

    setter = getattr(sheet, "setAlias", None)
    if not callable(setter):
        return False

    try:
        setter(cell, "")
    except Exception:  # pylint: disable=broad-exception-caught
        try:
            setter(cell, None)
        except Exception:  # pylint: disable=broad-exception-caught
            return False

    return True

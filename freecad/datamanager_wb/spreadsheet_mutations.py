"""Mutation helpers for spreadsheet aliases.

Contains operations that modify spreadsheets, such as clearing/removing an
alias definition.
"""

from collections.abc import Mapping

from .freecad_context import FreeCadContext, get_runtime_context
from .freecad_port import FreeCadContextAdapter


def _iter_cell_coordinates(*, max_rows: int, max_cols: int) -> list[str]:
    cols = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    cells: list[str] = []
    for col_idx in range(max_cols):
        a = cols[col_idx % 26]
        prefix = a if col_idx < 26 else f"{cols[(col_idx // 26) - 1]}{a}"
        for row in range(1, max_rows + 1):
            cells.append(f"{prefix}{row}")
    return cells


def _scan_aliases_via_getAlias(spreadsheet: object) -> dict[str, str]:
    getter_one = getattr(spreadsheet, "getAlias", None)
    if not callable(getter_one):
        return {}

    result: dict[str, str] = {}
    for cell in _iter_cell_coordinates(max_rows=200, max_cols=52):
        try:
            alias = getter_one(cell)
        except Exception:  # pylint: disable=broad-exception-caught
            continue
        if alias:
            result[str(alias)] = cell
    return result


def _alias_map_from_getAliases(spreadsheet: object) -> dict[str, str]:
    getter = getattr(spreadsheet, "getAliases", None)
    if not callable(getter):
        return {}
    raw = getter()
    if isinstance(raw, Mapping):
        return {str(k): str(v) for k, v in raw.items()}
    return {}


def _alias_map_from_properties(spreadsheet: object) -> dict[str, str]:
    for prop_name in ("Alias", "Aliases"):
        alias_prop = getattr(spreadsheet, prop_name, None)
        if isinstance(alias_prop, Mapping):
            return {str(k): str(v) for k, v in alias_prop.items()}
    return {}


def _try_get_spreadsheet(
    spreadsheet_name: str,
    *,
    ctx: FreeCadContext | None = None,
) -> object | None:
    if ctx is None:
        ctx = get_runtime_context()
    port = FreeCadContextAdapter(ctx)
    doc = port.get_active_document()
    if doc is None:
        return None
    return port.get_typed_object(doc, spreadsheet_name, type_id="Spreadsheet::Sheet")


def _try_get_cell_from_alias(sheet: object, alias_name: str) -> str | None:
    getter_cell = getattr(sheet, "getCellFromAlias", None)
    if callable(getter_cell):
        try:
            cell = getter_cell(alias_name)
            if cell:
                return str(cell)
        except Exception:  # pylint: disable=broad-exception-caught
            return None

    aliases = _get_alias_map(sheet)
    cell = aliases.get(alias_name)
    if cell:
        return str(cell)
    return None


def _try_clear_alias(sheet: object, cell: str) -> bool:
    setter = getattr(sheet, "setAlias", None)
    if not callable(setter):
        return False

    try:
        setter(cell, "")
        return True
    except Exception:  # pylint: disable=broad-exception-caught
        try:
            setter(cell, None)
            return True
        except Exception:  # pylint: disable=broad-exception-caught
            return False


def _get_alias_map(spreadsheet: object) -> dict[str, str]:
    # Local minimal map extraction for mutations.
    aliases = _alias_map_from_getAliases(spreadsheet)
    if aliases:
        return aliases
    aliases = _alias_map_from_properties(spreadsheet)
    if aliases:
        return aliases
    return _scan_aliases_via_getAlias(spreadsheet)


def removeSpreadsheetAlias(
    spreadsheet_name: str,
    alias_name: str,
    *,
    ctx: FreeCadContext | None = None,
) -> bool:
    """Remove (clear) a spreadsheet alias definition.

    This function resolves the cell associated with an alias and then clears the
    alias using `Spreadsheet::Sheet.setAlias`.

    The implementation supports FreeCAD versions with different alias APIs by
    attempting:
    - `getCellFromAlias` when available
    - a local alias map extracted via `getAliases`/properties or `getAlias(cell)`

    Args:
        spreadsheet_name: Name of the `Spreadsheet::Sheet` object.
        alias_name: Alias to remove.

    Returns:
        ``True`` if the alias was cleared, otherwise ``False``.
    """
    sheet = _try_get_spreadsheet(spreadsheet_name, ctx=ctx)
    if sheet is None:
        return False

    cell = _try_get_cell_from_alias(sheet, alias_name)
    if not cell:
        return False

    return _try_clear_alias(sheet, cell)

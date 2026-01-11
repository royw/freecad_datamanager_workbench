"""Query helpers for spreadsheet aliases.

Provides discovery of spreadsheet objects, enumeration of alias names, and
searching expressions for alias references.
"""

import re
from collections.abc import Iterator, Mapping
from typing import cast

import FreeCAD as App

translate = App.Qt.translate


_CELL_RE = re.compile(r"^[A-Z]+[0-9]+$")


def _coerce_mapping(value: object) -> dict[str, str]:
    if value is None:
        return {}
    if isinstance(value, Mapping):
        return {str(k): str(v) for k, v in value.items()}
    return {}


def _count_cell_like(values: object) -> int:
    if not isinstance(values, (list, tuple, set)):
        return 0
    return sum(1 for v in values if _CELL_RE.match(str(v or "")))


def _normalize_alias_map(raw: dict[str, str]) -> dict[str, str]:
    if not raw:
        return {}

    key_cells = _count_cell_like(list(raw.keys()))
    val_cells = _count_cell_like(list(raw.values()))
    if key_cells > val_cells:
        return {alias: cell for cell, alias in raw.items()}
    return raw


def _iter_cell_coordinates(*, max_rows: int, max_cols: int) -> Iterator[str]:
    cols = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    for col_idx in range(max_cols):
        a = cols[col_idx % 26]
        prefix = a if col_idx < 26 else f"{cols[(col_idx // 26) - 1]}{a}"
        for row in range(1, max_rows + 1):
            yield f"{prefix}{row}"


def _try_get_cell_text(sheet_obj: object, cell: str) -> str | None:
    getter = getattr(sheet_obj, "getContents", None)
    if callable(getter):
        try:
            value = getter(cell)
            if isinstance(value, str):
                return value
            return str(value)
        except Exception:  # pylint: disable=broad-exception-caught
            return None

    getter = getattr(sheet_obj, "get", None)
    if callable(getter):
        try:
            value = getter(cell)
            if isinstance(value, str):
                return value
            return str(value)
        except Exception:  # pylint: disable=broad-exception-caught
            return None
    return None


def _iter_expression_engine_entries(doc: object) -> Iterator[tuple[object, object, object]]:
    for obj in getattr(doc, "Objects", []) or []:
        expressions = getattr(obj, "ExpressionEngine", None)
        if not expressions:
            continue
        for expr in expressions:
            try:
                lhs = expr[0]
                expr_text = expr[1]
            except Exception:  # pylint: disable=broad-exception-caught
                continue
            yield obj, lhs, expr_text


def _add_internal_alias_refs(
    *,
    sheet: object,
    alias_re: re.Pattern[str] | None,
    results: dict[str, str],
) -> None:
    if alias_re is None:
        return
    sheet_name = getattr(sheet, "Name", None)
    if not isinstance(sheet_name, str) or not sheet_name:
        return
    for cell in _iter_candidate_cells(sheet):
        text = _try_get_cell_text(sheet, cell)
        if not text:
            continue
        if alias_re.search(text) is not None:
            results[f"{sheet_name}.{cell}"] = text


def _build_alias_search(
    *,
    label_or_name: str,
    alias_name: str | None,
) -> tuple[list[str], re.Pattern[str] | None]:
    patterns: list[str] = [f"<<{label_or_name}>>"]
    if not alias_name:
        return patterns, None

    patterns = [
        f"<<{label_or_name}>>.{alias_name}",
        f"{label_or_name}.{alias_name}",
    ]
    alias_re = re.compile(rf"(?<![A-Za-z0-9_]){re.escape(alias_name)}(?![A-Za-z0-9_])")
    return patterns, alias_re


def _matches_expression(
    *,
    expr_text: object,
    patterns: list[str],
    alias_re: re.Pattern[str] | None,
) -> bool:
    text = str(expr_text)
    if any(p in text for p in patterns):
        return True
    if alias_re is None:
        return False
    return alias_re.search(text) is not None


def _get_active_spreadsheet(spreadsheet_name: str) -> object | None:
    doc = App.ActiveDocument
    if doc is None:
        return None
    sheet = doc.getObject(spreadsheet_name)
    if sheet is None or getattr(sheet, "TypeId", None) != "Spreadsheet::Sheet":
        return None
    return cast(object, sheet)


def _sheet_label_or_name(sheet: object) -> str:
    label_value = getattr(sheet, "Label", None)
    if label_value is None or label_value == "":
        return str(getattr(sheet, "Name", ""))
    return str(label_value)


def _collect_expression_engine_refs(
    *,
    doc: object,
    patterns: list[str],
    alias_re: re.Pattern[str] | None,
) -> dict[str, str]:
    results: dict[str, str] = {}
    for obj, lhs, expr_text in _iter_expression_engine_entries(doc):
        obj_name = getattr(obj, "Name", None)
        if not isinstance(obj_name, str) or not obj_name:
            continue
        key = f"{obj_name}{lhs}" if str(lhs).startswith(".") else f"{obj_name}.{lhs}"
        if _matches_expression(expr_text=expr_text, patterns=patterns, alias_re=alias_re):
            results[key] = str(expr_text)
    return results


def _scan_aliases_via_getAlias(spreadsheet: object) -> dict[str, str]:
    getter_one = getattr(spreadsheet, "getAlias", None)
    if not callable(getter_one):
        return {}

    aliases: dict[str, str] = {}
    for cell in _iter_candidate_cells(spreadsheet):
        try:
            alias = getter_one(cell)
        except Exception:  # pylint: disable=broad-exception-caught
            continue
        if alias:
            aliases[str(alias)] = str(cell)
    return aliases


def _scan_aliases_via_cell_from_alias(spreadsheet: object) -> dict[str, str]:
    getter_one = getattr(spreadsheet, "getAlias", None)
    cell_from_alias = getattr(spreadsheet, "getCellFromAlias", None)
    if not callable(getter_one) or not callable(cell_from_alias):
        return {}

    aliases: dict[str, str] = {}
    for cell in _iter_candidate_cells(spreadsheet):
        try:
            alias = getter_one(cell)
        except Exception:  # pylint: disable=broad-exception-caught
            continue
        if not alias:
            continue
        try:
            resolved = cell_from_alias(alias)
        except Exception:  # pylint: disable=broad-exception-caught
            resolved = None

        if resolved:
            aliases[str(alias)] = str(resolved)
        else:
            aliases[str(alias)] = str(cell)
    return aliases


def _get_copy_on_change_spreadsheet_names(doc: "App.Document") -> set[str]:
    groups: list[object] = []

    direct = doc.getObject("CopyOnChangeGroup")
    if direct is not None:
        groups.append(direct)

    for obj in getattr(doc, "Objects", []):
        label = getattr(obj, "Label", None)
        if isinstance(label, str) and label.startswith("CopyOnChangeGroup"):
            groups.append(obj)

    seen: set[int] = set()
    names: set[str] = set()

    def visit(o: object) -> None:
        oid = id(o)
        if oid in seen:
            return
        seen.add(oid)

        if getattr(o, "TypeId", None) == "Spreadsheet::Sheet":
            name = getattr(o, "Name", None)
            if isinstance(name, str) and name:
                names.add(name)
            return

        if hasattr(o, "Group"):
            for child in getattr(o, "Group", []) or []:
                visit(child)

        for child in getattr(o, "OutList", []) or []:
            visit(child)

    for group in groups:
        visit(group)

    return names


def getSpreadsheets(*, exclude_copy_on_change: bool = False) -> Iterator[str]:
    """Yield spreadsheet object names from the active document.

    Args:
        exclude_copy_on_change: When true, filters out spreadsheets that are
            created by FreeCAD's copy-on-change mechanism.

    Yields:
        The `Name` of each `Spreadsheet::Sheet` object.
    """
    doc = App.ActiveDocument
    if doc is None:
        return

    excluded: set[str] = set()
    if exclude_copy_on_change:
        excluded = _get_copy_on_change_spreadsheet_names(doc)

    for obj in getattr(doc, "Objects", []) or []:
        if getattr(obj, "TypeId", None) == "Spreadsheet::Sheet":
            if exclude_copy_on_change and getattr(obj, "Name", None) in excluded:
                continue
            yield obj.Name


def _get_alias_map(spreadsheet: object) -> dict[str, str]:
    getter = getattr(spreadsheet, "getAliases", None)
    if callable(getter):
        raw = _coerce_mapping(getter())
        normalized = _normalize_alias_map(raw)
        if normalized:
            return normalized

    # Property name differs across versions: try Alias then Aliases.
    for prop_name in ("Alias", "Aliases"):
        raw = _coerce_mapping(getattr(spreadsheet, prop_name, None))
        normalized = _normalize_alias_map(raw)
        if normalized:
            return normalized

    # Fallback for FreeCAD versions that only provide getAlias(cell) (no getAliases()).
    aliases = _scan_aliases_via_cell_from_alias(spreadsheet)
    if aliases:
        return aliases
    aliases = _scan_aliases_via_getAlias(spreadsheet)
    if aliases:
        return aliases

    return {}


def _iter_candidate_cells(spreadsheet: object) -> Iterator[str]:
    # Prefer built-in APIs if available.
    for attr in ("getUsedCells", "getNonEmptyCells", "getCells"):
        getter = getattr(spreadsheet, attr, None)
        if callable(getter):
            try:
                cells = getter()
                if cells:
                    for cell in cells:
                        if cell:
                            yield str(cell)
                    return
            except Exception:  # pylint: disable=broad-exception-caught
                pass

    # Conservative fallback scan: enough for typical alias sheets.
    # (Avoid scanning the entire spreadsheet which could be very large.)
    yield from _iter_cell_coordinates(max_rows=200, max_cols=52)


def getSpreadsheetAliasNames(spreadsheet_name: str) -> list[str]:
    """Return all alias names defined on a spreadsheet.

    Args:
        spreadsheet_name: Name of a `Spreadsheet::Sheet`.

    Returns:
        Sorted list of alias names.
    """
    doc = App.ActiveDocument
    if doc is None:
        return []

    sheet = doc.getObject(spreadsheet_name)
    if sheet is None or getattr(sheet, "TypeId", None) != "Spreadsheet::Sheet":
        return []

    names = sorted(_get_alias_map(sheet).keys())
    return names


def getSpreadsheetAliasReferences(
    spreadsheet_name: str,
    alias_name: str | None = None,
) -> dict[str, str]:
    """Find expressions that reference a spreadsheet or a specific alias.

    Args:
        spreadsheet_name: Name of the spreadsheet.
        alias_name: Optional alias name. When provided, searches for references
            to that alias; otherwise searches for references to the spreadsheet.

    Returns:
        Mapping of ``"Object.Property"`` -> expression string.
    """
    doc = App.ActiveDocument
    if doc is None:
        return {}

    sheet = _get_active_spreadsheet(spreadsheet_name)
    if sheet is None:
        return {}

    label_or_name = _sheet_label_or_name(sheet)

    patterns, alias_re = _build_alias_search(label_or_name=label_or_name, alias_name=alias_name)

    results: dict[str, str] = {}

    # Include spreadsheet-internal references (cell formulas referencing aliases).
    if alias_name is not None:
        _add_internal_alias_refs(sheet=sheet, alias_re=alias_re, results=results)

    results.update(_collect_expression_engine_refs(doc=doc, patterns=patterns, alias_re=alias_re))

    return results

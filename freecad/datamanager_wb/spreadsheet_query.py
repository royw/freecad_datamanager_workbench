"""Query helpers for spreadsheet aliases.

Provides discovery of spreadsheet objects, enumeration of alias names, and
searching expressions for alias references.
"""

import re
from collections.abc import Iterable, Iterator, Mapping, Sequence
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


def _try_call_cell_getter(sheet_obj: object, *, getter_name: str, cell: str) -> str | None:
    getter = getattr(sheet_obj, getter_name, None)
    if not callable(getter):
        return None
    try:
        value = getter(cell)
    except Exception:  # pylint: disable=broad-exception-caught
        return None
    if isinstance(value, str):
        return value
    return str(value)


def _try_get_cell_text(sheet_obj: object, cell: str) -> str | None:
    text = _try_call_cell_getter(sheet_obj, getter_name="getContents", cell=cell)
    if text is not None:
        return text
    return _try_call_cell_getter(sheet_obj, getter_name="get", cell=cell)


def _iter_doc_objects(doc: object) -> Iterator[object]:
    for obj in getattr(doc, "Objects", []) or []:
        if obj is not None:
            yield obj


def _iter_expression_engine(obj: object) -> Iterator[object]:
    expressions = getattr(obj, "ExpressionEngine", None)
    if not expressions or not isinstance(expressions, Iterable):
        return
    yield from expressions


def _try_parse_expression(expr: object) -> tuple[object, object] | None:
    if not isinstance(expr, Sequence) or len(expr) < 2:
        return None
    try:
        lhs = expr[0]
        expr_text = expr[1]
    except Exception:  # pylint: disable=broad-exception-caught
        return None
    return lhs, expr_text


def _iter_expression_engine_entries(doc: object) -> Iterator[tuple[object, object, object]]:
    for obj in _iter_doc_objects(doc):
        for expr in _iter_expression_engine(obj):
            parsed = _try_parse_expression(expr)
            if parsed is None:
                continue
            lhs, expr_text = parsed
            yield obj, lhs, expr_text


def _get_object_name(obj: object) -> str | None:
    name = getattr(obj, "Name", None)
    if isinstance(name, str) and name:
        return name
    return None


def _build_expression_key(*, obj_name: str, lhs: object) -> str:
    if str(lhs).startswith("."):
        return f"{obj_name}{lhs}"
    return f"{obj_name}.{lhs}"


def _iter_nonempty_cell_texts(sheet: object) -> Iterator[tuple[str, str]]:
    for cell in _iter_candidate_cells(sheet):
        text = _try_get_cell_text(sheet, cell)
        if text:
            yield cell, text


def _iter_alias_referenced_cells(
    sheet: object, *, alias_re: re.Pattern[str]
) -> Iterator[tuple[str, str]]:
    for cell, text in _iter_nonempty_cell_texts(sheet):
        if alias_re.search(text) is not None:
            yield cell, text


def _add_internal_alias_refs(
    *,
    sheet: object,
    alias_re: re.Pattern[str] | None,
    results: dict[str, str],
) -> None:
    if alias_re is None:
        return
    sheet_name = _get_object_name(sheet)
    if sheet_name is None:
        return
    for cell, text in _iter_alias_referenced_cells(sheet, alias_re=alias_re):
        results[f"{sheet_name}.{cell}"] = text


def _iter_cell_aliases(spreadsheet: object) -> Iterator[tuple[str, str]]:
    getter_one = getattr(spreadsheet, "getAlias", None)
    if not callable(getter_one):
        return
    for cell in _iter_candidate_cells(spreadsheet):
        try:
            alias = getter_one(cell)
        except Exception:  # pylint: disable=broad-exception-caught
            continue
        if alias:
            yield str(cell), str(alias)


def _try_resolve_cell_from_alias(spreadsheet: object, alias: str) -> str | None:
    cell_from_alias = getattr(spreadsheet, "getCellFromAlias", None)
    if not callable(cell_from_alias):
        return None
    try:
        resolved = cell_from_alias(alias)
    except Exception:  # pylint: disable=broad-exception-caught
        return None
    if resolved:
        return str(resolved)
    return None


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
        obj_name = _get_object_name(obj)
        if obj_name is None:
            continue
        key = _build_expression_key(obj_name=obj_name, lhs=lhs)
        if _matches_expression(expr_text=expr_text, patterns=patterns, alias_re=alias_re):
            results[key] = str(expr_text)
    return results


def _scan_aliases_via_getAlias(spreadsheet: object) -> dict[str, str]:
    aliases: dict[str, str] = {}
    for cell, alias in _iter_cell_aliases(spreadsheet):
        aliases[alias] = cell
    return aliases


def _get_copy_on_change_groups(doc: "App.Document") -> list[object]:
    groups: list[object] = []
    direct = doc.getObject("CopyOnChangeGroup")
    if direct is not None:
        groups.append(direct)
    for obj in getattr(doc, "Objects", []):
        label = getattr(obj, "Label", None)
        if isinstance(label, str) and label.startswith("CopyOnChangeGroup"):
            groups.append(obj)
    return groups


def _scan_aliases_via_cell_from_alias(spreadsheet: object) -> dict[str, str]:
    aliases: dict[str, str] = {}
    for cell, alias in _iter_cell_aliases(spreadsheet):
        resolved = _try_resolve_cell_from_alias(spreadsheet, alias)
        aliases[alias] = resolved if resolved is not None else cell
    return aliases


def _add_sheet_name_from_object(o: object, names: set[str]) -> bool:
    if getattr(o, "TypeId", None) != "Spreadsheet::Sheet":
        return False
    name = _get_object_name(o)
    if name is not None:
        names.add(name)
    return True


def _iter_object_children(o: object) -> Iterator[object]:
    group = getattr(o, "Group", None)
    if group:
        for child in group:
            yield child
    out_list = getattr(o, "OutList", None)
    if out_list:
        for child in out_list:
            yield child


def _visit_copy_on_change(o: object, *, seen: set[int], names: set[str]) -> None:
    oid = id(o)
    if oid in seen:
        return
    seen.add(oid)
    if _add_sheet_name_from_object(o, names):
        return
    for child in _iter_object_children(o):
        _visit_copy_on_change(child, seen=seen, names=names)


def _get_copy_on_change_spreadsheet_names(doc: "App.Document") -> set[str]:
    seen: set[int] = set()
    names: set[str] = set()
    for group in _get_copy_on_change_groups(doc):
        _visit_copy_on_change(group, seen=seen, names=names)
    return names


def _should_exclude_spreadsheet(
    *,
    exclude_copy_on_change: bool,
    name: str,
    excluded: set[str],
) -> bool:
    return bool(exclude_copy_on_change and name in excluded)


def _iter_sheet_objects(doc: object) -> Iterator[object]:
    for obj in _iter_doc_objects(doc):
        if getattr(obj, "TypeId", None) == "Spreadsheet::Sheet":
            yield obj


def _iter_sheet_names(doc: object) -> Iterator[str]:
    for obj in _iter_sheet_objects(doc):
        name = _get_object_name(obj)
        if name is not None:
            yield name


def _iter_filtered_sheet_names(
    *,
    doc: object,
    excluded: set[str],
    exclude_copy_on_change: bool,
) -> Iterator[str]:
    for name in _iter_sheet_names(doc):
        if _should_exclude_spreadsheet(
            exclude_copy_on_change=exclude_copy_on_change,
            name=name,
            excluded=excluded,
        ):
            continue
        yield name


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

    excluded: set[str] = (
        _get_copy_on_change_spreadsheet_names(doc) if exclude_copy_on_change else set()
    )
    yield from _iter_filtered_sheet_names(
        doc=doc,
        excluded=excluded,
        exclude_copy_on_change=exclude_copy_on_change,
    )


def _alias_map_from_getAliases(spreadsheet: object) -> dict[str, str]:
    getter = getattr(spreadsheet, "getAliases", None)
    if not callable(getter):
        return {}
    raw = _coerce_mapping(getter())
    return _normalize_alias_map(raw)


def _alias_map_from_properties(spreadsheet: object) -> dict[str, str]:
    for prop_name in ("Alias", "Aliases"):
        raw = _coerce_mapping(getattr(spreadsheet, prop_name, None))
        normalized = _normalize_alias_map(raw)
        if normalized:
            return normalized
    return {}


def _get_alias_map(spreadsheet: object) -> dict[str, str]:
    aliases = _alias_map_from_getAliases(spreadsheet)
    if aliases:
        return aliases
    aliases = _alias_map_from_properties(spreadsheet)
    if aliases:
        return aliases

    aliases = _scan_aliases_via_cell_from_alias(spreadsheet)
    if aliases:
        return aliases
    return _scan_aliases_via_getAlias(spreadsheet)


def _try_get_cells_via_attr(spreadsheet: object, *, attr: str) -> list[str] | None:
    getter = getattr(spreadsheet, attr, None)
    if not callable(getter):
        return None
    try:
        cells = getter()
    except Exception:  # pylint: disable=broad-exception-caught
        return None
    return _coerce_cells(cells)


def _coerce_cells(cells: object) -> list[str] | None:
    if not cells:
        return None
    if not isinstance(cells, Iterable):
        return None
    return [str(cell) for cell in cells if cell]


def _get_candidate_cells_from_api(spreadsheet: object) -> list[str] | None:
    for attr in ("getUsedCells", "getNonEmptyCells", "getCells"):
        cells = _try_get_cells_via_attr(spreadsheet, attr=attr)
        if cells is not None:
            return cells
    return None


def _iter_candidate_cells(spreadsheet: object) -> Iterator[str]:
    cells = _get_candidate_cells_from_api(spreadsheet)
    if cells is not None:
        yield from cells
        return
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

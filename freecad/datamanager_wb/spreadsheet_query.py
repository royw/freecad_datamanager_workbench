"""Query helpers for spreadsheet aliases.

Provides discovery of spreadsheet objects, enumeration of alias names, and
searching expressions for alias references.
"""

import re
from collections.abc import Iterable, Iterator, Mapping

from .freecad_context import FreeCadContext, get_runtime_context
from .freecad_helpers import (
    build_expression_key,
    get_copy_on_change_names,
    get_object_name,
    iter_document_objects,
    iter_named_expression_engine_entries,
)
from .freecad_port import FreeCadContextAdapter

_CELL_RE = re.compile(r"^[A-Z]+[0-9]+$")


def _get_active_doc(*, ctx: FreeCadContext | None = None) -> object | None:
    if ctx is None:
        ctx = get_runtime_context()
    port = FreeCadContextAdapter(ctx)
    return port.get_active_document()


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
    sheet_name = get_object_name(sheet)
    if sheet_name is None:
        return
    for cell, text in _iter_alias_referenced_cells(sheet, alias_re=alias_re):
        results[f"{sheet_name}.{cell}"] = text


def _iter_cell_aliases(spreadsheet: object) -> Iterator[tuple[str, str]]:
    getter_one = getattr(spreadsheet, "getAlias", None)
    if not callable(getter_one):
        return
    for cell in _iter_candidate_cells(spreadsheet):
        alias = _try_get_alias(getter_one, cell)
        if alias is not None:
            yield str(cell), alias


def _try_get_alias(getter_one: object, cell: str) -> str | None:
    if not callable(getter_one):
        return None
    try:
        alias = getter_one(cell)
    except Exception:  # pylint: disable=broad-exception-caught
        return None
    if not alias:
        return None
    return str(alias)


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


def _get_active_spreadsheet(
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
    for obj_name, lhs, expr_text in iter_named_expression_engine_entries(doc):
        key = build_expression_key(obj_name=obj_name, lhs=lhs)
        if _matches_expression(expr_text=expr_text, patterns=patterns, alias_re=alias_re):
            results[key] = str(expr_text)
    return results


def _scan_aliases_via_getAlias(spreadsheet: object) -> dict[str, str]:
    aliases: dict[str, str] = {}
    for cell, alias in _iter_cell_aliases(spreadsheet):
        aliases[alias] = cell
    return aliases


def _scan_aliases_via_cell_from_alias(spreadsheet: object) -> dict[str, str]:
    aliases: dict[str, str] = {}
    for cell, alias in _iter_cell_aliases(spreadsheet):
        resolved = _try_resolve_cell_from_alias(spreadsheet, alias)
        aliases[alias] = resolved if resolved is not None else cell
    return aliases


def _get_alias_map(spreadsheet: object) -> dict[str, str]:
    for getter in (
        _alias_map_from_getAliases,
        _alias_map_from_properties,
        _scan_aliases_via_cell_from_alias,
        _scan_aliases_via_getAlias,
    ):
        aliases = getter(spreadsheet)
        if aliases:
            return aliases
    return {}


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


def _get_copy_on_change_spreadsheet_names(doc: object) -> set[str]:
    return get_copy_on_change_names(doc=doc, type_id="Spreadsheet::Sheet")


def _iter_sheet_objects(doc: object) -> Iterator[object]:
    for obj in iter_document_objects(doc):
        if getattr(obj, "TypeId", None) == "Spreadsheet::Sheet":
            yield obj


def _iter_sheet_names(doc: object) -> Iterator[str]:
    for obj in _iter_sheet_objects(doc):
        name = get_object_name(obj)
        if name is not None:
            yield name


def _iter_filtered_sheet_names(
    *,
    doc: object,
    excluded: set[str],
    exclude_copy_on_change: bool,
) -> Iterator[str]:
    for name in _iter_sheet_names(doc):
        if exclude_copy_on_change and name in excluded:
            continue
        yield name


def getSpreadsheets(
    *,
    exclude_copy_on_change: bool = False,
    ctx: FreeCadContext | None = None,
) -> Iterator[str]:
    """Yield spreadsheet object names from the active document.

    Args:
        exclude_copy_on_change: When true, filters out spreadsheets that are
            created by FreeCAD's copy-on-change mechanism.

    Yields:
        The `Name` of each `Spreadsheet::Sheet` object.
    """
    doc = _get_active_doc(ctx=ctx)
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


def getSpreadsheetAliasNames(
    spreadsheet_name: str,
    *,
    ctx: FreeCadContext | None = None,
) -> list[str]:
    """Return all alias names defined on a spreadsheet.

    Args:
        spreadsheet_name: Name of a `Spreadsheet::Sheet`.

    Returns:
        Sorted list of alias names.
    """
    if ctx is None:
        ctx = get_runtime_context()
    port = FreeCadContextAdapter(ctx)
    doc = port.get_active_document()
    if doc is None:
        return []

    sheet = port.get_typed_object(doc, spreadsheet_name, type_id="Spreadsheet::Sheet")
    if sheet is None:
        return []

    names = sorted(_get_alias_map(sheet).keys())
    return names


def getSpreadsheetAliasReferences(
    spreadsheet_name: str,
    alias_name: str | None = None,
    *,
    ctx: FreeCadContext | None = None,
) -> dict[str, str]:
    """Find expressions that reference a spreadsheet or a specific alias.

    Args:
        spreadsheet_name: Name of the spreadsheet.
        alias_name: Optional alias name. When provided, searches for references
            to that alias; otherwise searches for references to the spreadsheet.

    Returns:
        Mapping of ``"Object.Property"`` -> expression string.
    """
    doc = _get_active_doc(ctx=ctx)
    if doc is None:
        return {}

    sheet = _get_active_spreadsheet(spreadsheet_name, ctx=ctx)
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

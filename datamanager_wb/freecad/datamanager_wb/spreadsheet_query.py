from typing import Iterator
import re

import FreeCAD as App

translate = App.Qt.translate


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
    def coerce_map(value: object) -> dict[str, str]:
        if value is None:
            return {}
        if isinstance(value, dict):
            return {str(k): str(v) for k, v in value.items()}
        items = getattr(value, "items", None)
        if callable(items):
            try:
                return {str(k): str(v) for k, v in items()}
            except Exception:  # pylint: disable=broad-exception-caught
                return {}
        try:
            return {str(k): str(v) for k, v in dict(value).items()}  # type: ignore[arg-type]
        except Exception:  # pylint: disable=broad-exception-caught
            return {}

    def normalize_alias_map(raw: dict[str, str]) -> dict[str, str]:
        if not raw:
            return {}
        cell_re = re.compile(r"^[A-Z]+[0-9]+$")
        key_cells = sum(1 for k in raw.keys() if cell_re.match(k or ""))
        val_cells = sum(1 for v in raw.values() if cell_re.match(v or ""))

        # Normalize to alias->cell.
        # Some FreeCAD versions/APIs return cell->alias.
        if key_cells > val_cells:
            return {alias: cell for cell, alias in raw.items()}
        return raw

    getter = getattr(spreadsheet, "getAliases", None)
    if callable(getter):
        raw = coerce_map(getter())
        normalized = normalize_alias_map(raw)
        if normalized:
            return normalized

    # Property name differs across versions: try Alias then Aliases.
    for prop_name in ("Alias", "Aliases"):
        raw = coerce_map(getattr(spreadsheet, prop_name, None))
        normalized = normalize_alias_map(raw)
        if normalized:
            return normalized

    # Fallback for FreeCAD versions that only provide getAlias(cell) (no getAliases())
    getter_one = getattr(spreadsheet, "getAlias", None)
    if callable(getter_one):
        cell_from_alias = getattr(spreadsheet, "getCellFromAlias", None)
        if callable(cell_from_alias):
            # If the API supports alias->cell directly, prefer it. We still need the alias names,
            # so we discover aliases by scanning cells.
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
            if aliases:
                return aliases

        aliases = {}
        for cell in _iter_candidate_cells(spreadsheet):
            try:
                alias = getter_one(cell)
            except Exception:  # pylint: disable=broad-exception-caught
                continue
            if alias:
                aliases[str(alias)] = str(cell)
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
    cols = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    max_rows = 200
    max_cols = 52
    for col_idx in range(max_cols):
        a = cols[col_idx % 26]
        prefix = a if col_idx < 26 else f"{cols[(col_idx // 26) - 1]}{a}"
        for row in range(1, max_rows + 1):
            yield f"{prefix}{row}"


def getSpreadsheetAliasNames(spreadsheet_name: str) -> list[str]:
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
    doc = App.ActiveDocument
    if doc is None:
        return {}

    sheet = doc.getObject(spreadsheet_name)
    if sheet is None or getattr(sheet, "TypeId", None) != "Spreadsheet::Sheet":
        return {}

    label_or_name = getattr(sheet, "Label", None) or getattr(sheet, "Name", "")

    patterns: list[str] = [f"<<{label_or_name}>>"]
    if alias_name:
        patterns = [
            f"<<{label_or_name}>>.{alias_name}",
            f"{label_or_name}.{alias_name}",
            f"{alias_name}",
        ]

    results: dict[str, str] = {}
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

            if alias_name:
                tokens = str(expr_text).split()
                if any(
                    token.endswith(patterns[0])
                    or token.endswith(patterns[1])
                    or token.startswith(patterns[2])
                    for token in tokens
                ):
                    results[f"{obj.Name}.{lhs}"] = expr_text
            else:
                if any(p in str(expr_text) for p in patterns):
                    results[f"{obj.Name}.{lhs}"] = expr_text

    return results

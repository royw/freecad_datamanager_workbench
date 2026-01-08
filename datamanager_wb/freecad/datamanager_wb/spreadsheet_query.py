from typing import Iterator

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
    getter = getattr(spreadsheet, "getAliases", None)
    if callable(getter):
        aliases = getter()
        if isinstance(aliases, dict):
            return {str(k): str(v) for k, v in aliases.items()}

    alias_prop = getattr(spreadsheet, "Alias", None)
    if isinstance(alias_prop, dict):
        return {str(k): str(v) for k, v in alias_prop.items()}

    return {}


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

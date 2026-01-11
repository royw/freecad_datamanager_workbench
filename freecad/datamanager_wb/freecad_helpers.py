from __future__ import annotations

from collections.abc import Iterable, Iterator, Sequence
from typing import cast

import FreeCAD as App


def iter_document_objects(doc: object) -> Iterator[object]:
    for obj in getattr(doc, "Objects", []) or []:
        if obj is not None:
            yield obj


def get_active_document() -> object | None:
    doc = App.ActiveDocument
    if doc is None:
        return None
    return cast(object, doc)


def get_object_name(obj: object) -> str | None:
    name = getattr(obj, "Name", None)
    if isinstance(name, str) and name:
        return name
    return None


def get_typed_object(doc: object, name: str, *, type_id: str) -> object | None:
    getter = getattr(doc, "getObject", None)
    if not callable(getter):
        return None
    obj = getter(name)
    if obj is None or getattr(obj, "TypeId", None) != type_id:
        return None
    return cast(object, obj)


def build_expression_key(*, obj_name: str, lhs: object) -> str:
    if str(lhs).startswith("."):
        return f"{obj_name}{lhs}"
    return f"{obj_name}.{lhs}"


def iter_expression_engine_entries(doc: object) -> Iterator[tuple[object, object, object]]:
    for obj in iter_document_objects(doc):
        expressions = getattr(obj, "ExpressionEngine", None)
        if not expressions or not isinstance(expressions, Iterable):
            continue
        for expr in expressions:
            if not isinstance(expr, Sequence) or len(expr) < 2:
                continue
            try:
                lhs = expr[0]
                expr_text = expr[1]
            except Exception:  # pylint: disable=broad-exception-caught
                continue
            yield obj, lhs, expr_text


def iter_named_expression_engine_entries(doc: object) -> Iterator[tuple[str, object, object]]:
    for obj, lhs, expr_text in iter_expression_engine_entries(doc):
        obj_name = get_object_name(obj)
        if obj_name is None:
            continue
        yield obj_name, lhs, expr_text


def get_copy_on_change_groups(doc: object) -> list[object]:
    groups: list[object] = []
    getter = getattr(doc, "getObject", None)
    if callable(getter):
        direct = getter("CopyOnChangeGroup")
        if direct is not None:
            groups.append(direct)

    for obj in getattr(doc, "Objects", []) or []:
        label = getattr(obj, "Label", None)
        if isinstance(label, str) and label.startswith("CopyOnChangeGroup"):
            groups.append(obj)
    return groups


def iter_object_children(obj: object) -> Iterator[object]:
    group = getattr(obj, "Group", None)
    if group:
        for child in group:
            if child is not None:
                yield child

    out_list = getattr(obj, "OutList", None)
    if out_list:
        for child in out_list:
            if child is not None:
                yield child


def get_copy_on_change_names(*, doc: object, type_id: str) -> set[str]:
    seen: set[int] = set()
    names: set[str] = set()

    def visit(o: object) -> None:
        oid = id(o)
        if oid in seen:
            return
        seen.add(oid)

        if getattr(o, "TypeId", None) == type_id:
            name = get_object_name(o)
            if name is not None:
                names.add(name)
            return

        for child in iter_object_children(o):
            visit(child)

    for group in get_copy_on_change_groups(doc):
        visit(group)

    return names

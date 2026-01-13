from __future__ import annotations

from collections.abc import Iterable, Iterator, Sequence
from typing import cast

from .freecad_context import FreeCadContext, get_runtime_context


def iter_document_objects(doc: object) -> Iterator[object]:
    for obj in getattr(doc, "Objects", []) or []:
        if obj is not None:
            yield obj


def get_active_document(*, ctx: FreeCadContext | None = None) -> object | None:
    if ctx is None:
        ctx = get_runtime_context()
    _ = ctx.gui
    doc = ctx.app.ActiveDocument
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


def iter_expression_engine_entries(doc: object) -> Iterator[tuple[object, object, object]]:
    for obj in iter_document_objects(doc):
        for expr in _iter_expression_engine(obj):
            parsed = _try_parse_expression(expr)
            if parsed is None:
                continue
            lhs, expr_text = parsed
            yield obj, lhs, expr_text


def iter_named_expression_engine_entries(doc: object) -> Iterator[tuple[str, object, object]]:
    for obj, lhs, expr_text in iter_expression_engine_entries(doc):
        obj_name = get_object_name(obj)
        if obj_name is None:
            continue
        yield obj_name, lhs, expr_text


def _get_direct_copy_on_change_group(doc: object) -> object | None:
    getter = getattr(doc, "getObject", None)
    if not callable(getter):
        return None
    group = getter("CopyOnChangeGroup")
    if group is None:
        return None
    return cast(object, group)


def _iter_copy_on_change_named_groups(doc: object) -> Iterator[object]:
    for obj in getattr(doc, "Objects", []) or []:
        label = getattr(obj, "Label", None)
        if isinstance(label, str) and label.startswith("CopyOnChangeGroup"):
            yield cast(object, obj)


def get_copy_on_change_groups(doc: object) -> list[object]:
    groups: list[object] = []
    direct = _get_direct_copy_on_change_group(doc)
    if direct is not None:
        groups.append(direct)
    groups.extend(_iter_copy_on_change_named_groups(doc))
    return groups


def _iter_non_null(values: object) -> Iterator[object]:
    if not values:
        return
    if not isinstance(values, Iterable):
        return
    for item in values:
        if item is not None:
            yield cast(object, item)


def _iter_children_from_attr(obj: object, attr: str) -> Iterator[object]:
    yield from _iter_non_null(getattr(obj, attr, None))


def iter_object_children(obj: object) -> Iterator[object]:
    yield from _iter_children_from_attr(obj, "Group")
    yield from _iter_children_from_attr(obj, "OutList")


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

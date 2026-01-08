from .parent_child_ref import parse_parent_child_ref


def parse_varset_variable_item(text: str) -> tuple[str, str] | None:
    ref = parse_parent_child_ref(text)
    if ref is None:
        return None
    return ref.parent, ref.child


def parse_expression_item_object_name(text: str) -> str | None:
    left = text.split("=", 1)[0].strip()
    ref = parse_parent_child_ref(left)
    if ref is None:
        return None
    return ref.parent

"""VarSet-backed `TabDataSource` for the VarSets tab.

Adapts varset document-model operations to the generic `TabController`.
"""

from .expression_item import ExpressionItem
from .parent_child_ref import ParentChildRef, normalize_parent_child_items
from .parsing_helpers import parse_varset_variable_item
from .tab_datasource import RemoveUnusedResult, TabDataSource
from .varset_mutations import removeVarsetVariable
from .varset_query import (
    getVarsetReferences,
    getVarsets,
    getVarsetVariableGroups,
    getVarsetVariableNames,
    getVarsetVariableNamesForGroup,
)


class VarsetDataSource(TabDataSource):
    """Adapter that exposes VarSets through the `TabDataSource` protocol.

    This class maps generic tab operations (parents, children, expression
    queries, remove-unused) onto the VarSet-specific document model.
    """

    def get_sorted_parents(self, *, exclude_copy_on_change: bool = False) -> list[str]:
        """Return sorted VarSet names.

        If a VarSet contains variables in more than one group, also include
        virtual VarSet entries of the form "{varset}.{group}".
        """

        parents: list[str] = []
        for varset_name in sorted(getVarsets(exclude_copy_on_change=exclude_copy_on_change)):
            parents.append(varset_name)

            groups = set(getVarsetVariableGroups(varset_name).values())
            if len(groups) <= 1:
                continue
            for group in sorted(groups):
                parents.append(f"{varset_name}.{group}")
        return parents

    def _get_varset_groups(self, varset_name: str) -> set[str]:
        return set(getVarsetVariableGroups(varset_name).values())

    def _split_virtual_parent(self, text: str) -> tuple[str, str] | None:
        if "." not in text:
            return None
        varset_name, group = text.split(".", 1)
        if not varset_name or not group:
            return None
        return varset_name, group

    def _parse_virtual_varset(self, text: str) -> tuple[str, str] | None:
        parsed = self._split_virtual_parent(text)
        if parsed is None:
            return None
        varset_name, group = parsed

        groups = self._get_varset_groups(varset_name)
        if len(groups) <= 1 or group not in groups:
            return None
        return parsed

    def _get_var_names_for_parent(self, parent: str) -> tuple[str, list[str]]:
        parsed_virtual = self._parse_virtual_varset(parent)
        if parsed_virtual is None:
            return parent, getVarsetVariableNames(parent)
        varset_name, group = parsed_virtual
        return varset_name, getVarsetVariableNamesForGroup(varset_name, group)

    def get_child_refs(self, selected_parents: list[str]) -> list[ParentChildRef]:
        """Return variable refs for the selected VarSets."""
        variable_items: list[str] = []
        for parent in selected_parents:
            varset_name, var_names = self._get_var_names_for_parent(parent)

            for var_name in var_names:
                variable_items.append(f"{varset_name}.{var_name}")

        variable_items.sort()
        refs: list[ParentChildRef] = []
        for text in variable_items:
            parsed = parse_varset_variable_item(text)
            if parsed is None:
                continue
            parent, child = parsed
            refs.append(ParentChildRef(parent=parent, child=child))
        return refs

    def get_expression_items(
        self, selected_children: list[ParentChildRef] | list[str]
    ) -> tuple[list[ExpressionItem], dict[str, int]]:
        """Return expression items referencing the selected variables."""
        expression_items: list[ExpressionItem] = []
        counts: dict[str, int] = {}

        for text in normalize_parent_child_items(selected_children):
            parsed = parse_varset_variable_item(text)
            if parsed is None:
                continue
            varset_name, variable_name = parsed
            refs = getVarsetReferences(varset_name, variable_name)
            counts[text] = len(refs)
            for k, v in refs.items():
                object_name = k.split(".", 1)[0].strip()
                expression_items.append(ExpressionItem(object_name=object_name, lhs=k, rhs=v))

        expression_items.sort(key=lambda item: item.display_text)
        return expression_items, counts

    def get_expression_reference_counts(
        self, selected_children: list[ParentChildRef] | list[str]
    ) -> dict[str, int]:
        """Return expression reference counts for the selected variables."""
        counts: dict[str, int] = {}

        for text in normalize_parent_child_items(selected_children):
            parsed = parse_varset_variable_item(text)
            if parsed is None:
                continue
            varset_name, variable_name = parsed
            refs = getVarsetReferences(varset_name, variable_name)
            counts[text] = len(refs)

        return counts

    def remove_unused_children(
        self, selected_children: list[ParentChildRef] | list[str]
    ) -> RemoveUnusedResult:
        """Remove variables that have no expression references."""
        removed: list[str] = []
        still_used: list[str] = []
        failed: list[str] = []

        for text in normalize_parent_child_items(selected_children):
            parsed = parse_varset_variable_item(text)
            if parsed is None:
                failed.append(text)
                continue
            varset_name, variable_name = parsed
            refs = getVarsetReferences(varset_name, variable_name)
            if refs:
                still_used.append(text)
                continue
            ok = removeVarsetVariable(varset_name, variable_name)
            if ok:
                removed.append(text)
            else:
                failed.append(text)

        return RemoveUnusedResult(removed=removed, still_used=still_used, failed=failed)

# Test Documentation

> **Auto-generated** on 2026-01-15 10:37:26
> **Total Tests**: 36

This page provides a comprehensive overview of all tests in the project, automatically extracted from test docstrings.

## Unit Tests

| Test Class | Test Name | Description |
|------------|-----------|-------------|
| (module) | `test_build_alias_search_regex_respects_word_boundaries` | Alias matching treats alias tokens as word-boundary matches to avoid false positives. |
| (module) | `test_format_object_name_label_mode_falls_back_to_name` | format_object_name falls back to the original name when no label is available. |
| (module) | `test_format_object_name_label_mode_handles_dotted_names` | format_object_name preserves the property suffix when formatting dotted names. |
| (module) | `test_format_object_name_label_mode_uses_label` | format_object_name uses object labels when label mode is enabled. |
| (module) | `test_get_active_document_change_plan_clears_and_repopulates` | get_active_document_change_plan requests clearing and repopulating all UI lists. |
| (module) | `test_get_alias_expressions_state_formats_expression_with_label` | get_alias_expressions_state formats alias expression items using labels when enabled. |
| (module) | `test_get_aliases_state_formats_parent_child_with_label` | get_aliases_state formats alias parent.child refs using labels when enabled. |
| (module) | `test_get_child_refs_for_non_virtual_parent_includes_all` | VarsetDataSource.get_child_refs returns all variables for a non-virtual varset parent. |
| (module) | `test_get_child_refs_for_virtual_varset_filters_by_group` | VarsetDataSource.get_child_refs filters variables by virtual varset group selection. |
| (module) | `test_get_child_refs_sorts` | SpreadsheetDataSource.get_child_refs returns sorted alias refs. |
| (module) | `test_get_expression_items_counts_and_operator` | SpreadsheetDataSource.get_expression_items returns reference counts and operators. |
| (module) | `test_get_filtered_child_items_only_unused_filters_by_counts` | TabController filters child items to only-unused items based on reference counts. |
| (module) | `test_get_filtered_parents_plain_substring_becomes_glob` | TabController treats plain filter text as an implicit substring glob. |
| (module) | `test_get_project_version_invalid_shapes` | \_get_project_version returns None for invalid pyproject shapes. |
| (module) | `test_get_project_version_valid` | \_get_project_version returns the version string for a valid pyproject shape. |
| (module) | `test_get_show_plan_with_existing_subwindow_reuses` | get_show_plan reuses an existing MDI subwindow when present. |
| (module) | `test_get_show_plan_with_mdi_creates_subwindow` | get_show_plan creates a new MDI subwindow when MDI is available and none exists. |
| (module) | `test_get_show_plan_without_mdi_shows_standalone` | get_show_plan chooses standalone display when MDI is not available. |
| (module) | `test_get_varset_expressions_state_formats_expression_with_label` | get_varset_expressions_state formats expression items using labels when enabled. |
| (module) | `test_get_varset_variables_state_formats_parent_child_with_label` | get_varset_variables_state formats parent.child refs using labels when enabled. |
| (module) | `test_get_varsets_state_filters_on_label_in_label_mode` | get_varsets_state applies filter against display text when label mode is enabled. |
| (module) | `test_get_varsets_state_formats_display_and_preserves_selection` | get_varsets_state formats items and preserves selected keys. |
| (module) | `test_get_version_falls_back_when_read_fails` | get_version falls back to 0.0.0 when reading pyproject fails. |
| (module) | `test_get_version_returns_value_when_available` | get_version returns the read version when available. |
| (module) | `test_normalize_alias_map_inverts_when_keys_are_cells` | \_normalize_alias_map inverts a cell->alias mapping into alias->cell. |
| (module) | `test_normalize_alias_map_keeps_alias_to_cell_mapping` | \_normalize_alias_map preserves an alias->cell mapping. |
| (module) | `test_normalize_parent_child_items_handles_mixed_types` | normalize_parent_child_items normalizes mixed ParentChildRef and string inputs. |
| (module) | `test_parse_expression_item_object_name_parses_lhs_before_equals` | parse_expression_item_object_name extracts the object name from the LHS of an expression. |
| (module) | `test_parse_parent_child_ref_rejects_missing_or_empty_parts` | parse_parent_child_ref rejects refs with missing or empty parent/child parts. |
| (module) | `test_parse_parent_child_ref_success` | parse_parent_child_ref parses a valid Parent.Child reference. |
| (module) | `test_parse_varset_variable_item_delegates_to_parent_child_parser` | parse_varset_variable_item parses VarSet.Variable and rejects non-dotted input. |
| (module) | `test_remove_unused_and_get_update_returns_post_update_items` | TabController remove-unused returns an updated list consistent with filters. |
| (module) | `test_remove_unused_children` | SpreadsheetDataSource.remove_unused_children removes only aliases with zero references. |
| (module) | `test_should_enable_copy_button_requires_focus_and_selection` | should_enable_copy_button requires list focus and a non-empty selection. |
| (module) | `test_should_enable_remove_unused_delegates_to_controller` | should_enable_remove_unused delegates enablement logic to the controller. |
| (module) | `test_virtual_parent_with_unknown_group_falls_back_to_normal` | Unknown virtual group selection falls back to treating the selection as a normal variable prefix. |

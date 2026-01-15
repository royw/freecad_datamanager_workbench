set(Namespace_SRCS
        freecad/datamanager_wb/__init__.py
        freecad/datamanager_wb/init_gui.py
        freecad/datamanager_wb/entrypoints/__init__.py
        freecad/datamanager_wb/entrypoints/init_gui.py
        freecad/datamanager_wb/entrypoints/commands.py
        freecad/datamanager_wb/entrypoints/workbench.py
        freecad/datamanager_wb/ui/__init__.py
        freecad/datamanager_wb/ui/main_panel.py
        freecad/datamanager_wb/ui/main_panel_presenter.py
        freecad/datamanager_wb/ui/panel_controller.py
        freecad/datamanager_wb/ui/gui_selection.py
        freecad/datamanager_wb/ports/__init__.py
        freecad/datamanager_wb/ports/app_port.py
        freecad/datamanager_wb/ports/freecad_context.py
        freecad/datamanager_wb/ports/freecad_port.py
        freecad/datamanager_wb/ports/gui_port.py
        freecad/datamanager_wb/ports/settings_port.py
        freecad/datamanager_wb/domain/__init__.py
        freecad/datamanager_wb/domain/expression_item.py
        freecad/datamanager_wb/freecad_helpers.py
        freecad/datamanager_wb/freecad_version_check.py
        freecad/datamanager_wb/domain/parent_child_ref.py
        freecad/datamanager_wb/domain/parsing_helpers.py
        freecad/datamanager_wb/resources.py
        freecad/datamanager_wb/spreadsheets/__init__.py
        freecad/datamanager_wb/spreadsheets/spreadsheet_datasource.py
        freecad/datamanager_wb/spreadsheets/spreadsheet_mutations.py
        freecad/datamanager_wb/spreadsheets/spreadsheet_query.py
        freecad/datamanager_wb/domain/tab_controller.py
        freecad/datamanager_wb/domain/tab_datasource.py
        freecad/datamanager_wb/varsets/__init__.py
        freecad/datamanager_wb/varsets/varset_datasource.py
        freecad/datamanager_wb/varsets/varset_mutations.py
        freecad/datamanager_wb/varsets/varset_query.py
        freecad/datamanager_wb/version.py
        freecad/datamanager_wb/resources/icons/datamanager_wb.svg
        freecad/datamanager_wb/resources/icons/Varsets.svg
        freecad/datamanager_wb/resources/icons/Aliases.svg
        freecad/datamanager_wb/resources/ui/main_panel.ui
        freecad/datamanager_wb/resources/translations/README.md
        freecad/datamanager_wb/resources/translations/datamanager_wb_es-ES.ts
        freecad/datamanager_wb/resources/translations/update_translation.sh
)

SOURCE_GROUP("" FILES ${Namespace_SRCS})

ADD_CUSTOM_TARGET(DATAMANAGER_WB ALL
        SOURCES ${Namespace_SRCS}
)

fc_copy_sources(DATAMANAGER_WB "${CMAKE_BINARY_DIR}/Mod/datamanager_wb" ${Namespace_SRCS})

INSTALL(
    FILES
        ${Namespace_SRCS}
    DESTINATION
        Mod/datamanager_wb
)

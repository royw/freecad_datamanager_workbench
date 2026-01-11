set(Namespace_SRCS
        freecad/datamanager_wb/init_gui.py
        freecad/datamanager_wb/__init__.py
        freecad/datamanager_wb/commands.py
        freecad/datamanager_wb/expression_item.py
        freecad/datamanager_wb/freecad_helpers.py
        freecad/datamanager_wb/freecad_version_check.py
        freecad/datamanager_wb/gui_selection.py
        freecad/datamanager_wb/main_panel.py
        freecad/datamanager_wb/panel_controller.py
        freecad/datamanager_wb/parent_child_ref.py
        freecad/datamanager_wb/parsing_helpers.py
        freecad/datamanager_wb/resources.py
        freecad/datamanager_wb/spreadsheet_datasource.py
        freecad/datamanager_wb/spreadsheet_mutations.py
        freecad/datamanager_wb/spreadsheet_query.py
        freecad/datamanager_wb/tab_controller.py
        freecad/datamanager_wb/tab_datasource.py
        freecad/datamanager_wb/varset_datasource.py
        freecad/datamanager_wb/varset_mutations.py
        freecad/datamanager_wb/varset_query.py
        freecad/datamanager_wb/version.py
        freecad/datamanager_wb/workbench.py
        freecad/datamanager_wb/resources/datamanager_wb.svg
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

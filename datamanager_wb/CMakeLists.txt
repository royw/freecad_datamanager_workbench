set(Namespace_SRCS
        freecad/datamanager_wb/init_gui.py
        freecad/datamanager_wb/__init__.py
        freecad/datamanager_wb/my_numpy_function.py
        freecad/datamanager_wb/version.py
        freecad/datamanager_wb/resources/datamanager_wb.svg
        freecad/datamanager_wb/resources/translations/datamanager_wb_es-ES.qm
        freecad/datamanager_wb/resources/translations/datamanager_wb_es-ES.ts
)

SOURCE_GROUP("" FILES ${Namespace_SRCS})

ADD_CUSTOM_TARGET(SEARCHBAR ALL
        SOURCES ${Namespace_SRCS}
)

fc_copy_sources(SEARCHBAR "${CMAKE_BINARY_DIR}/Mod/datamanager_wb" ${Namespace_SRCS})

INSTALL(
    FILES
        ${Namespace_SRCS}
    DESTINATION
        Mod/SearchBar
)

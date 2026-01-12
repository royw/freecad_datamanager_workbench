"""
FreeCAD datamanager workbench
"""

import FreeCAD as App
import FreeCADGui as Gui

from .commands import register_commands
from .freecad_version_check import check_python_and_freecad_version
from .main_panel import get_main_panel
from .resources import TRANSLATIONSPATH
from .workbench import DataManagerWorkbench

translate = App.Qt.translate

# Add translations path
Gui.addLanguagePath(TRANSLATIONSPATH)
Gui.updateLocale()

check_python_and_freecad_version()
register_commands(get_main_panel)
Gui.addWorkbench(DataManagerWorkbench())

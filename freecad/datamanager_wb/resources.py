"""Filesystem paths to packaged workbench resources.
Provides absolute paths for icons, translations, and UI files bundled with the workbench."""

import os

PACKAGE_DIR = os.path.dirname(__file__)

ICONPATH = os.path.join(PACKAGE_DIR, "resources", "icons")
TRANSLATIONSPATH = os.path.join(PACKAGE_DIR, "resources", "translations")
UIPATH = os.path.join(PACKAGE_DIR, "resources", "ui")

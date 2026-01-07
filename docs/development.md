# Development

## Installing the workbench for development (symlink)

FreeCAD discovers user workbenches by scanning your user `Mod/` directory. During development, the simplest workflow is to create a symbolic link from FreeCAD’s `Mod/` directory to this repository’s `datamanager_wb` folder.

FreeCAD generally discovers available workbenches only during startup. After adding or removing a workbench (or updating a symlink), restart FreeCAD to ensure the workbench is detected.

### Find your `Mod/` directory

You can find the user `Mod/` directory in a few ways:

1. **In FreeCAD**
   - Open `Edit` -> `Preferences` -> `General` -> `Macro`.
   - Note the macro path shown there; the user `Mod/` directory is typically adjacent to it.

2. **Common Linux default**
   - FreeCAD stores per-version user data under `~/.local/share/FreeCAD/<version>/`.
   - For example:
     - `~/.local/share/FreeCAD/v1-2/Mod`

3. **Search your home directory**
   - If you’re unsure which version directory is active:
     - `find ~/.local/share/FreeCAD -maxdepth 3 -type d -name Mod`

### Create the symlink

From your FreeCAD user `Mod/` directory:

```sh
cd ~/.local/share/FreeCAD/v1-2/Mod
ln -s {path to project}/datamanager_wb datamanager_wb
```

After creating the symlink, restart FreeCAD. The workbench should appear in the workbench selector.

### Reloading during development (Python console)

For iterative development, you can sometimes reload Python modules from the FreeCAD Python console.

```py
import importlib
import datamanager_wb
importlib.reload(datamanager_wb)
```

Notes:

1. Reloading is useful for pure-Python changes, but it is not a full substitute for restarting FreeCAD.
2. FreeCAD’s workbench discovery and command registration are primarily done at startup; if you add/remove the workbench (e.g. create/remove the `Mod/` symlink), you still need to restart.
3. GUI objects, registered commands, and existing Qt widgets may keep references to old classes/functions; after a reload you may need to close/re-open the panel or restart FreeCAD if you see inconsistent behavior.

## Qt version (FreeCAD)

FreeCAD is transitioning from Qt5 to Qt6, with the 1.1 release planned to make Qt6 the default.

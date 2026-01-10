# DataManager FreeCAD Workbench

Manages FreeCAD VarSets and aliases.

## Status

This project is in **early development**. Expect breaking changes, incomplete features, and rough edges.
Tested on weekly dev release and v1.0.2 of FreeCAD on linux and MacOS. See [Tested On](#tested-on) for details.

## Suggestion FreeCAD Preferences

- Enable: General --> Selection --> Tree Selection Behavior --> Auto expand tree item when the corresponding object is selected in the 3D view.
- Disable: Display --> UI --> Tree View --> Hide internal names

## Installation (from GitHub)

FreeCAD discovers user workbenches by scanning your FreeCAD `Mod/` directory. For development (and for installing
from a cloned repo), the recommended workflow is to clone this repository and then create a link into your `Mod/`
directory pointing at the repository’s `datamanager_wb` folder.

After adding/removing a workbench (or changing the link), **restart FreeCAD**.

### 1) Clone the repository

```sh
git clone git@github.com:royw/freecad_datamanager_workbench.git
```

### 2) Locate your FreeCAD `Mod/` directory

FreeCAD’s per-user data directory is versioned. Typical locations:

#### Linux

- `~/.local/share/FreeCAD/<version>/Mod`
- Example: `~/.local/share/FreeCAD/v1-2/Mod`

#### macOS

- `~/Library/Application Support/FreeCAD/<version>/Mod`

#### Windows

- `%APPDATA%\\FreeCAD\\<version>\\Mod`

#### Find your FreeCAD `Mod/` directory

If you’re unsure, in FreeCAD go to:

- `Edit` -> `Preferences` -> `General` -> `Macro`

The macro directory is typically adjacent to your user `Mod/` directory.
If you find the `Macro/` directory and there is not a `Mod/` directory, create a `Mod/` directory in the same location.

Typically:

```bash
,,,/Freecad/Macro/
,,,/Freecad/Mod/
```

or

```bash
.../FreeCAD/<version>/Macro/
.../FreeCAD/<version>/Mod/
```

### 3) Create the link

Link the repository’s directory into your FreeCAD user `Mod/` directory.

#### Linux (symlink)

```sh
ln -s /path/to/FreeCAD_Workbench_DataManager ~/.local/share/FreeCAD/<version>/Mod/datamanager_wb
```

#### macOS (symlink)

```sh
ln -s /path/to/FreeCAD_Workbench_DataManager "$HOME/Library/Application Support/FreeCAD/<version>/Mod/datamanager_wb"
```

#### Windows (PowerShell junction)

Use a directory junction:

```powershell
New-Item -ItemType Junction -Path "$env:APPDATA\\FreeCAD\\<version>\\Mod\\datamanager_wb" -Target "C:\\path\\to\\FreeCAD_Workbench_DataManager"
```

## Usage

### VarSets tab

- **VarSets list**
  - Select one or more VarSets to populate the Variables list.

- **VarSets filter**
  - Filters VarSets by name using a glob match.
  - If you type no glob characters, the filter is treated as a substring match.

- **Exclude CopyOnChanged varsets**
  - When you create Links to objects referencing a VarSet, FreeCAD may create hidden *copy-on-change* groups (typically `CopyOnChangeGroup*`) and generate copied VarSets (e.g. `VarSet001`).
  - Enabling this option hides those generated copies so the list focuses on the VarSets you created.

- **Variables filter**
  - Filters variables by variable name using a glob match.
  - The match is against the variable name only (not the `VarSetName.` prefix).

- **Only Unused**
  - Shows only variables that have **no** expression references.

- **Remove Selected Unused Variables**
  - Removes the selected unused variables from the VarSet.

- **Expressions list**
  - Shows the expressions that reference each variable.
  - Clicking an expression selects the Object in the Model tree.

## Tested On

```text
OS: Manjaro Linux (KDE/plasma/wayland)
Architecture: x86_64
Version: 1.2.0dev.20260106 (Git shallow) AppImage
Build date: 2026/01/06 15:36:19
Build type: Release
Branch: (HEAD detached at 9b64da8)
Hash: 9b64da827a112d88a025be26316e3d023ff491dc
Python 3.11.14, Qt 6.8.3, Coin 4.0.3, Vtk 9.3.1, boost 1_86, Eigen3 3.4.0, PySide 6.8.3
shiboken 6.8.3, xerces-c 3.3.0, IfcOpenShell 0.8.2, OCC 7.8.1
Locale: English/United States (en_US)
Navigation Style/Orbit Style/Rotation Mode: CAD/Rounded Arcball/Window center
Stylesheet/Theme/QtStyle: FreeCAD.qss/FreeCAD Dark/
Logical DPI/Physical DPI/Pixel Ratio: 96/40.64/1.5
Installed mods: 
  * datamanager_wb
  * OpenTheme 2025.5.20
```

```text
OS: macOS 26.0.1
Architecture: arm64
Version: 1.0.2.39319 (Git) Conda
Build type: Release
Branch: (HEAD detached at 1.0.2)
Hash: 256fc7eff3379911ab5daf88e10182c509aa8052
Python 3.11.13, Qt 5.15.15, Coin 4.0.3, Vtk 9.3.0, OCC 7.8.1
Locale: C/Default (C)
Stylesheet/Theme/QtStyle: FreeCAD Dark.qss/FreeCAD Dark/Fusion
Installed mods: 
  * datamanager_wb
```

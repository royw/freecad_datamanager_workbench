# DataManager FreeCAD Workbench

Manages FreeCAD VarSets and aliases.

## Status

This project is in **early development**. Expect breaking changes, incomplete features, and rough edges.

## Installation (from GitHub)

FreeCAD discovers user workbenches by scanning your user `Mod/` directory. For development (and for installing from a cloned repo), the recommended workflow is to clone this repository and then create a link into your `Mod/` directory pointing at the repository’s `datamanager_wb` folder.

After adding/removing a workbench (or changing the link), **restart FreeCAD**.

### 1) Clone the repository

```sh
git clone https://github.com/<your-org-or-user>/<repo>.git
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

If you’re unsure, in FreeCAD go to:

- `Edit` -> `Preferences` -> `General` -> `Macro`

The macro directory is typically adjacent to your user `Mod/` directory.

### 3) Create the link

Link the repository’s `datamanager_wb` directory into your FreeCAD user `Mod/` directory.

#### Linux (symlink)

```sh
ln -s /path/to/FreeCAD_Workbench_DataManager/datamanager_wb ~/.local/share/FreeCAD/<version>/Mod/datamanager_wb
```

#### macOS (symlink)

```sh
ln -s /path/to/FreeCAD_Workbench_DataManager/datamanager_wb "$HOME/Library/Application Support/FreeCAD/<version>/Mod/datamanager_wb"
```

#### Windows (PowerShell junction)

Use a directory junction:

```powershell
New-Item -ItemType Junction -Path "$env:APPDATA\\FreeCAD\\<version>\\Mod\\datamanager_wb" -Target "C:\\path\\to\\FreeCAD_Workbench_DataManager\\datamanager_wb"
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

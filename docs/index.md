# DataManager Workbench

**DataManager** is a FreeCAD workbench for auditing and cleaning up:

- **VarSets** (`App::VarSet`) and their variables
- **Spreadsheet aliases** (`Spreadsheet::Sheet`) and their alias names

It helps you:

- Filter and browse VarSets/Spreadsheets and their child items.
- Inspect expression references to variables/aliases.
- Identify and remove **unused** variables/aliases.

![DataManager panel annotated](images/datamanager_wb_annotated.png)

*Screenshot: DataManager panel showing both tabs (Varsets and Aliases), with the three-pane layout (parents, children, expressions). Details in the [User Guide](user-guide.md).*

## Documentation index

### User documentation

- [User Guide](user-guide.md)
- [Installation (TBD)](install.md)

### Developer documentation

- [Architecture](architecture.md)
- [Development](development.md)
- [Tests](tests.md)

### API reference

- [datamanager_wb](reference/datamanager_wb/)

from __future__ import annotations

import sys
from pathlib import Path


_repo_root = Path(__file__).resolve().parents[1]
_sys_path_entry = str(_repo_root / "datamanager_wb")
if _sys_path_entry not in sys.path:
    sys.path.insert(0, _sys_path_entry)

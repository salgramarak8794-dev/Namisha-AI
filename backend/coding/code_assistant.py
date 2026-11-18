import os
import re
from pathlib import Path
from typing import Dict, Any, List, Optional

class CodeAssistant:
    def __init__(self, workspace_path: Optional[str] = None):
        self.workspace_path = Path(workspace_path) if workspace_path else None

    def set_workspace(self, path: str):
        self.workspace_path = Path(path)

    def scan_project_structure(self, max_depth: int = 2) -> Dict[str, Any]:
        if not self.workspace_path or not self.workspace_path.exists():
            return {"error": "Workspace not set or does not exist"}

        structure = {}
        for root, dirs, files in os.walk(self.workspace_path):
            # Skip hidden and cache folders
            dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("node_modules", "__pycache__", "venv", ".venv")]
            rel_path = os.path.relpath(root, self.workspace_path)
            depth = 0 if rel_path == "." else rel_path.count(os.sep) + 1
            if depth > max_depth:
                continue
            structure[rel_path] = [f for f in files if not f.startswith(".")]
        return structure

    def read_file_safe(self, rel_path: str) -> Optional[str]:
        if not self.workspace_path:
            return None
        target = (self.workspace_path / rel_path).resolve()
        # Security boundary check: ensure target stays inside workspace
        if not str(target).startswith(str(self.workspace_path.resolve())):
            raise PermissionError("Access outside workspace is strictly prohibited.")
        if target.exists() and target.is_file():
            return target.read_text(encoding="utf-8", errors="replace")
        return None

    def explain_traceback(self, traceback_text: str) -> str:
        """Lightweight regex parser for common Python and JS errors."""
        match = re.search(r"(\w+Error|Exception):\s*(.*)", traceback_text)
        if match:
            err_type = match.group(1)
            err_msg = match.group(2)
            return f"Found {err_type}: {err_msg}"
        return "Traceback detected."

# SPDX-License-Identifier: GPL-2.0-only
"""Repository-relative output paths and explicitly configured private evidence."""
import json
import os
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
BUILD = PROJECT / "build"
RESULTS = BUILD / "results"


def local_directory(key):
    """Resolve a saved-file directory; never guess a device or former chat path."""
    config_path = PROJECT / ".local/project-paths.json"
    config = json.loads(config_path.read_text()) if config_path.is_file() else {}
    value = os.environ.get("GAMESIR_" + key.upper(), config.get(key))
    if not isinstance(value, str) or not value:
        raise RuntimeError(f"Configure {key} in .local/project-paths.json or "
                           f"GAMESIR_{key.upper()}; see docs/TESTING.md")
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = PROJECT / path
    path = path.resolve()
    if path == Path("/") or any(path == p or p in path.parents
                                    for p in map(Path, ["/dev", "/proc", "/sys"])):
        raise ValueError("Only stored-file directories are allowed")
    if not path.is_dir():
        raise FileNotFoundError(path)
    return path

#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Hash only explicitly staged/tracked regular project files, never raw folders."""
import hashlib
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def main():
    names = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT).decode().split("\0")
    lines = []
    for name in sorted(n for n in names if n and n != "SHA256SUMS"):
        path = ROOT / name
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"Not a regular project file: {name}")
        with path.open("rb") as source:
            digest = hashlib.file_digest(source, "sha256").hexdigest()
        lines.append(f"{digest}  {name}\n")
    if not lines:
        raise RuntimeError("Review and stage the intended project files first")
    (ROOT / "SHA256SUMS").write_text("".join(lines))
    print(f"SHA256SUMS: {len(lines)} project files")


if __name__ == "__main__":
    main()

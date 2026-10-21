#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""License distribution/annotation checks; ordinary project files only."""
import hashlib
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
UAPI = "include/uapi/gs_native.h"
GPL_HASH = "e6d6a009505e345fe949e1310334fcb0747f28dae2856759de102ab66b722cb4"
EXCEPTION_HASH = "8e378ab93586eb55135d3bc119cce787f7324f48394777d00c34fa3d0be3303f"


def sources():
    """Works in a plain source copy, without .git or any private configuration."""
    found = {ROOT / "Makefile"}
    for folder in ("src", "kernel", "include", "tools", "scripts", "tests", "packaging"):
        for path in (ROOT / folder).rglob("*"):
            if not path.is_file():
                continue
            if (path.suffix in (".c", ".h", ".py", ".sh", ".qml", ".service", ".hook", ".conf") or
                    path.name in ("Kbuild", "PKGBUILD.in", "dkms.conf.in") or
                    path.read_bytes().startswith(b"#!")):
                found.add(path)
    return sorted(found)


class Licensing(unittest.TestCase):
    def test_complete_gpl_and_exception_match_the_reviewed_primary_texts(self):
        # Fixed primary-source hashes prevent passing by copying a truncated
        # license consistently into all of the packaging destinations.
        self.assertEqual(hashlib.sha256((ROOT / "COPYING").read_bytes()).hexdigest(), GPL_HASH)
        self.assertEqual(hashlib.sha256((ROOT / "LICENSES/exceptions/Linux-syscall-note").read_bytes()).hexdigest(),
                         EXCEPTION_HASH)

    def test_all_own_sources_have_one_precise_spdx_at_first_comment_line(self):
        files = sources()
        self.assertGreater(len(files), 100)
        exceptions = []
        for path in files:
            relative = path.relative_to(ROOT).as_posix()
            with self.subTest(source=relative):
                text = path.read_text(encoding="utf-8")
                lines = text.splitlines()
                index = int(lines[0].startswith("#!"))
                expression = "GPL-2.0-only WITH Linux-syscall-note" if relative == UAPI else "GPL-2.0-only"
                expected = (f"// SPDX-License-Identifier: {expression}" if path.suffix in (".c", ".qml") else
                            f"/* SPDX-License-Identifier: {expression} */" if path.suffix == ".h" else
                            f"# SPDX-License-Identifier: {expression}")
                self.assertEqual(lines[index], expected)
                # Ignore examples/strings elsewhere in diagnostic tests.
                actual = re.findall(r"^(?://|/\*|#) SPDX-License-Identifier: ([^\n]+)", text, re.MULTILINE)
                self.assertEqual(len(actual), 1)
                if " WITH " in expression:
                    exceptions.append(relative)
        self.assertEqual(exceptions, [UAPI])

    def test_kernel_module_metadata_stays_a_valid_kernel_tag(self):
        text = (ROOT / "kernel/gs_native_usb.c").read_text()
        self.assertIn('MODULE_LICENSE("GPL");', text)
        self.assertNotIn('MODULE_LICENSE("GPL-2.0-only")', text)


if __name__ == "__main__":
    unittest.main()

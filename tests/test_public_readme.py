#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Check the public entry point without network, GUI, root or device access."""
from pathlib import Path
from html.parser import HTMLParser
import re
import unittest
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
WARNING = """⚠️ **WARNING: EXPERIMENTAL SOFTWARE**

This project is in a **PRE-ALPHA** development stage.

Intended exclusively for experienced Linux users and developers with a solid understanding of kernel modules, system recovery and debugging.

The driver is incomplete, has not undergone comprehensive hardware validation and may cause:

- Kernel crashes, freezes or boot failures
- USB/HID driver conflicts and device malfunctions
- Data loss or system instability
- Unexpected behavior after kernel updates

**DO NOT use on production-critical systems.**

Installation and use are entirely at your own risk.

No stability, compatibility or safety guarantees are provided."""
GOALS = (
    "Our goal is to provide native, community-driven Linux support for GameSir controllers, including advanced features that are often unavailable through generic Xbox-compatible drivers.",
    "The long-term ambition is to develop maintainable, upstream-quality support suitable for consideration in the Linux kernel.",
)
ACKNOWLEDGEMENT_URLS = {
    "https://github.com/broroeror/gamesir-linux-tools",
    "https://github.com/questionablesyntax/g7ctl",
}
PRIVATE_DETAILS = re.compile(
    r"/home/|/Users/|\bmainrig\b|\bwohnzimmer\w*\b|\bdennis\b|deck@",
    re.IGNORECASE,
)


def read_document(relative):
    return (ROOT / relative).read_bytes().decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")


def section(text, heading):
    match = re.search(r"^##[ \t]+" + re.escape(heading) + r"[ \t]*$", text, re.MULTILINE)
    if not match:
        raise AssertionError(f"Missing public README section: {heading}")
    remaining = text[match.end():]
    end = re.search(r"^##[ \t]+", remaining, re.MULTILINE)
    return remaining[:end.start()] if end else remaining


def link_targets(text):
    """Read Markdown links and repository-hosted HTML image/link targets."""
    targets = [match.group(1).strip().strip("<>")
               for match in re.finditer(r"!?\[[^\]\n]*\]\(([^()\n]+)\)", text)]
    class Links(HTMLParser):
        def handle_starttag(self, tag, attributes):
            attribute = 'src' if tag == 'img' else 'href' if tag == 'a' else None
            target = dict(attributes).get(attribute)
            if target:
                targets.append(target)
    Links().feed(text)
    return targets


class PublicReadmeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.readme = read_document("README.md")

    def test_visible_short_warning_and_complete_expandable_warning(self):
        prefix = "# GameSir Native Linux\n\n> ⚠️ **PRE-ALPHA — experimental software.**"
        self.assertTrue(self.readme.startswith(prefix),
                        "The approved short warning must remain visible at the top")
        details = re.search(r'<details>.*?</details>', self.readme, re.DOTALL)
        self.assertIsNotNone(details, "Retain the complete expandable warning")
        self.assertIn(WARNING, details.group())

    def test_warning_preserves_risks_and_emphasis(self):
        warning = self.readme.split("## Project Goals", 1)[0]
        for required in (
            "⚠️ **WARNING: EXPERIMENTAL SOFTWARE**",
            "**PRE-ALPHA**",
            "- Kernel crashes, freezes or boot failures",
            "- USB/HID driver conflicts and device malfunctions",
            "- Data loss or system instability",
            "- Unexpected behavior after kernel updates",
            "**DO NOT use on production-critical systems.**",
        ):
            with self.subTest(required=required):
                self.assertIn(required, warning)

    def test_project_goals_retain_both_user_sentences(self):
        goals = " ".join(section(self.readme, "Project Goals").split())
        for sentence in GOALS:
            with self.subTest(sentence=sentence):
                self.assertIn(sentence, goals)

    def test_acknowledgements_link_original_projects_as_references(self):
        acknowledgement = section(self.readme, "Acknowledgements / Special Thanks")
        urls = {target.rstrip("/") for target in link_targets(acknowledgement)}
        self.assertTrue(ACKNOWLEDGEMENT_URLS <= urls,
                        "Acknowledgements must link the original Deadband and g7ctl repositories")
        normalized = " ".join(acknowledgement.lower().split())
        self.assertRegex(normalized, r"\breferenc(?:e|es)\b")
        self.assertIn("independent projects", normalized)

    def test_license_and_uapi_exception_are_linked(self):
        self.assertIn("GPL-2.0-only", self.readme)
        targets = {unquote(urlsplit(target).path) for target in link_targets(self.readme)}
        for required in ("COPYING", "docs/LICENSING.md", "LICENSES/exceptions/Linux-syscall-note"):
            with self.subTest(required=required):
                self.assertIn(required, targets)

    def test_readme_local_links_resolve_inside_the_repository(self):
        for target in link_targets(self.readme):
            parsed = urlsplit(target)
            if parsed.scheme or parsed.netloc or not parsed.path:
                continue
            with self.subTest(target=target):
                resolved = (ROOT / unquote(parsed.path)).resolve()
                self.assertTrue(resolved.is_relative_to(ROOT), "Public links must not escape this repository")
                self.assertTrue(resolved.is_file(), "README link points to a missing repository file")

    def test_public_entry_guides_do_not_include_private_machine_details(self):
        for relative in ("README.md", "docs/INSTALLATION.md", "docs/RELEASE_AUDIT.md"):
            with self.subTest(document=relative):
                text = read_document(relative)
                self.assertIsNone(PRIVATE_DETAILS.search(text),
                                  "Public entry guides must use portable paths and omit private machine details")


if __name__ == "__main__":
    unittest.main()

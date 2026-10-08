# -*- coding: utf-8 -*-
import base64
import os
import re
import unittest

from export_shell import (
    EXPORT_SHELL,
    INDEX_HTML,
    inject_dsl_into_html,
    read_export_shell,
)

BASE = os.path.dirname(os.path.abspath(__file__))
DSL_TAG_RE = re.compile(
    r'<script[^>]*id="canvas-initial-dsl"[^>]*>([\s\S]*?)</script>',
    re.I,
)


def read_dsl_from_export_html(html: str) -> str:
    m = DSL_TAG_RE.search(html)
    if not m or not m.group(1).strip():
        return ""
    return base64.b64decode(m.group(1).strip()).decode("utf-8")


class TestExportShell(unittest.TestCase):
    def test_export_shell_exists_and_smaller_than_index(self):
        self.assertTrue(
            EXPORT_SHELL.is_file(),
            "index.export.html がありません。py -3 export_shell.py を実行してください",
        )
        self.assertLess(EXPORT_SHELL.stat().st_size, INDEX_HTML.stat().st_size)

    def test_read_export_shell_uses_minify_file(self):
        html = read_export_shell()
        self.assertIn("AI-Canvas", html)
        self.assertIn("canvas-initial-dsl", html)

    def test_inject_dsl_json_safe_for_backslash_nu(self):
        shell = '<script type="text/plain" id="canvas-initial-dsl" data-encoding="base64"></script>'
        dsl = 'math: m [latex="h\\nu"]'
        out = inject_dsl_into_html(shell, dsl)
        parsed = read_dsl_from_export_html(out)
        self.assertIn(r"h\nu", parsed)
        self.assertNotIn("latex=\"h\n", parsed)

    def test_inject_dsl_with_semicolon_in_content(self):
        shell = INDEX_HTML.read_text(encoding="utf-8")
        dsl = 'text: t [content="a; b; c", to="x"]'
        out = inject_dsl_into_html(shell, dsl)
        embedded = read_dsl_from_export_html(out)
        self.assertIn("a; b; c", embedded)

    def test_quantum_demo_roundtrip_via_export_shell(self):
        demo = (INDEX_HTML.parent / "quantum_demo.txt").read_text(encoding="utf-8")
        out = inject_dsl_into_html(read_export_shell(), demo)
        back = read_dsl_from_export_html(out)
        self.assertEqual(back, demo)

    def test_canvas_app_uses_read_export_shell(self):
        with open(os.path.join(BASE, "canvas_app.py"), encoding="utf-8") as f:
            self.assertIn("read_export_shell", f.read())


if __name__ == "__main__":
    unittest.main()

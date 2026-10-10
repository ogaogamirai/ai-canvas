# -*- coding: utf-8 -*-
"""src/（正本）→ editor.html / index.html（生成物）の検証。"""
import re
import unittest
from pathlib import Path

import export_shell as es

BASE = Path(__file__).resolve().parent
SRC = BASE / "src"
TEMPLATE = SRC / "template.html"
STYLES = SRC / "styles.css"
CANVAS_JS = SRC / "canvas.js"
EDITOR_JS = SRC / "editor.js"
EDITOR = BASE / "editor.html"
INDEX = BASE / "index.html"


class TestEditorBuild(unittest.TestCase):
    def test_sources_exist(self):
        for p in (TEMPLATE, STYLES, SRC / "editor.css", CANVAS_JS, EDITOR_JS):
            self.assertTrue(p.is_file(), p.name)

    def test_template_placeholders_and_markers(self):
        t = TEMPLATE.read_text(encoding="utf-8")
        self.assertIn("{{STYLES}}", t)
        self.assertIn("{{APP_JS}}", t)
        self.assertGreater(t.count("@editor-only:start"), 0)
        self.assertEqual(t.count("@editor-only:start"), t.count("@editor-only:end"))

    def test_editor_js_has_editorapp_canvas_js_not(self):
        self.assertIn("const EditorApp = {", EDITOR_JS.read_text(encoding="utf-8"))
        self.assertNotIn("const EditorApp = {", CANVAS_JS.read_text(encoding="utf-8"))

    def test_strip_removes_editor_html_regions(self):
        stripped = es.strip_editor_regions(TEMPLATE.read_text(encoding="utf-8"))
        self.assertNotIn("@editor-only", stripped)
        self.assertNotIn('id="editor-pane"', stripped)
        self.assertNotIn('id="slash-menu"', stripped)
        self.assertIn("canvas-initial-dsl", stripped)

    def test_generated_editor_and_index(self):
        self.assertTrue(EDITOR.is_file() and INDEX.is_file())
        ed = EDITOR.read_text(encoding="utf-8")
        ix = INDEX.read_text(encoding="utf-8")
        self.assertIn("const EditorApp = {", ed)
        self.assertIn('id="editor-pane"', ed)
        self.assertNotIn("{{APP_JS}}", ed)
        self.assertNotIn("const EditorApp = {", ix)
        self.assertNotIn('id="editor-pane"', ix)
        self.assertIn("const Canvas", ix)
        self.assertIn("canvas-initial-dsl", ix)

    def test_text_component_sets_foreignobject_size(self):
        js = CANVAS_JS.read_text(encoding="utf-8")
        m = re.search(r"registerComponent\('text',\s*\{.*?\n    \}\);", js, re.S)
        self.assertIsNotNone(m, "text component not found")
        self.assertIn("fo.setAttribute('width'", m.group(0))
        self.assertIn("fo.setAttribute('height'", m.group(0))

    def test_connect_drag_preview_not_gated_by_activedrag(self):
        js = CANVAS_JS.read_text(encoding="utf-8")
        self.assertNotIn("if (!activeDrag) return;\n        // 🌟 結線ドラッグ追従", js)

    def test_autolayout_refits_view(self):
        js = CANVAS_JS.read_text(encoding="utf-8")
        m = re.search(r"autoLayout: function.*?\n        \}", js, re.S)
        self.assertIsNotNone(m, "autoLayout not found")
        self.assertIn("this.fitView()", m.group(0))

    def test_editorapp_has_no_duplicate_methods(self):
        js = EDITOR_JS.read_text(encoding="utf-8")
        for name in ("init", "initSplitter", "toggleCollapse"):
            self.assertEqual(len(re.findall(r"\n      %s: function" % name, js)), 1, name)

    def test_editor_action_buttons_are_icon_only(self):
        t = TEMPLATE.read_text(encoding="utf-8")
        m = re.search(r'<div class="editor-actions">(.*?)</div>', t, re.S)
        self.assertIsNotNone(m, "editor-actions not found")
        block = m.group(1)
        for bid in (
            "btn-sync-from-canvas",
            "btn-normalize-dsl",
            "btn-import-dsl",
            "btn-download-dsl",
            "btn-copy-dsl",
            "btn-load-demo",
            "btn-collapse-editor",
        ):
            self.assertIn(bid, block)
        self.assertNotIn('class="btn" id="btn-', block)


if __name__ == "__main__":
    unittest.main()

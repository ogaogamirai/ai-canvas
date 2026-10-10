# -*- coding: utf-8 -*-
"""editor.html（正本）→ index.html（canvas-only 生成物）の検証。"""
import re
import unittest
from pathlib import Path

import export_shell as es

BASE = Path(__file__).resolve().parent
EDITOR = BASE / "editor.html"
INDEX = BASE / "index.html"


class TestEditorBuild(unittest.TestCase):
    def test_editor_is_source_with_balanced_markers(self):
        html = EDITOR.read_text(encoding="utf-8")
        self.assertGreater(html.count("@editor-only:start"), 0)
        self.assertEqual(html.count("@editor-only:start"), html.count("@editor-only:end"))
        self.assertIn("const EditorApp = {", html)
        self.assertIn('id="editor-pane"', html)

    def test_strip_removes_editor_regions(self):
        stripped = es.strip_editor_regions(EDITOR.read_text(encoding="utf-8"))
        self.assertNotIn("@editor-only", stripped)
        self.assertNotIn('id="editor-pane"', stripped)
        self.assertNotIn('id="slash-menu"', stripped)
        self.assertNotIn("const EditorApp = {", stripped)
        self.assertIn("const Canvas", stripped)
        self.assertIn("registerComponent", stripped)
        self.assertIn("canvas-initial-dsl", stripped)

    def test_generated_index_is_canvas_only(self):
        self.assertTrue(INDEX.is_file(), "index.html がありません。build を実行してください")
        html = INDEX.read_text(encoding="utf-8")
        self.assertNotIn('id="editor-pane"', html)
        self.assertNotIn("const EditorApp = {", html)
        self.assertIn("const Canvas", html)
        self.assertIn("canvas-initial-dsl", html)

    def test_text_component_sets_foreignobject_size(self):
        # foreignObject は width/height 未設定だと 0 サイズで描画されない（TEXT 非表示バグの回帰防止）
        html = EDITOR.read_text(encoding="utf-8")
        m = re.search(r"registerComponent\('text',\s*\{.*?\n    \}\);", html, re.S)
        self.assertIsNotNone(m, "text component not found")
        block = m.group(0)
        self.assertIn("fo.setAttribute('width'", block)
        self.assertIn("fo.setAttribute('height'", block)

    def test_connect_drag_preview_not_gated_by_activedrag(self):
        # Shift 結線時は activeDrag が null。pointermove は connectDrag を先に扱う必要がある
        html = EDITOR.read_text(encoding="utf-8")
        self.assertNotIn("if (!activeDrag) return;\n        // 🌟 結線ドラッグ追従", html)

    def test_editor_action_buttons_are_icon_only(self):
        # ヘッダーの操作ボタンはアイコンのみ（.btn-icon）＋ title ポップアップ
        html = EDITOR.read_text(encoding="utf-8")
        m = re.search(r'<div class="editor-actions">(.*?)</div>', html, re.S)
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

    def test_autolayout_refits_view(self):
        # 整列後に fitView しないと、整列で視界外へ出たグラフが非表示になる
        html = EDITOR.read_text(encoding="utf-8")
        m = re.search(r"autoLayout: function.*?\n        \}", html, re.S)
        self.assertIsNotNone(m, "autoLayout not found")
        self.assertIn("this.fitView()", m.group(0))

    def test_editorapp_has_no_duplicate_methods(self):
        html = EDITOR.read_text(encoding="utf-8")
        for name in ("init", "initSplitter", "toggleCollapse"):
            self.assertEqual(
                len(re.findall(r"\n      %s: function" % name, html)), 1, name
            )


if __name__ == "__main__":
    unittest.main()

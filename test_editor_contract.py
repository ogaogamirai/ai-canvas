# -*- coding: utf-8 -*-
"""editor_app.py の JS 契約と webview 非依存 import の検証。"""
import json
import os
import tempfile
import unittest
from unittest import mock

os.environ.setdefault("AI_CANVAS_NO_REVEAL", "1")

import editor_app


class TestEditorAppContract(unittest.TestCase):
    def setUp(self):
        self.api = editor_app.CanvasAPI()

    def test_import_without_webview(self):
        # webview 未導入でも import できる（遅延 import の担保）
        self.assertTrue(hasattr(editor_app, "CanvasAPI"))

    def test_js_contract_methods_exist(self):
        for name in (
            "get_startup_content",
            "get_export_shell",
            "sync_canvas_state",
            "sync_state",
            "save_dsl",
            "open_dsl_file",
            "export_html",
        ):
            self.assertTrue(hasattr(self.api, name), name)

    def test_sync_canvas_state_writes_state(self):
        state = {"schema_version": 1, "objects": [{"id": "a", "type": "card"}], "edges": []}
        with tempfile.TemporaryDirectory() as td:
            original = editor_app.STATE_FILE
            editor_app.STATE_FILE = os.path.join(td, "canvas_state.json")
            try:
                self.assertEqual(self.api.sync_canvas_state("a", "card", 1.0, 2.0, state), "ok")
                with open(editor_app.STATE_FILE, encoding="utf-8") as f:
                    self.assertEqual(json.load(f)["objects"][0]["id"], "a")
            finally:
                editor_app.STATE_FILE = original

    def test_sync_state_accepts_json_string(self):
        state = {"objects": [], "edges": []}
        with tempfile.TemporaryDirectory() as td:
            original = editor_app.STATE_FILE
            editor_app.STATE_FILE = os.path.join(td, "s.json")
            try:
                self.assertEqual(self.api.sync_state(json.dumps(state)), "ok")
            finally:
                editor_app.STATE_FILE = original

    def test_export_marker_routes_to_export_html(self):
        with tempfile.TemporaryDirectory() as td:
            original = editor_app.BASE_DIR
            editor_app.BASE_DIR = td
            try:
                with mock.patch.object(editor_app.os.path, "expanduser", return_value=td):
                    res = self.api.sync_canvas_state(
                        "__EXPORT_HTML__", "system", 0, 0, {"raw_html": "<html></html>"}
                    )
                self.assertTrue(isinstance(res, str) and res.startswith("保存完了"), res)
            finally:
                editor_app.BASE_DIR = original


if __name__ == "__main__":
    unittest.main()

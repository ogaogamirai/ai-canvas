# -*- coding: utf-8 -*-
"""Phase 1: schema_version / edge DSL キーワードのスモーク"""
import os
import re
import unittest

BASE = os.path.dirname(os.path.abspath(__file__))


class TestPhase1(unittest.TestCase):
    def test_index_has_schema_and_edge_helpers(self):
        with open(os.path.join(BASE, "index.html"), encoding="utf-8") as f:
            html = f.read()
        self.assertIn("schema_version", html)
        self.assertIn("CANVAS_SCHEMA_VERSION", html)
        self.assertIn("edgeStyleFromNodeProps", html)
        self.assertIn("normalizeEdgeStyle", html)
        self.assertIn("calcEdgePath", html)
        self.assertIn("assembleExportHtml", html)
        self.assertIn("CanvasTable", html)
        self.assertIn("canvas-data-table", html)
        self.assertIn("get_export_shell", html)
        self.assertNotIn("edge-style.js", html)
        self.assertIn('type === \'edge\'', html)
        self.assertIn("toggleHeaderMenu", html)
        with open(os.path.join(BASE, "canvas_app.py"), encoding="utf-8") as f:
            self.assertIn("get_export_shell", f.read())
        self.assertIn("--header-h", html)

    def test_quantum_demo_optional_edge_attrs(self):
        with open(os.path.join(BASE, "quantum_demo.txt"), encoding="utf-8") as f:
            demo = f.read()
        self.assertIn("edge_color=", demo)
        self.assertIn("edge_width=", demo)
        self.assertIn("edge_dash=", demo)


if __name__ == "__main__":
    unittest.main()

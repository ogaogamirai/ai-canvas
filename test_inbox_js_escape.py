# -*- coding: utf-8 -*-
"""inbox 監視が quantum_demo を壊さず JS に載せられること"""
import json
import os
import unittest

BASE = os.path.dirname(os.path.abspath(__file__))


class TestInboxJsEscape(unittest.TestCase):
    def test_dsl_json_has_no_raw_newlines_from_nu(self):
        path = os.path.join(BASE, "quantum_demo.txt")
        with open(path, encoding="utf-8") as f:
            dsl = f.read()
        self.assertIn(r"h\nu", dsl)
        js = "window.__applyCanvasDslFromHost(" + json.dumps(dsl) + ");"
        # 旧方式: テンプレートリテラル内で \n が実改行になる
        broken = "Canvas.applyDSL(`" + dsl.replace("\\", "\\\\").replace("`", "\\`") + "`);"
        self.assertIn("\n", broken)
        self.assertNotIn("\n", js)
        self.assertIn("__applyCanvasDslFromHost", js)
        self.assertIn("h\\\\nu", js)  # JSON 内は \\nu


if __name__ == "__main__":
    unittest.main()

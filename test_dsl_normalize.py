# -*- coding: utf-8 -*-
import json
import os
import unittest

from dsl_normalize import (
    normalize_dsl_text,
    normalize_latex_for_katex,
    normalize_state,
)

BASE = os.path.dirname(os.path.abspath(__file__))


class TestDslNormalize(unittest.TestCase):
    def test_collapse_times(self):
        self.assertEqual(normalize_latex_for_katex(r"6.626 \\times 10^{-34}"), r"6.626 \times 10^{-34}")

    def test_nu_single(self):
        self.assertEqual(normalize_latex_for_katex(r"h\\nu"), r"h\nu")

    def test_dsl_line(self):
        line = (
            'math: m1 [latex="E_{max} = h\\\\nu - W_0", '
            'detail="**$\\\\nu$**: 定数 ($6.626 \\\\times 10^{-34}$)"]'
        )
        out, n = normalize_dsl_text(line)
        self.assertEqual(n, 1)
        self.assertIn(r"\nu", out)
        self.assertIn(r"\times", out)
        self.assertNotIn(r"\\times", out)

    def test_state_einstein(self):
        with open(os.path.join(BASE, "canvas_state.json"), encoding="utf-8") as f:
            state = json.load(f)
        new_state, n = normalize_state(state)
        self.assertGreaterEqual(n, 0)
        ein = next((o for o in new_state["objects"] if o["id"] == "einstein"), None)
        if ein and ein.get("data", {}).get("detail"):
            detail = ein["data"]["detail"]
            self.assertIn(r"\nu", detail)
            self.assertNotIn(r"\\nu", detail)
        if n > 0:
            self.assertNotEqual(state, new_state)


if __name__ == "__main__":
    unittest.main()

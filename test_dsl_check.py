# -*- coding: utf-8 -*-
"""DSL 検証（dsl_check）と rich 正規化（dsl_normalize）のテスト。"""
import unittest

from dsl_check import check_dsl_text
from dsl_normalize import normalize_dsl_text


class TestDslCheck(unittest.TestCase):
    def test_valid_no_diags(self):
        dsl = (
            'clear\ncard: a [title="A"]\n'
            'math: m [latex="E=mc^2", to="a"]\n\n'
            'edge: e1 [from="a", to="m", color="#10b981", width=2, arrow=double]'
        )
        self.assertEqual(check_dsl_text(dsl), [])

    def test_unknown_type(self):
        d = check_dsl_text('foo: a [title="x"]')
        self.assertTrue(any(x["level"] == "error" and "未知の型" in x["message"] for x in d))

    def test_duplicate_id(self):
        d = check_dsl_text('card: a [title="A"]\ncard: a [title="B"]')
        self.assertTrue(any("重複" in x["message"] for x in d))

    def test_edge_missing_endpoints(self):
        d = check_dsl_text('card: a [title="A"]\nedge: e1 [from="a"]')
        self.assertTrue(any("from / to" in x["message"] for x in d))

    def test_edge_unknown_node(self):
        d = check_dsl_text('card: a [title="A"]\nedge: e1 [from="a", to="zzz"]')
        self.assertTrue(any("to='zzz'" in x["message"] for x in d))

    def test_invalid_color_warns(self):
        d = check_dsl_text('card: a [title="A", color="red"]')
        self.assertTrue(any(x["level"] == "warning" and "color=" in x["message"] for x in d))

    def test_non_numeric_width_warns(self):
        d = check_dsl_text('card: a [title="A"]\ncard: a2 [title="A2"]\nedge: e1 [from="a", to="a2", width=abc]')
        self.assertTrue(any("数値ではない" in x["message"] for x in d))

    def test_unbalanced_bracket(self):
        d = check_dsl_text('card: a [title="A"')
        self.assertTrue(any("括弧" in x["message"] for x in d))

    def test_plain_line_warns(self):
        d = check_dsl_text("ただのメモ")
        self.assertTrue(any(x["level"] == "warning" and "未整形" in x["message"] for x in d))

    def test_arrow_unknown(self):
        d = check_dsl_text('card: a [title="A"]\na -> zzz')
        self.assertTrue(any("zzz" in x["message"] for x in d))


class TestRichNormalize(unittest.TestCase):
    def test_hex_lowercase(self):
        out, _ = normalize_dsl_text('card: a [title="A", color="#ABCDEF"]', rich=True)
        self.assertIn('color="#abcdef"', out)

    def test_dedupe_edges(self):
        dsl = ('card: a [title="A"]\ncard: b [title="B"]\n'
               'edge: e1 [from="a", to="b"]\nedge: e2 [from="a", to="b"]')
        out, _ = normalize_dsl_text(dsl, rich=True)
        self.assertEqual(out.count("edge:"), 1)

    def test_default_unchanged(self):
        out, _ = normalize_dsl_text('card: a [title="A", color="#ABCDEF"]')
        self.assertIn('color="#ABCDEF"', out)


if __name__ == "__main__":
    unittest.main()

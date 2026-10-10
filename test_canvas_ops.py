# -*- coding: utf-8 -*-
"""canvas_ops（D1 state→DSL / D2 diff / D3 merge / D4 query）のテスト。"""
import unittest

from canvas_ops import (
    diff_dsl,
    dsl_from_state,
    find_path,
    merge_dsl,
    neighbors,
    parse_dsl,
    tree_lines,
)

STATE = {
    "schema_version": 1,
    "objects": [
        {"id": "a", "type": "card", "w": 200, "h": 84, "x": 10, "y": 20,
         "data": {"id": "a", "title": "A", "color": "#ABCDEF", "x": 10, "y": 20}},
        {"id": "b", "type": "card", "w": 200, "h": 84, "data": {"id": "b", "title": "B"}},
    ],
    "edges": [
        {"u": "a", "v": "b", "label": "to-b", "style": {"stroke": "#10b981", "width": 2, "dash": "5,4"}},
    ],
}


class TestDslFromState(unittest.TestCase):
    def test_basic(self):
        out = dsl_from_state(STATE)
        self.assertIn("clear", out)
        self.assertIn('card: a [x=10, y=20, title="A", color="#ABCDEF"]', out)
        self.assertIn('card: b [title="B"]', out)  # 座標なし（manualPos でない）
        self.assertIn('edge: e1 [from="a", to="b", label="to-b", color="#10b981", width=2, dash="5,4"]', out)


class TestParseAndDiff(unittest.TestCase):
    def test_parse_inline_to(self):
        s = parse_dsl('card: a [title="A"]\ncard: b [title="B", to="a", link="x"]')
        self.assertIn(("a", "b"), s["edges"])
        self.assertNotIn("to", s["nodes"]["b"]["props"])  # inline はエッジへ正規化

    def test_diff(self):
        a = 'card: a [title="A"]\ncard: b [title="B"]\nedge: e1 [from="a", to="b"]'
        b = 'card: a [title="A2"]\ncard: c [title="C"]\nedge: e1 [from="a", to="c"]'
        kinds = {(k, op, ref) for k, op, ref, _ in diff_dsl(a, b)}
        self.assertIn(("node", "-", "b"), kinds)
        self.assertIn(("node", "+", "c"), kinds)
        self.assertIn(("node", "~", "a"), kinds)
        self.assertIn(("edge", "-", "a -> b"), kinds)
        self.assertIn(("edge", "+", "a -> c"), kinds)


class TestMerge(unittest.TestCase):
    def test_merge_upsert(self):
        base = 'card: a [title="A"]\ncard: b [title="B"]\nedge: e1 [from="a", to="b"]'
        patch = 'card: a [color="#fff"]\ncard: c [title="C"]\nedge: e2 [from="a", to="c", dash="5,4"]'
        out = merge_dsl(base, patch)
        self.assertIn('card: a [title="A", color="#fff"]', out)
        self.assertIn('card: c [title="C"]', out)
        self.assertEqual(out.count("edge:"), 2)


class TestQueries(unittest.TestCase):
    def test_neighbors(self):
        s = parse_dsl('card: a [title="A"]\ncard: b [title="B"]\nedge: e1 [from="a", to="b"]')
        nb = neighbors(s, "a")
        self.assertEqual(nb["outgoing"], ["a -> b"])
        self.assertEqual(nb["incoming"], [])

    def test_path(self):
        s = parse_dsl(
            'card: a [title="A"]\ncard: b [title="B"]\ncard: c [title="C"]\n'
            'edge: e1 [from="a", to="b"]\nedge: e2 [from="b", to="c"]'
        )
        self.assertEqual(find_path(s, "a", "c"), ["a", "b", "c"])
        self.assertIsNone(find_path(s, "c", "a"))  # 有向

    def test_tree(self):
        s = parse_dsl('card: a [title="A"]\ncard: b [title="B"]\nedge: e1 [from="a", to="b"]')
        lines = tree_lines(s)
        self.assertTrue(any("a" in l for l in lines))
        self.assertTrue(any("b" in l for l in lines))


if __name__ == "__main__":
    unittest.main()

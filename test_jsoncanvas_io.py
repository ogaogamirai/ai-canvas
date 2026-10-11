# -*- coding: utf-8 -*-
"""jsoncanvas_io: state ⇄ JSON Canvas の往復と相互運用形状の検証。"""
import json
import unittest

from canvas_ops import dsl_from_state
from jsoncanvas_io import jsoncanvas_to_state, state_to_jsoncanvas


def _sample_state():
    return {
        "schema_version": 1,
        "objects": [
            {"id": "origin", "type": "card", "x": 80, "y": 120, "w": 200, "h": 84,
             "data": {"id": "origin", "title": "光の本質", "sub": "問い", "color": "#c084fc",
                      "detail": "# 転換点\n光は波か粒子か。"}},
            {"id": "einstein", "type": "math", "x": 420, "y": 120, "w": 230, "h": 92,
             "data": {"id": "einstein", "title": "EINSTEIN", "latex": "E_{max} = h\\nu - W_0"}},
            {"id": "tbl", "type": "table", "x": 80, "y": 300, "w": 300, "h": 120,
             "data": {"id": "tbl", "title": "対比", "headers": "対象, 波動性", "rows": "光|干渉; 電子|回折"}},
            {"id": "memo", "type": "sticky", "x": 420, "y": 300, "w": 180, "h": 120,
             "data": {"id": "memo", "title": "TODO", "content": "ド・ブロイ", "color": "#fef08a"}},
            {"id": "grp", "type": "group", "x": 60, "y": 100, "w": 600, "h": 340,
             "data": {"id": "grp", "title": "領域", "color": "#38bdf8", "contains": "origin,einstein"}},
        ],
        "edges": [
            {"u": "origin", "v": "einstein", "label": "定式化",
             "style": {"stroke": "#10b981", "width": 2.5, "dash": "5,4", "arrow": "double"}},
            {"u": "einstein", "v": "memo", "label": "", "style": {}},
        ],
    }


class TestJsonCanvasIO(unittest.TestCase):
    def test_export_shape(self):
        jc = state_to_jsoncanvas(_sample_state())
        self.assertIn("nodes", jc)
        self.assertIn("edges", jc)
        for n in jc["nodes"]:
            self.assertIn(n["type"], ("text", "file", "link", "group"))
            for k in ("id", "x", "y", "width", "height"):
                self.assertIn(k, n)
        for e in jc["edges"]:
            self.assertIn("fromNode", e)
            self.assertIn("toNode", e)
        types = {n["id"]: n["type"] for n in jc["nodes"]}
        self.assertEqual(types["grp"], "group")
        self.assertEqual(types["einstein"], "text")

    def test_round_trip_state_via_json(self):
        s0 = _sample_state()
        jc = json.loads(json.dumps(state_to_jsoncanvas(s0)))  # JSON を通す
        s1 = jsoncanvas_to_state(jc)
        by_id = {o["id"]: o for o in s1["objects"]}
        for o in s0["objects"]:
            r = by_id[o["id"]]
            self.assertEqual(r["type"], o["type"])
            self.assertEqual(r["data"], o["data"])
            self.assertEqual(int(r["x"]), int(o["x"]))
            self.assertEqual(int(r["y"]), int(o["y"]))
        self.assertEqual(len(s1["edges"]), len(s0["edges"]))
        e0 = s0["edges"][0]
        e1 = [e for e in s1["edges"] if e["u"] == e0["u"] and e["v"] == e0["v"]][0]
        self.assertEqual(e1["label"], e0["label"])
        self.assertEqual(e1["style"], e0["style"])

    def test_foreign_jsoncanvas_import(self):
        jc = {
            "nodes": [
                {"id": "a", "type": "text", "x": 0, "y": 0, "width": 200, "height": 80,
                 "text": "# 見出し\n本文テキスト"},
                {"id": "g", "type": "group", "x": -20, "y": -20, "width": 300, "height": 200,
                 "label": "クラスタ"},
                {"id": "l", "type": "link", "x": 0, "y": 200, "width": 200, "height": 80,
                 "url": "https://example.com"},
                {"id": "c", "type": "text", "x": 0, "y": 100, "width": 200, "height": 80,
                 "text": "colored", "color": "4"},
            ],
            "edges": [{"id": "e1", "fromNode": "a", "toNode": "l", "label": "ref"}],
        }
        st = jsoncanvas_to_state(jc)
        by_id = {o["id"]: o for o in st["objects"]}
        self.assertEqual(by_id["a"]["type"], "card")
        self.assertIn("detail", by_id["a"]["data"])
        self.assertEqual(by_id["g"]["type"], "group")
        self.assertEqual(by_id["g"]["data"]["title"], "クラスタ")
        self.assertEqual(by_id["g"]["data"]["contains"], "a,c")  # 幾何推定
        self.assertEqual(by_id["c"]["data"]["color"], "#22c55e")  # preset 4 → hex
        self.assertEqual(len(st["edges"]), 1)
        self.assertEqual(st["edges"][0]["u"], "a")

    def test_dsl_from_jsoncanvas_state(self):
        jc = {"nodes": [{"id": "x", "type": "text", "x": 10, "y": 20, "width": 200, "height": 80,
                         "text": "hello"}], "edges": []}
        dsl = dsl_from_state(jsoncanvas_to_state(jc))
        self.assertIn("card: x [", dsl)


if __name__ == "__main__":
    unittest.main()

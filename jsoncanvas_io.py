# -*- coding: utf-8 -*-
"""JSON Canvas（.canvas）⇄ AI-Canvas state の相互変換。

JSON Canvas は無限キャンバスのオープン形式（Obsidian 発・MIT・spec v1.0・jsoncanvas.org）。
- nodes: {id, type(text|file|link|group), x, y, width, height, color?, text?, label?, ...}
- edges: {id, fromNode, toNode, fromSide?, toSide?, fromEnd?, toEnd?, color?, label?}

AI-Canvas の型付きオブジェクト（math/svg/table/sticky/…）は JSON Canvas の `text` に
Markdown として写す。**完全往復**のため、各ノード/エッジに独自フィールド `ai_canvas`
（他アプリは無視する）を併記し、当方の import はそれを優先して復元する。
"""
from __future__ import annotations

import hashlib
import os
from typing import Dict, List

# JSON Canvas のプリセット色 → 代表 hex（AI-Canvas は hex 前提）
JC_PRESET_COLOR = {
    "1": "#ef4444",  # red
    "2": "#f97316",  # orange
    "3": "#eab308",  # yellow
    "4": "#22c55e",  # green
    "5": "#06b6d4",  # cyan
    "6": "#a855f7",  # purple
}
JC_NODE_TYPES = ("text", "file", "link", "group")


def _num(v, default: float = 0.0) -> float:
    try:
        f = float(v)
        return f if f == f else default
    except (TypeError, ValueError):
        return default


def _i(v, default: int = 0) -> int:
    return int(round(_num(v, default)))


def _hex16(s: str) -> str:
    return hashlib.sha1(str(s).encode("utf-8")).hexdigest()[:16]


def _color_in(v):
    """JSON Canvas の color（hex または preset "1".."6"）→ hex。"""
    if not v:
        return None
    v = str(v)
    return JC_PRESET_COLOR.get(v, v)


def _color_out(v):
    if not v:
        return None
    v = str(v)
    return v if v.startswith("#") else None


# --------------------------------------------------------------------------- Markdown 化
def _md_table(headers, rows) -> str:
    if not headers and not rows:
        return ""
    hs = [h.strip() for h in str(headers or "").split(",") if h.strip()]
    out: List[str] = []
    if hs:
        out.append("| " + " | ".join(hs) + " |")
        out.append("| " + " | ".join(["---"] * len(hs)) + " |")
    for r in str(rows or "").split(";"):
        r = r.strip()
        if not r:
            continue
        cells = [c.strip() for c in r.split("|")]
        out.append("| " + " | ".join(cells) + " |")
    return "\n".join(out)


def _md_for_object(o: dict) -> str:
    """AI-Canvas オブジェクト → JSON Canvas text（他アプリで読める Markdown）。"""
    d = o.get("data") or {}
    typ = o.get("type", "card")
    if typ == "math":
        title = d.get("title") or d.get("label") or ""
        latex = d.get("latex") or ""
        body = f"$$\n{latex}\n$$" if latex else ""
        return (f"**{title}**\n\n{body}" if title else body).strip()
    if typ == "svg":
        return d.get("svg_content") or d.get("title") or ""
    if typ == "table":
        return _md_table(d.get("headers") or d.get("cols"), d.get("rows")) or (d.get("title") or "")
    if typ == "group":
        return d.get("title") or ""
    parts: List[str] = []
    if d.get("title"):
        parts.append(f"# {d['title']}")
    if d.get("sub"):
        parts.append(f"*{d['sub']}*")
    if d.get("content") or d.get("text"):
        parts.append(d.get("content") or d.get("text"))
    if d.get("detail"):
        parts.append(d["detail"])
    return "\n\n".join(p for p in parts if p).strip()


def _first_line(text: str, limit: int = 60) -> str:
    for line in str(text or "").splitlines():
        s = line.strip().lstrip("#").strip()
        if s:
            return s[:limit]
    return ""


# --------------------------------------------------------------------------- 座標補完
def _hierarchy_levels(node_ids: List[str], edges: List[dict]) -> Dict[str, int]:
    """JS autoLayout 相当のサイクル安全な階層（BFS・各ノード一度だけ）。"""
    adj: Dict[str, List[str]] = {i: [] for i in node_ids}
    indeg: Dict[str, int] = {i: 0 for i in node_ids}
    for e in edges:
        u, v = e.get("u"), e.get("v")
        if u in adj and v in adj:
            adj[u].append(v)
            indeg[v] += 1
    seeds = [i for i in node_ids if indeg[i] == 0]
    if not seeds and node_ids:
        seeds = [node_ids[0]]
    level: Dict[str, int] = {}
    q = list(seeds)
    for s in seeds:
        level[s] = 0
    while q:
        u = q.pop(0)
        for v in adj.get(u, []):
            if v not in level:
                level[v] = level[u] + 1
                q.append(v)
    for i in node_ids:
        level.setdefault(i, 0)
    return level


def _layout_all(objects: List[dict], edges: List[dict]) -> Dict[str, tuple]:
    """座標欠落時のフォールバック階層レイアウト（LR）。group は包含ノードの外接矩形。"""
    node_ids = [str(o.get("id", "")) for o in objects if o.get("type") != "group"]
    level = _hierarchy_levels(node_ids, edges)
    by_level: Dict[int, List[str]] = {}
    for i in node_ids:
        by_level.setdefault(level[i], []).append(i)
    pos: Dict[str, tuple] = {}
    startX, startY, gapX, gapY = 80, 120, 340, 150
    for lvl, ids in by_level.items():
        for rank, i in enumerate(ids):
            pos[i] = (startX + lvl * gapX, startY + rank * gapY)
    for o in objects:
        if o.get("type") != "group":
            continue
        d = o.get("data") or {}
        members = [m.strip() for m in str(d.get("contains") or "").split(",") if m.strip()]
        xs = [pos[m][0] for m in members if m in pos]
        ys = [pos[m][1] for m in members if m in pos]
        pos[str(o.get("id", ""))] = ((min(xs) - 30, min(ys) - 50) if xs and ys else (startX - 40, startY - 60))
    return pos


# --------------------------------------------------------------------------- export
def state_to_jsoncanvas(state: dict, auto_layout: bool = True) -> dict:
    """AI-Canvas state（canvas_state.json）→ JSON Canvas dict。

    座標が欠けたノード（自動整列ノードは state に x/y を持たない）がある場合、
    auto_layout=True なら階層レイアウトで全ノードの座標を補う（他アプリで重ならない）。
    """
    objects = state.get("objects", [])
    edges_in = state.get("edges", [])

    positions: Dict[str, tuple] = {}
    for o in objects:
        d = o.get("data") or {}
        x = o.get("x", d.get("x"))
        y = o.get("y", d.get("y"))
        if x is not None and y is not None:
            positions[str(o.get("id", ""))] = (_num(x), _num(y))
    if auto_layout and len(positions) < len(objects):
        positions = _layout_all(objects, edges_in)

    nodes: List[dict] = []
    for o in objects:
        d = o.get("data") or {}
        typ = o.get("type", "card")
        jc_type = "group" if typ == "group" else "text"
        px, py = positions.get(str(o.get("id", "")), (0, 0))
        node = {
            "id": str(o.get("id", "")),
            "type": jc_type,
            "x": _i(px),
            "y": _i(py),
            "width": _i(o.get("w", d.get("w", 250)), 250),
            "height": _i(o.get("h", d.get("h", 100)), 100),
        }
        color = _color_out(d.get("color"))
        if color:
            node["color"] = color
        if jc_type == "group":
            node["label"] = d.get("title") or str(o.get("id", ""))
        else:
            node["text"] = _md_for_object(o)
        # 完全往復用の独自拡張（他アプリは無視）
        node["ai_canvas"] = {"type": typ, "data": d}
        nodes.append(node)

    edges: List[dict] = []
    for idx, e in enumerate(edges_in):
        u, v = e.get("u"), e.get("v")
        if not u or not v:
            continue
        st = e.get("style") or {}
        ed = {"id": _hex16(f"{u}->{v}:{idx}"), "fromNode": u, "toNode": v}
        if e.get("label"):
            ed["label"] = e["label"]
        color = _color_out(st.get("stroke"))
        if color:
            ed["color"] = color
        arrow = st.get("arrow")
        if arrow == "none":
            ed["fromEnd"], ed["toEnd"] = "none", "none"
        elif arrow == "double":
            ed["fromEnd"], ed["toEnd"] = "arrow", "arrow"
        else:
            ed["fromEnd"], ed["toEnd"] = "none", "arrow"
        ext: Dict = {}
        if st.get("width") is not None:
            ext["width"] = st["width"]
        if st.get("dash"):
            ext["dash"] = st["dash"]
        if arrow:
            ext["arrow"] = arrow
        if st.get("arrow_color"):
            ext["arrow_color"] = st["arrow_color"]
        if ext:
            ed["ai_canvas"] = ext
        edges.append(ed)

    return {"nodes": nodes, "edges": edges}


# --------------------------------------------------------------------------- import
def _infer_node(n: dict):
    """独自拡張の無い（他アプリ製）JSON Canvas ノード → (AI-Canvas型, data)。"""
    t = n.get("type")
    color = _color_in(n.get("color"))
    if t == "group":
        data = {"title": n.get("label") or ""}
        if color:
            data["color"] = color
        return "group", data
    if t == "file":
        f = n.get("file") or ""
        data = {"title": os.path.basename(f) or f, "sub": f}
        if f:
            data["detail"] = f"[file]({f})"
        return "card", data
    if t == "link":
        u = n.get("url") or ""
        return "card", {"title": u, "detail": u}
    # text（既定）
    text = n.get("text") or ""
    data = {"title": _first_line(text) or "note"}
    if text.strip():
        data["detail"] = text
    if color:
        data["color"] = color
    return "card", data


def _derive_arrow(e: dict) -> str:
    if e.get("toEnd") == "none" and e.get("fromEnd") == "none":
        return "none"
    if e.get("toEnd") == "arrow" and e.get("fromEnd") == "arrow":
        return "double"
    return ""


def jsoncanvas_to_state(jc: dict) -> dict:
    """JSON Canvas dict → AI-Canvas state（canvas_state.json 相当）。"""
    objects: List[dict] = []
    for n in jc.get("nodes") or []:
        ext = n.get("ai_canvas") or {}
        if ext.get("type"):
            typ = ext["type"]
            data = dict(ext.get("data") or {})
        else:
            typ, data = _infer_node(n)
        objects.append({
            "id": str(n.get("id", "")),
            "type": typ,
            "w": _num(n.get("width"), 250),
            "h": _num(n.get("height"), 100),
            "x": _num(n.get("x"), 0),
            "y": _num(n.get("y"), 0),
            "data": data,
        })

    # group の contains は幾何（中心が group 内か）から推定。
    # ただし当方由来（ai_canvas 復元）で contains 済みなら尊重する。
    for g in [o for o in objects if o["type"] == "group"]:
        if g["data"].get("contains"):
            continue
        gx, gy, gw, gh = g["x"], g["y"], g["w"], g["h"]
        inside = []
        for o in objects:
            if o is g or o["type"] == "group":
                continue
            cx, cy = o["x"] + o["w"] / 2, o["y"] + o["h"] / 2
            if gx <= cx <= gx + gw and gy <= cy <= gy + gh:
                inside.append(o["id"])
        if inside:
            g["data"]["contains"] = ",".join(inside)

    edges: List[dict] = []
    for e in jc.get("edges") or []:
        u, v = e.get("fromNode"), e.get("toNode")
        if not u or not v:
            continue
        ext = e.get("ai_canvas") or {}
        style: Dict = {}
        color = _color_in(e.get("color"))
        if color:
            style["stroke"] = color
        if ext.get("width") is not None:
            style["width"] = ext["width"]
        if ext.get("dash"):
            style["dash"] = ext["dash"]
        arrow = ext.get("arrow") or _derive_arrow(e)
        if arrow:
            style["arrow"] = arrow
        if ext.get("arrow_color"):
            style["arrow_color"] = ext["arrow_color"]
        item = {"u": u, "v": v, "label": e.get("label") or ""}
        if style:
            item["style"] = style
        edges.append(item)

    return {"schema_version": 1, "objects": objects, "edges": edges}

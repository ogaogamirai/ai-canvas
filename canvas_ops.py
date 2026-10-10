# -*- coding: utf-8 -*-
"""AI-Canvas 操作ユーティリティ（CLI 用・本体非依存）。

- state → DSL 再生成（D1）
- DSL 構造の解析・差分（D2）
- 構造マージ（D3）
- グラフ問い合わせ: neighbors / path / tree（D4）
"""
from __future__ import annotations

import re
from collections import OrderedDict
from typing import Dict, List, Optional, Tuple

LINE_RE = re.compile(r"^([a-z]+):\s*([a-zA-Z0-9_-]+)\s*\[(.*)\]\s*$")
ARROW_RE = re.compile(r"^([^\s\-]+)\s*->\s*([^\s:]+)(?:\s*:\s*(.*))?$")
PROP_RE = re.compile(r'([a-zA-Z0-9_-]+)=(?:"([^"]*)"|\'([^\']*)\'|([^\s,\]]+))')

CONTROL = frozenset({"clear", "reset", "reload", "refresh", "export", "save"})
NODE_TYPES = frozenset({"card", "math", "text", "svg", "sticky", "table", "group"})
SKIP_NODE_EDGE_PROPS = frozenset(
    {"to", "link", "edge", "edge_color", "edge_width", "edge_dash", "edge_stroke", "edge_style", "edge_arrow"}
)
BARE_KEYS = frozenset({"x", "y", "width", "edge_width"})


def _props(raw: str) -> "OrderedDict[str, str]":
    out: "OrderedDict[str, str]" = OrderedDict()
    for m in PROP_RE.finditer(raw):
        val = m.group(2) if m.group(2) is not None else (m.group(3) if m.group(3) is not None else m.group(4))
        out[m.group(1)] = val
    return out


def _dq(v) -> str:
    return '"' + str(v).replace('"', '\\"') + '"'


def _num(v, default: float = 0.0) -> float:
    try:
        f = float(v)
        return f if f == f else default
    except (TypeError, ValueError):
        return default


# --------------------------------------------------------------------------- D1
def dsl_from_state(state: dict) -> str:
    """canvas_state.json（構造化JSON）から DSL を再生成する（JS buildExportDsl 相当）。"""
    lines = ["clear"]
    for o in state.get("objects", []):
        d = o.get("data") or {}
        typ = o.get("type", "card")
        oid = o.get("id", "")
        is_group_contains = typ == "group" and d.get("contains")
        props: List[str] = []
        if not is_group_contains and ("x" in o or "x" in d):
            props.append(f"x={round(_num(o.get('x', d.get('x'))))}")
            props.append(f"y={round(_num(o.get('y', d.get('y'))))}")
        for k, v in d.items():
            if k in ("id", "x", "y"):
                continue
            if k in ("w", "h") and d.get("contains"):
                continue
            if k in SKIP_NODE_EDGE_PROPS:
                continue
            props.append(f"{k}={_dq(v)}")
        lines.append(f"{typ}: {oid} [{', '.join(props)}]")
    edges = state.get("edges", [])
    if edges:
        lines.append("")
        for idx, e in enumerate(edges):
            st = e.get("style") or {}
            eprops = [f'from="{e.get("u")}"', f'to="{e.get("v")}"']
            if e.get("label"):
                eprops.append(f"label={_dq(e['label'])}")
            if st.get("stroke"):
                eprops.append(f'color="{st["stroke"]}"')
            if st.get("width") is not None:
                eprops.append(f'width={st["width"]}')
            if st.get("dash"):
                eprops.append(f'dash="{st["dash"]}"')
            if st.get("arrow") == "none":
                eprops.append("arrow=none")
            elif st.get("arrow") == "double":
                eprops.append("arrow=double")
            if st.get("arrow_color"):
                eprops.append(f'arrow_color="{st["arrow_color"]}"')
            lines.append(f'edge: e{idx + 1} [{", ".join(eprops)}]')
    return "\n".join(lines)


# --------------------------------------------------------------------------- 解析
def _edge_from_standalone(props: dict) -> dict:
    return {
        "label": props.get("label", ""),
        "stroke": props.get("color") or props.get("stroke") or "",
        "width": props.get("width"),
        "dash": props.get("dash") or "",
        "arrow": props.get("arrow") or "",
    }


def _edge_from_node(props: dict) -> dict:
    return {
        "label": props.get("link") or props.get("label") or "",
        "stroke": props.get("edge_color") or props.get("edge_stroke") or "",
        "width": props.get("edge_width"),
        "dash": props.get("edge_dash") or "",
        "arrow": props.get("edge_arrow") or "",
    }


def parse_dsl(text: str) -> dict:
    """DSL を構造へ解析。inline to= / 矢印もエッジへ正規化する。"""
    nodes: "OrderedDict[str, dict]" = OrderedDict()
    edges: "OrderedDict[Tuple[str, str], dict]" = OrderedDict()
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith("#") or s.lower() in CONTROL:
            continue
        m = LINE_RE.match(s)
        if m:
            typ, oid, raw = m.group(1), m.group(2), m.group(3)
            props = _props(raw)
            if typ == "edge":
                u, v = props.get("from"), props.get("to")
                if u and v:
                    edges[(u, v)] = _edge_from_standalone(props)
            elif typ in NODE_TYPES:
                clean = OrderedDict((k, v) for k, v in props.items() if k not in SKIP_NODE_EDGE_PROPS)
                nodes[oid] = {"type": typ, "props": clean}
                if props.get("to"):
                    edges[(props["to"], oid)] = _edge_from_node(props)
            continue
        am = ARROW_RE.match(s)
        if am:
            u, v = am.group(1).strip(), am.group(2).strip()
            edges[(u, v)] = {"label": (am.group(3) or "").strip(), "stroke": "", "width": None, "dash": "", "arrow": ""}
    return {"nodes": nodes, "edges": edges}


def render_structure(struct: dict) -> str:
    """構造を DSL へ書き戻す。"""
    lines = ["clear"]
    for oid, n in struct["nodes"].items():
        parts = [f"{k}={v}" if k in BARE_KEYS else f"{k}={_dq(v)}" for k, v in n["props"].items()]
        lines.append(f'{n["type"]}: {oid} [{", ".join(parts)}]')
    if struct["edges"]:
        lines.append("")
        for idx, ((u, v), e) in enumerate(struct["edges"].items()):
            eprops = [f'from="{u}"', f'to="{v}"']
            if e.get("label"):
                eprops.append(f"label={_dq(e['label'])}")
            if e.get("stroke"):
                eprops.append(f'color="{e["stroke"]}"')
            if e.get("width") is not None:
                eprops.append(f'width={e["width"]}')
            if e.get("dash"):
                eprops.append(f'dash="{e["dash"]}"')
            if e.get("arrow") == "none":
                eprops.append("arrow=none")
            elif e.get("arrow") == "double":
                eprops.append("arrow=double")
            lines.append(f'edge: e{idx + 1} [{", ".join(eprops)}]')
    return "\n".join(lines)


# --------------------------------------------------------------------------- D2
def diff_dsl(a_text: str, b_text: str) -> List[Tuple[str, str, str, str]]:
    """構造差分。[(kind, op, ref, detail)] op: + - ~"""
    A, B = parse_dsl(a_text), parse_dsl(b_text)
    out: List[Tuple[str, str, str, str]] = []
    an, bn = A["nodes"], B["nodes"]
    for oid, n in an.items():
        if oid not in bn:
            out.append(("node", "-", oid, n["type"]))
    for oid, n in bn.items():
        if oid not in an:
            out.append(("node", "+", oid, n["type"]))
        else:
            keys = []
            for k in set(an[oid]["props"]) | set(n["props"]):
                if an[oid]["props"].get(k) != n["props"].get(k):
                    keys.append(k)
            if an[oid]["type"] != n["type"]:
                keys.append("type")
            if keys:
                out.append(("node", "~", oid, ",".join(sorted(keys))))
    ae, be = A["edges"], B["edges"]
    for k in ae:
        if k not in be:
            out.append(("edge", "-", f"{k[0]} -> {k[1]}", ""))
    for k, e in be.items():
        if k not in ae:
            out.append(("edge", "+", f"{k[0]} -> {k[1]}", ""))
        elif ae[k] != e:
            out.append(("edge", "~", f"{k[0]} -> {k[1]}", ""))
    return out


# --------------------------------------------------------------------------- D3
def merge_dsl(base_text: str, patch_text: str) -> str:
    """base へ patch を増分適用（id 一致は更新、無ければ追加）。"""
    base = parse_dsl(base_text)
    patch = parse_dsl(patch_text)
    for oid, n in patch["nodes"].items():
        if oid in base["nodes"]:
            base["nodes"][oid]["type"] = n["type"]
            base["nodes"][oid]["props"].update(n["props"])
        else:
            base["nodes"][oid] = n
    for k, e in patch["edges"].items():
        base["edges"][k] = e
    return render_structure(base)


# --------------------------------------------------------------------------- D4
def neighbors(struct: dict, node_id: str) -> dict:
    incoming = [f"{u} -> {v}" for (u, v) in struct["edges"] if v == node_id]
    outgoing = [f"{u} -> {v}" for (u, v) in struct["edges"] if u == node_id]
    return {"incoming": incoming, "outgoing": outgoing}


def find_path(struct: dict, src: str, dst: str, undirected: bool = False) -> Optional[List[str]]:
    adj: Dict[str, List[str]] = {}
    for (u, v) in struct["edges"]:
        adj.setdefault(u, []).append(v)
        if undirected:
            adj.setdefault(v, []).append(u)
    if src == dst:
        return [src]
    from collections import deque

    prev = {src: None}
    q = deque([src])
    while q:
        cur = q.popleft()
        for nxt in adj.get(cur, []):
            if nxt not in prev:
                prev[nxt] = cur
                if nxt == dst:
                    path = [dst]
                    while path[-1] != src:
                        path.append(prev[path[-1]])
                    return list(reversed(path))
                q.append(nxt)
    return None


def tree_lines(struct: dict) -> List[str]:
    incoming = {v for (_, v) in struct["edges"]}
    roots = [oid for oid in struct["nodes"] if oid not in incoming]
    if not roots and struct["nodes"]:
        roots = [next(iter(struct["nodes"]))]
    adj: Dict[str, List[str]] = {}
    for (u, v) in struct["edges"]:
        adj.setdefault(u, []).append(v)
    lines: List[str] = []
    seen = set()

    def walk(nid: str, depth: int) -> None:
        if nid in seen:
            lines.append("  " * depth + f"- {nid} (…)")
            return
        seen.add(nid)
        typ = struct["nodes"].get(nid, {}).get("type", "?")
        lines.append("  " * depth + f"- {nid} [{typ}]")
        for c in adj.get(nid, []):
            walk(c, depth + 1)

    for r in roots:
        walk(r, 0)
    for oid in struct["nodes"]:
        if oid not in seen:
            walk(oid, 0)
    return lines

# -*- coding: utf-8 -*-
"""AI-Canvas DSL 検証（行番号付きの error / warning 診断）。

本体（HTML/JS）には載せず、CLI 側に置くことでファイルサイズを気にせず充実させる。
将来的に一部をエディタの正規化（rich）へ移す前提。
"""
from __future__ import annotations

import re
from typing import Dict, List

LINE_RE = re.compile(r"^([a-z]+):\s*([a-zA-Z0-9_-]+)\s*\[(.*)\]\s*$")
ARROW_RE = re.compile(r"^([^\s\-]+)\s*->\s*([^\s:]+)(?:\s*:\s*(.*))?$")
PROP_RE = re.compile(r'([a-zA-Z0-9_-]+)=(?:"([^"]*)"|\'([^\']*)\'|([^\s,\]]+))')

NODE_TYPES = frozenset({"card", "math", "text", "svg", "sticky", "table", "group"})
EDGE_TYPES = frozenset({"edge"})
CONTROL = frozenset({"clear", "reset", "reload", "refresh", "export", "save"})
HEX_RE = re.compile(r"^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")
COLOR_KEYS = ("color", "edge_color", "edge_stroke", "arrow_color")
WIDTH_KEYS = ("width", "edge_width")
ARROW_VALUES = frozenset({"single", "double", "none", "false", "true", "0", "1"})


def _props(raw: str) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for m in PROP_RE.finditer(raw):
        val = m.group(2) if m.group(2) is not None else (m.group(3) if m.group(3) is not None else m.group(4))
        out[m.group(1)] = val
    return out


def _diag(line: int, level: str, message: str) -> Dict[str, str]:
    return {"line": line, "level": level, "message": message}


def check_dsl_text(text: str) -> List[Dict[str, str]]:
    """DSL テキストを検証し、行番号付きの診断リストを返す（level: error|warning）。"""
    diags: List[Dict[str, str]] = []
    ids: Dict[str, int] = {}
    parsed = []  # (line_no, kind, ref, props)

    for i, raw in enumerate(text.splitlines(), 1):
        s = raw.strip()
        if not s or s.startswith("#") or s.lower() in CONTROL:
            continue

        m = LINE_RE.match(s)
        if m:
            typ, oid, rawprops = m.group(1), m.group(2), m.group(3)
            props = _props(rawprops)
            if typ not in NODE_TYPES and typ not in EDGE_TYPES:
                diags.append(_diag(i, "error", f"未知の型 '{typ}'（card/math/text/svg/sticky/table/group/edge）"))
                continue
            if typ in NODE_TYPES:
                if oid in ids:
                    diags.append(_diag(i, "error", f"id '{oid}' が重複（L{ids[oid]} で定義済み）"))
                else:
                    ids[oid] = i
            parsed.append((i, typ, oid, props))
            continue

        am = ARROW_RE.match(s)
        if am:
            parsed.append((i, "arrow", am.group(1).strip(), {"to": am.group(2).strip()}))
            continue

        if s.count("[") != s.count("]"):
            diags.append(_diag(i, "error", "構文エラー: 括弧 [ ] が閉じていない可能性（type: id [props]）"))
        else:
            diags.append(_diag(i, "warning", "未整形行（自動で card 化されます）"))

    for i, typ, ref, props in parsed:
        # 参照チェック
        if typ == "edge":
            fr, to = props.get("from"), props.get("to")
            if not fr or not to:
                diags.append(_diag(i, "error", "edge には from / to が必要"))
            else:
                if fr not in ids:
                    diags.append(_diag(i, "error", f"from='{fr}' は未定義のノード"))
                if to not in ids:
                    diags.append(_diag(i, "error", f"to='{to}' は未定義のノード"))
        elif typ == "arrow":
            if ref not in ids:
                diags.append(_diag(i, "error", f"'{ref}' は未定義のノード"))
            if props.get("to") not in ids:
                diags.append(_diag(i, "error", f"'{props.get('to')}' は未定義のノード"))
        else:  # node
            if props.get("to") and props["to"] not in ids:
                diags.append(_diag(i, "error", f"to='{props['to']}' は未定義のノード"))

        # 値チェック（共通）
        for ck in COLOR_KEYS:
            v = props.get(ck)
            if v and not HEX_RE.match(str(v).strip()):
                diags.append(_diag(i, "warning", f"{ck}='{v}' は色（#rgb / #rrggbb）として不正"))
        for wk in WIDTH_KEYS:
            v = props.get(wk)
            if v not in (None, ""):
                try:
                    float(v)
                except (TypeError, ValueError):
                    diags.append(_diag(i, "warning", f"{wk}='{v}' は数値ではない"))
        av = props.get("arrow") or props.get("edge_arrow")
        if av and str(av).lower() not in ARROW_VALUES:
            diags.append(_diag(i, "warning", f"arrow='{av}' は single / double / none のいずれか"))

    diags.sort(key=lambda d: d["line"])
    return diags

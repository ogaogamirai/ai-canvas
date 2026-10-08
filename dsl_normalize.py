# -*- coding: utf-8 -*-
"""
AI-Canvas DSL 正規化（index.html の KaTeX / detail 表示と同じ規則を投入前に適用）
"""

from __future__ import annotations

import re
from typing import Dict, List, Tuple

LINE_RE = re.compile(r"^([a-z]+):\s*([a-zA-Z0-9_-]+)\s*\[(.*)\]\s*$")
PROP_RE = re.compile(
    r'([a-zA-Z0-9_-]+)=(?:"([^"]*)"|\'([^\']*)\'|([^\s,\]]+))'
)
LATEX_ATTR_KEYS = frozenset({"latex", "detail"})
MATH_INLINE_RE = re.compile(
    r"\$\$[\s\S]+?\$\$|\$(?:\\.|[^\$\\])+\$"
)


def normalize_latex_for_katex(expr: str) -> str:
    """JS normalizeLatexForKatex と同等。"""
    if not expr:
        return ""
    s = expr.replace("\u00a5", "\\").replace("¥", "\\").strip()
    while True:
        new = re.sub(r"\\{2}(?=[a-zA-Z])", r"\\", s)
        if new == s:
            break
        s = new
    return s


def _normalize_math_in_text(text: str) -> str:
    if not text:
        return text

    def repl(match: re.Match) -> str:
        seg = match.group(0)
        if seg.startswith("$$") and seg.endswith("$$"):
            inner = seg[2:-2]
            return "$$" + normalize_latex_for_katex(inner) + "$$"
        if seg.startswith("$") and seg.endswith("$"):
            inner = seg[1:-1]
            return "$" + normalize_latex_for_katex(inner) + "$"
        return seg

    return MATH_INLINE_RE.sub(repl, text)


def normalize_detail_field(value: str) -> str:
    """detail 属性: 数式区間のバックスラッシュを正規化（改行エスケープ \\n は維持）。"""
    return _normalize_math_in_text(value)


def normalize_attribute(key: str, value: str) -> str:
    if key == "latex":
        return normalize_latex_for_katex(value)
    if key == "detail":
        return normalize_detail_field(value)
    return value


def _parse_props(raw_props: str) -> List[Tuple[str, str, str]]:
    """(key, value, quote_style) quote_style: dbl | sgl | bare"""
    out: List[Tuple[str, str, str]] = []
    for m in PROP_RE.finditer(raw_props):
        key = m.group(1)
        if m.group(2) is not None:
            out.append((key, m.group(2), "dbl"))
        elif m.group(3) is not None:
            out.append((key, m.group(3), "sgl"))
        else:
            out.append((key, m.group(4), "bare"))
    return out


def _format_prop(key: str, value: str, quote_style: str) -> str:
    if quote_style == "dbl":
        safe = value.replace('"', "'")
        return f'{key}="{safe}"'
    if quote_style == "sgl":
        return f"{key}='{value}'"
    if re.search(r"[\s,\[\]]", value):
        safe = value.replace('"', "'")
        return f'{key}="{safe}"'
    return f"{key}={value}"


def normalize_dsl_line(line: str) -> Tuple[str, bool]:
    """1行 DSL を正規化。変更があれば changed=True。"""
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        return line, False
    low = stripped.lower()
    if low in ("clear", "reset", "reload", "refresh", "export", "save"):
        return line, False

    m = LINE_RE.match(stripped)
    if not m:
        return line, False

    typ, oid, raw_props = m.group(1), m.group(2), m.group(3)
    props = _parse_props(raw_props)
    if not props:
        return line, False

    changed = False
    rebuilt: List[str] = []
    for key, val, qstyle in props:
        if key in LATEX_ATTR_KEYS:
            new_val = normalize_attribute(key, val)
            if new_val != val:
                changed = True
                val = new_val
        rebuilt.append(_format_prop(key, val, qstyle))

    if not changed:
        return line, False

    new_line = f"{typ}: {oid} [{', '.join(rebuilt)}]"
    if line.endswith("\n"):
        new_line += "\n"
    elif line != line.strip():
        pass
    return new_line, True


def normalize_dsl_text(text: str) -> Tuple[str, int]:
    """全文正規化。変更行数を返す。"""
    ends_with_nl = text.endswith("\n")
    lines = text.splitlines()
    out_lines: List[str] = []
    changes = 0
    for line in lines:
        new_line, ch = normalize_dsl_line(line)
        if ch:
            changes += 1
        out_lines.append(new_line)
    result = "\n".join(out_lines)
    if ends_with_nl and (out_lines or text == "\n"):
        result += "\n"
    return result, changes


def normalize_state_object_data(data: dict) -> Tuple[dict, bool]:
    """canvas_state.json の data フィールドを正規化。"""
    if not data:
        return data, False
    changed = False
    new_data = dict(data)
    if "latex" in new_data and new_data["latex"]:
        fixed = normalize_latex_for_katex(new_data["latex"])
        if fixed != new_data["latex"]:
            new_data["latex"] = fixed
            changed = True
    if "detail" in new_data and new_data["detail"]:
        fixed = normalize_detail_field(new_data["detail"])
        if fixed != new_data["detail"]:
            new_data["detail"] = fixed
            changed = True
    return new_data, changed


def normalize_state(state: dict) -> Tuple[dict, int]:
    """state 全体。変更オブジェクト数を返す。"""
    changed_count = 0
    objs = []
    for obj in state.get("objects", []):
        data = obj.get("data") or {}
        new_data, ch = normalize_state_object_data(data)
        if ch:
            changed_count += 1
            objs.append({**obj, "data": new_data})
        else:
            objs.append(obj)
    if changed_count:
        return {**state, "objects": objs}, changed_count
    return state, 0

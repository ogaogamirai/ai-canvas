# -*- coding: utf-8 -*-
"""AI-Canvas 起動復元のスモーク（GUI・webview 不要）"""
import json
import os
import re

BASE = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(BASE, "canvas_state.json")
INBOX_DSL = os.path.join(BASE, "inbox_dsl.txt")
DEMO = os.path.join(BASE, "quantum_demo.txt")


def get_startup_content():
    """canvas_app.CanvasAPI.get_startup_content と同じロジック"""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, encoding="utf-8") as f:
            state = json.load(f)
        if state.get("objects"):
            return {"mode": "state", "payload": state}
    for label, path in (("inbox", INBOX_DSL), ("demo", DEMO)):
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8") as f:
            dsl = f.read().strip()
        if dsl and dsl.lower() not in ("clear", "reset", "reload", "refresh", "export", "save"):
            return {"mode": "dsl", "payload": dsl, "source": label}
    return {"mode": "empty"}


def main():
    pack = get_startup_content()
    assert pack["mode"] == "state", pack
    n = len(pack["payload"]["objects"])
    e = len(pack["payload"]["edges"])
    assert n >= 8, n
    assert e >= 6, e
    print(f"[ok] get_startup_content: state with {n} objects, {e} edges")

    with open(os.path.join(BASE, "index.html"), encoding="utf-8") as f:
        html = f.read()
    assert "loadFromState" in html and "bootstrapCanvas" in html
    assert r"replace(/\\n(?![a-zA-Z])/g" in html
    print("[ok] index.html has bootstrap + A-fix")

    detail = next(o for o in pack["payload"]["objects"] if o["id"] == "einstein")["data"]["detail"]
    fixed = re.sub(r"\\n(?![a-zA-Z])", "\n", detail)
    assert "$$E_{max} = h\\nu - W_0$$" in fixed
    assert "解明\nアイン" in fixed
    print("[ok] detail unescape: paragraph breaks + nu preserved")


if __name__ == "__main__":
    main()

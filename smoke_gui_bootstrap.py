# -*- coding: utf-8 -*-
"""WebView2 上で bootstrap 後のノード数を確認（数秒で終了）"""
import os
import sys
import threading
import time

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import webview  # noqa: E402
from canvas_app import CanvasAPI  # noqa: E402

HTML_PATH = os.path.join(BASE, "index.html")
RESULT = {}


def _probe(window):
    time.sleep(3.5)
    try:
        RESULT["node_count"] = window.evaluate_js(
            "document.querySelectorAll('.canvas-obj').length"
        )
        RESULT["log"] = window.evaluate_js(
            "document.getElementById('log-bar').innerText"
        )
    except Exception as exc:
        RESULT["error"] = str(exc)
    finally:
        window.destroy()


def main():
    api = CanvasAPI()
    window = webview.create_window(
        "AI-Canvas smoke",
        HTML_PATH,
        js_api=api,
        width=960,
        height=640,
    )
    threading.Thread(target=_probe, args=(window,), daemon=True).start()
    webview.start()
    count = RESULT.get("node_count", 0)
    log = RESULT.get("log", "")
    if RESULT.get("error"):
        raise SystemExit(f"GUI smoke failed: {RESULT['error']}")
    if count < 8:
        raise SystemExit(f"GUI smoke failed: node_count={count}, log={log!r}")
    print(f"[ok] GUI bootstrap: {count} nodes on canvas")
    print(f"[ok] log-bar: {log[:80]}...")


if __name__ == "__main__":
    main()

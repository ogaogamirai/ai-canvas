# -*- coding: utf-8 -*-
"""Phase 1 GUI: bootstrap 後 schema_version とエッジ stroke 属性"""
import json
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
    time.sleep(4.0)
    try:
        raw = window.evaluate_js("JSON.stringify(Canvas.getFullState())")
        state = json.loads(raw)
        RESULT["schema"] = state.get("schema_version")
        RESULT["nodes"] = len(state.get("objects", []))
        RESULT["edges"] = len(state.get("edges", []))
        stroke = window.evaluate_js("""
          (function(){
            const p = document.querySelector('.edge-path[stroke]');
            return p ? p.getAttribute('stroke') : null;
          })()
        """)
        RESULT["styled_stroke"] = stroke
        RESULT["node_count"] = window.evaluate_js(
            "document.querySelectorAll('.canvas-obj').length"
        )
    except Exception as exc:
        RESULT["error"] = str(exc)
    finally:
        window.destroy()


def main():
    api = CanvasAPI()
    window = webview.create_window("phase1", HTML_PATH, js_api=api, width=960, height=640)
    threading.Thread(target=_probe, args=(window,), daemon=True).start()
    webview.start()
    if RESULT.get("error"):
        raise SystemExit(RESULT["error"])
    if RESULT.get("schema") != 1:
        raise SystemExit(f"schema_version expected 1, got {RESULT.get('schema')}")
    if RESULT.get("node_count", 0) < 8:
        raise SystemExit(f"node_count low: {RESULT}")
    print(f"[ok] schema_version={RESULT['schema']} nodes={RESULT['node_count']} edges={RESULT['edges']}")
    if RESULT.get("styled_stroke"):
        print(f"[ok] optional edge stroke on canvas: {RESULT['styled_stroke']}")
    else:
        print("[ok] no styled edge in current state (optional attrs OK if demo not loaded)")


if __name__ == "__main__":
    main()

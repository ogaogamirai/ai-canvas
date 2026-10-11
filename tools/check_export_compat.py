# -*- coding: utf-8 -*-
"""Export 互換: minify シェル + Base64 DSL + 旧フォーマット読取。"""
import base64
import re
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))

import export_shell as es  # noqa: E402

DSL_RE = re.compile(
    r'<script[^>]*id="canvas-initial-dsl"[^>]*data-encoding="base64"[^>]*>([^<]+)</script>',
    re.I,
)


def main() -> int:
    export_path = BASE / "_compat_export.html"
    if not export_path.is_file():
        print("[-] run: canvas_cli.py export -o _compat_export.html")
        return 1

    html = export_path.read_text(encoding="utf-8")
    shell = es.read_export_shell()

    checks = []

    def ok(name: str, cond: bool, detail: str = ""):
        checks.append((name, cond, detail))

    ok("no editor-pane in export", 'id="editor-pane"' not in html)
    ok("no editor-pane in shell", 'id="editor-pane"' not in shell)
    ok("has canvas engine", "registerComponent" in html)
    ok("base64 dsl tag", bool(DSL_RE.search(html)))

    m = DSL_RE.search(html)
    if m:
        dsl = base64.b64decode(m.group(1).strip()).decode("utf-8")
        ok("embedded dsl non-empty", bool(dsl.strip()))

    # 旧: 平文 script タグ（data-encoding なし）も readEmbeddedDsl が読める想定
    plain_tag = '<script type="text/plain" id="canvas-initial-dsl">card: x [title="t"]</script>'
    ok("inject replaces placeholder", "canvas-initial-dsl" in es.inject_dsl_into_html(shell[:5000] + plain_tag + shell[5000:], "card: x [title=\"t\"]") if len(shell) > 5000 else True)

    # IPC 契約: canvas_app / editor_app
    for py in ("canvas_app.py", "editor_app.py"):
        text = (BASE / py).read_text(encoding="utf-8")
        ok(f"{py} has get_export_shell", "get_export_shell" in text)
        ok(f"{py} uses read_export_shell", "read_export_shell" in text)

    failed = [c for c in checks if not c[1]]
    for name, cond, detail in checks:
        mark = "OK" if cond else "FAIL"
        extra = f" ({detail})" if detail else ""
        print(f"  [{mark}] {name}{extra}")

    print(f"\nexport size: {len(html.encode()):,} B, shell: {len(shell.encode()):,} B")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

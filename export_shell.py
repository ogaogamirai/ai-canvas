# -*- coding: utf-8 -*-
"""単一 HTML のビルド（src/ → editor.html / index.html / index.export.html）と DSL 埋め込み。

ソース（手編集する正本）は `src/`:

  src/template.html   … HTML シェル（エディタ層は <!-- @editor-only:start/end --> で囲う）
  src/styles.css      … 共有 CSS（エディタ層は /* @editor-only:start/end */ で囲う）
  src/editor.css      … エディタ専用 CSS
  src/canvas.js       … キャンバスエンジン（共有 JS）
  src/editor.js       … DSL Editor 層（EditorApp）

生成物:

  editor.html         … 人間/AI コックピット（canvas + editor）
  index.html          … canvas-only（エディタ層を除去）
  index.export.html   … canvas-only を minify した配布用シェル
"""
import base64
import re
import subprocess
import tempfile
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
SRC = BASE_DIR / "src"
TEMPLATE = SRC / "template.html"
STYLES = SRC / "styles.css"
EDITOR_CSS = SRC / "editor.css"
CANVAS_JS = SRC / "canvas.js"
EDITOR_JS = SRC / "editor.js"

EDITOR_HTML = BASE_DIR / "editor.html"
INDEX_HTML = BASE_DIR / "index.html"
EXPORT_SHELL = BASE_DIR / "index.export.html"

DSL_SCRIPT_RE = re.compile(
    r'<script\s+[^>]*id="canvas-initial-dsl"[^>]*>[\s\S]*?</script>',
    re.I,
)

# /* @editor-only:start */ ... /* @editor-only:end */  または
# <!-- @editor-only:start --> ... <!-- @editor-only:end -->
EDITOR_BLOCK_RE = re.compile(
    r"/\*\s*@editor-only:start.*?@editor-only:end\s*\*/"
    r"|<!--\s*@editor-only:start.*?@editor-only:end\s*-->",
    re.S,
)


def strip_editor_regions(text: str) -> str:
    """エディタ専用領域（マーカーで囲まれた範囲）を除去する。"""
    return EDITOR_BLOCK_RE.sub("", text)


def build_embedded_dsl_script_tag(dsl: str) -> str:
    """UTF-8 DSL を Base64 で埋め込む（; \\nu </script> 等で壊れない）。"""
    body = base64.b64encode(dsl.encode("utf-8")).decode("ascii")
    return f'<script type="text/plain" id="canvas-initial-dsl" data-encoding="base64">{body}</script>'


def read_export_shell() -> str:
    """GUI / CLI export 用テンプレート（minify 版があれば優先）。"""
    if EXPORT_SHELL.is_file():
        return EXPORT_SHELL.read_text(encoding="utf-8")
    return INDEX_HTML.read_text(encoding="utf-8")


def inject_dsl_into_html(html: str, dsl: str) -> str:
    """DSL を Base64 script タグに埋め込む（; や \\nu を含む DSL でも壊れない）。"""
    tag = build_embedded_dsl_script_tag(dsl)
    out, n = DSL_SCRIPT_RE.subn(tag, html, count=1)
    if n != 1:
        raise ValueError('canvas-initial-dsl 埋め込み箇所が見つかりません')
    return out


def _assemble(include_editor: bool, minify: bool = False) -> str:
    template = TEMPLATE.read_text(encoding="utf-8")
    styles = STYLES.read_text(encoding="utf-8")
    canvas_js = CANVAS_JS.read_text(encoding="utf-8")

    if include_editor:
        styles_all = styles + "\n" + EDITOR_CSS.read_text(encoding="utf-8")
        js_all = canvas_js + "\n" + EDITOR_JS.read_text(encoding="utf-8")
    else:
        template = strip_editor_regions(template)
        styles_all = strip_editor_regions(styles)
        js_all = canvas_js

    if minify:
        styles_all = _minify_css(styles_all)
        js_all = _minify_js(js_all)

    return template.replace("{{STYLES}}", styles_all).replace("{{APP_JS}}", js_all)


def build_editor_html() -> Path:
    """src/ から editor.html（canvas + editor）を生成。"""
    EDITOR_HTML.write_text(_assemble(True), encoding="utf-8")
    return EDITOR_HTML


def build_canvas_html() -> str:
    """src/ から canvas-only の index.html を生成。"""
    html = _assemble(False)
    INDEX_HTML.write_text(html, encoding="utf-8")
    return html


def build_export_shell(force: bool = True) -> Path:
    """canvas-only を minify して index.export.html を生成。"""
    html = _assemble(False, minify=True)
    if force or not EXPORT_SHELL.is_file():
        EXPORT_SHELL.write_text(html, encoding="utf-8")
    return EXPORT_SHELL


def build_all() -> Path:
    """editor.html / index.html / index.export.html をまとめて生成。"""
    build_editor_html()
    build_canvas_html()
    return build_export_shell()


def _run_cmd(cmd: list[str], stdin_text: str | None = None) -> bytes:
    if cmd and cmd[0] == "npx":
        cmd = ["npx.cmd", *cmd[1:]]
    r = subprocess.run(
        cmd,
        input=stdin_text.encode("utf-8") if stdin_text else None,
        capture_output=True,
        cwd=str(BASE_DIR),
    )
    if r.returncode != 0:
        err = (r.stderr or r.stdout or b"").decode("utf-8", errors="replace")[:800]
        raise RuntimeError(err or "command failed")
    return r.stdout


def _minify_js(js: str) -> str:
    with tempfile.TemporaryDirectory() as td:
        js_in = Path(td) / "app.js"
        js_out = Path(td) / "app.min.js"
        js_in.write_text(js, encoding="utf-8")
        _run_cmd(
            [
                "npx", "--yes", "esbuild", str(js_in),
                f"--outfile={js_out}", "--minify", "--legal-comments=none", "--target=es2020",
            ]
        )
        return js_out.read_text(encoding="utf-8")


def _minify_css(css: str) -> str:
    return _run_cmd(["npx", "--yes", "clean-css-cli", "-O2"], stdin_text=css).decode("utf-8")


if __name__ == "__main__":
    out = build_all()
    src = SRC.stat()
    print(f"[+] editor.html      = {EDITOR_HTML.stat().st_size:,} B")
    print(f"[+] index.html       = {INDEX_HTML.stat().st_size:,} B")
    print(f"[+] index.export.html= {out.stat().st_size:,} B")

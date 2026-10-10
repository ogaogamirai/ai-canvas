# -*- coding: utf-8 -*-
"""単体 HTML 用シェル（index.export.html）のビルドと DSL 埋め込み。

エンジン正本は **editor.html**（単一の手編集ソース）。
`index.html` / `index.export.html` はここで editor.html から生成する派生物:

  editor.html
    │  strip_editor_regions()  …  /* @editor-only:start */ 〜 end / <!-- ... --> を除去
    ▼
  index.html            … canvas-only（エディタ層なし・非圧縮）
    │  minify (esbuild / clean-css)
    ▼
  index.export.html     … canvas-only（minify・配布用シェル）

これによりエンジンの二重管理（旧 index.html との分岐）を解消する。
"""
import base64
import re
import subprocess
import tempfile
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
SOURCE_HTML = BASE_DIR / "editor.html"      # 手編集正本
INDEX_HTML = BASE_DIR / "index.html"        # 生成物（canvas-only）
EXPORT_SHELL = BASE_DIR / "index.export.html"  # 生成物（canvas-only / minify）

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


def strip_editor_regions(html: str) -> str:
    """editor.html からエディタ専用領域を除去し、canvas-only HTML を返す。"""
    return EDITOR_BLOCK_RE.sub("", html)


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
    """DSL を JSON script タグに埋め込む（; や \\nu を含む DSL でも壊れない）。"""
    tag = build_embedded_dsl_script_tag(dsl)
    out, n = DSL_SCRIPT_RE.subn(tag, html, count=1)
    if n != 1:
        raise ValueError('canvas-initial-dsl 埋め込み箇所が見つかりません')
    return out


def build_canvas_html() -> str:
    """editor.html（正本）から canvas-only の index.html を生成して書き出す。"""
    canvas = strip_editor_regions(SOURCE_HTML.read_text(encoding="utf-8"))
    INDEX_HTML.write_text(canvas, encoding="utf-8")
    return canvas


def _extract_parts(html: str) -> tuple[str, str]:
    styles = re.findall(r"<style>(.*?)</style>", html, re.S)
    scripts = re.findall(r"<script[^>]*>(.*?)</script>", html, re.S)
    app_js = ""
    for block in scripts:
        if "registerComponent" in block or "const Canvas" in block:
            app_js = block
            break
    if not app_js and len(scripts) > 1:
        app_js = scripts[-1]
    return (styles[0] if styles else "", app_js)


def _rebuild_html(html: str, css: str, js: str) -> str:
    out = re.sub(
        r"<style>.*?</style>",
        lambda _: f"<style>{css}</style>",
        html,
        count=1,
        flags=re.S,
    )
    matches = [
        m
        for m in re.finditer(r"<script([^>]*)>(.*?)</script>", out, re.S)
        if "registerComponent" in m.group(2) or "const Canvas" in m.group(2)
    ]
    if not matches:
        matches = list(re.finditer(r"<script([^>]*)>(.*?)</script>", out, re.S))
        if len(matches) < 2:
            raise ValueError("inline app script not found")
        m = matches[-1]
    else:
        m = matches[0]
    return out[: m.start(2)] + js + out[m.end(2) :]


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


def build_export_shell(force: bool = True) -> Path:
    """正本 editor.html から canvas-only を生成し、minify して index.export.html を書く。"""
    canvas_html = build_canvas_html()
    css, js = _extract_parts(canvas_html)
    if not js:
        raise RuntimeError("editor.html（strip 後）にアプリ script がありません")

    with tempfile.TemporaryDirectory() as td:
        js_in = Path(td) / "app.js"
        js_out = Path(td) / "app.min.js"
        js_in.write_text(js, encoding="utf-8")
        _run_cmd(
            [
                "npx",
                "--yes",
                "esbuild",
                str(js_in),
                f"--outfile={js_out}",
                "--minify",
                "--legal-comments=none",
                "--target=es2020",
            ]
        )
        css_min = _run_cmd(["npx", "--yes", "clean-css-cli", "-O2"], stdin_text=css)
        js_min_text = js_out.read_text(encoding="utf-8")
        css_min_text = css_min.decode("utf-8")

    min_html = _rebuild_html(canvas_html, css_min_text, js_min_text)
    if force or not EXPORT_SHELL.is_file():
        EXPORT_SHELL.write_text(min_html, encoding="utf-8")
    return EXPORT_SHELL


if __name__ == "__main__":
    out = build_export_shell()
    raw = out.stat().st_size
    src = SOURCE_HTML.stat().st_size
    idx = INDEX_HTML.stat().st_size
    print(f"[+] {INDEX_HTML.name} (canvas-only) = {idx:,} B")
    print(f"[+] {out.name} を生成しました ({raw:,} B, 正本 editor.html {src:,} B より {src - raw:,} B 削減)")

# -*- coding: utf-8 -*-
"""機能同等の minify だけで index.html がどれだけ縮むか（参考値）。"""
import gzip
import re
import subprocess
import sys
import tempfile
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
INDEX = BASE / "index.html"


def extract_parts(html: str):
    styles = re.findall(r"<style>(.*?)</style>", html, re.S)
    scripts = re.findall(r"<script[^>]*>(.*?)</script>", html, re.S)
    return styles[0] if styles else "", scripts[1] if len(scripts) > 1 else ""


def gz(n: bytes) -> int:
    return len(gzip.compress(n, 9))


def run_cmd(cmd: list[str], stdin_text: str | None = None) -> bytes:
    if cmd and cmd[0] == "npx":
        cmd = ["npx.cmd", *cmd[1:]]
    r = subprocess.run(
        cmd,
        input=stdin_text.encode("utf-8") if stdin_text else None,
        capture_output=True,
        cwd=str(BASE),
        shell=False,
    )
    if r.returncode != 0:
        raise RuntimeError(r.stderr.decode("utf-8", errors="replace")[:500])
    return r.stdout


def rebuild_html(html: str, css: str, js: str) -> str:
    out = re.sub(r"<style>.*?</style>", lambda _: f"<style>{css}</style>", html, count=1, flags=re.S)
    matches = list(re.finditer(r"<script([^>]*)>(.*?)</script>", out, re.S))
    if len(matches) < 2:
        return out
    m = matches[1]
    return out[: m.start(2)] + js + out[m.end(2) :]


def main():
    html = INDEX.read_text(encoding="utf-8")
    css, js = extract_parts(html)
    raw_html = html.encode("utf-8")
    raw_js = js.encode("utf-8")
    raw_css = css.encode("utf-8")

    print("=== AI-Canvas build savings (feature-preserving minify only) ===")
    print(f"index.html     raw {len(raw_html):>6} B   gzip {gz(raw_html):>5} B")
    print(f"  inline JS    raw {len(raw_js):>6} B   gzip {gz(raw_js):>5} B")
    print(f"  inline CSS   raw {len(raw_css):>6} B   gzip {gz(raw_css):>5} B")

    with tempfile.TemporaryDirectory() as td:
        js_in = Path(td) / "app.js"
        css_in = Path(td) / "app.css"
        js_out = Path(td) / "app.min.js"
        css_out = Path(td) / "app.min.css"
        js_in.write_text(js, encoding="utf-8")
        css_in.write_text(css, encoding="utf-8")

        # esbuild: minify, no bundle (single file) — limited tree-shake
        run_cmd(
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
        js_min = js_out.read_bytes()

        # clean-css-cli
        css_min = run_cmd(
            ["npx", "--yes", "clean-css-cli", "-O2"],
            stdin_text=css,
        )

    html_min = rebuild_html(html, css_min.decode("utf-8"), js_min.decode("utf-8"))
    raw_min = html_min.encode("utf-8")

    print()
    print("After esbuild (JS) + clean-css (CSS), re-inlined:")
    print(f"index.html     raw {len(raw_min):>6} B   gzip {gz(raw_min):>5} B")
    print(f"  inline JS    raw {len(js_min):>6} B   gzip {gz(js_min):>5} B")
    print(f"  inline CSS   raw {len(css_min):>6} B   gzip {gz(css_min):>5} B")
    saved = len(raw_html) - len(raw_min)
    pct = 100.0 * saved / len(raw_html)
    saved_gz = gz(raw_html) - gz(raw_min)
    pct_gz = 100.0 * saved_gz / gz(raw_html)
    print()
    print(f"Saved (raw):  {saved} B  ({pct:.1f}%)")
    print(f"Saved (gzip): {saved_gz} B  ({pct_gz:.1f}%)")

    # terser compare (mangle)
    with tempfile.TemporaryDirectory() as td2:
        ji = Path(td2) / "app.js"
        jo = Path(td2) / "app.min.js"
        ji.write_text(js, encoding="utf-8")
        run_cmd(
            [
                "npx",
                "--yes",
                "terser",
                str(ji),
                "-o",
                str(jo),
                "--compress",
                "passes=2",
                "--mangle",
            ]
        )
        js_terser = jo.read_bytes()
    html_terser = rebuild_html(html, css_min.decode("utf-8"), js_terser.decode("utf-8"))
    raw_terser = html_terser.encode("utf-8")
    print()
    print("After terser+mangle (JS) + clean-css (CSS):")
    print(f"index.html     raw {len(raw_terser):>6} B   gzip {gz(raw_terser):>5} B")
    print(f"Saved vs orig (raw):  {len(raw_html)-len(raw_terser)} B ({100*(len(raw_html)-len(raw_terser))/len(raw_html):.1f}%)")
    print(f"Saved vs orig (gzip): {gz(raw_html)-gz(raw_terser)} B ({100*(gz(raw_html)-gz(raw_terser))/gz(raw_html):.1f}%)")

    # export with demo DSL size
    export_path = BASE / "_size_check.html"
    if export_path.exists():
        exp = export_path.read_bytes()
        print()
        print(f"CLI export sample raw {len(exp)} B gzip {gz(exp)} B (+DSL delta vs index)")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("ERROR:", e, file=sys.stderr)
        sys.exit(1)

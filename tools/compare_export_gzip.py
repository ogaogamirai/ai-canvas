# -*- coding: utf-8 -*-
import gzip
import re
import sys
import tempfile
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE / "tools"))
from measure_build_savings import extract_parts, rebuild_html, run_cmd

DSL_PAT = re.compile(r"window\.__INITIAL_CANVAS_DSL__\s*=\s*`([^`]*)`;", re.S)


def main():
    html = (BASE / "index.html").read_text(encoding="utf-8")
    exp_path = BASE / "_size_check.html"
    if not exp_path.exists():
        print("run canvas_cli export first")
        return
    exp = exp_path.read_text(encoding="utf-8")
    dsl = DSL_PAT.search(exp).group(1)

    css, js = extract_parts(html)
    td = tempfile.mkdtemp()
    ji = Path(td) / "a.js"
    jo = Path(td) / "b.js"
    ji.write_text(js, encoding="utf-8")
    run_cmd(["npx", "terser", str(ji), "-o", str(jo), "--compress", "passes=2", "--mangle"])
    css_min = run_cmd(["npx", "clean-css-cli", "-O2"], stdin_text=css)
    html_min = rebuild_html(html, css_min.decode("utf-8"), jo.read_text(encoding="utf-8"))
    esc = dsl.replace("\\", "\\\\").replace("`", "\\`")
    exp_min = DSL_PAT.sub(f"window.__INITIAL_CANVAS_DSL__ = `{esc}`;", html_min, count=1)

    scenarios = [
        ("A. 現状 export（.html）", exp),
        ("B. minify export（.html）", exp_min),
    ]
    print("=== 実装パターン比較（量子デモ DSL 込み）===\n")
    for label, text in scenarios:
        raw = text.encode("utf-8")
        gz = gzip.compress(raw, 9)
        print(label)
        print(f"  添付するファイル: .html  サイズ {len(raw):,} B ({len(raw)/1024:.1f} KB)")
        print(f"  同じ内容を .html.gz にした場合: {len(gz):,} B ({len(gz)/1024:.1f} KB)")
        print()

    raw_a = exp.encode("utf-8")
    raw_b = exp_min.encode("utf-8")
    gz_a = gzip.compress(raw_a, 9)
    gz_b = gzip.compress(raw_b, 9)
    print("=== 送付形態のイメージ ===")
    print(f"  現状 .html only:           {len(raw_a)/1024:.1f} KB")
    print(f"  現状 .html.gz only:        {len(gz_a)/1024:.1f} KB（受信者は展開が必要）")
    print(f"  minify .html only:         {len(raw_b)/1024:.1f} KB")
    print(f"  minify .html.gz:           {len(gz_b)/1024:.1f} KB")


if __name__ == "__main__":
    main()

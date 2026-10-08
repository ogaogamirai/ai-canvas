# -*- coding: utf-8 -*-
"""
AI-Canvas CLI — 外部AIやターミナルからキャンバスを直接操作するツール
"""

import os
import sys
import json
import argparse

# Windows コンソールでの文字化け・UnicodeEncodeError防止
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(BASE_DIR, "canvas_state.json")
INBOX_DSL = os.path.join(BASE_DIR, "inbox_dsl.txt")

from dsl_normalize import normalize_dsl_text, normalize_state  # noqa: E402


def _read_text_arg(path_or_text: str) -> tuple[str, bool]:
    """ファイルパスなら読込、(本文, from_file)。"""
    if os.path.exists(path_or_text):
        with open(path_or_text, "r", encoding="utf-8") as f:
            return f.read(), True
    return path_or_text, False


def cmd_types(args):
    """index.html に登録されているコンポーネント型を一覧"""
    index_path = os.path.join(BASE_DIR, "index.html")
    if not os.path.exists(index_path):
        print("[-] index.html が見つかりません")
        return
    import re

    with open(index_path, "r", encoding="utf-8") as f:
        html = f.read()
    types = sorted(set(re.findall(r"Canvas\.registerComponent\(\s*['\"]([a-z0-9_-]+)['\"]", html)))
    print("=== AI-Canvas コンポーネント型 ===")
    for t in types:
        print(f"  - {t}")
    print(f"\n({len(types)} 種別)")


def cmd_state(args):
    """現在のキャンバス状態を表示"""
    if not os.path.exists(STATE_FILE):
        print("[-] canvas_state.json が存在しません（キャンバス未起動または未保存）")
        return
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    print(f"=== 🎨 AI-Canvas 現在の状態 (更新: {data.get('timestamp')}) ===")
    print(f"■ オブジェクト ({len(data.get('objects', []))}件):")
    for o in data.get("objects", []):
        print(f"  - [{o.get('type')}] id='{o.get('id')}' at (x={o.get('x')}, y={o.get('y')})")
        if o.get("type") == "math":
            print(f"      latex: {o.get('data', {}).get('latex')}")
        elif o.get("type") == "text":
            cnt = o.get('data', {}).get('content') or ""
            print(f"      content: {cnt[:35]}...")
        elif o.get("type") == "card":
            print(f"      title: {o.get('data', {}).get('title')}")
            
    print(f"\n■ エッジ接続 ({len(data.get('edges', []))}本):")
    for e in data.get("edges", []):
        print(f"  - {e.get('u')} ➔ {e.get('v')} (label='{e.get('label')}')")


def cmd_show(args):
    """DSL テキストまたはファイルをキャンバスへ投入"""
    content, from_file = _read_text_arg(args.dsl_or_path)
    if getattr(args, "normalize", False):
        content, n = normalize_dsl_text(content)
        if n:
            print(f"[normalize] {n} 行を修正しました（投入前）")

    with open(INBOX_DSL, "w", encoding="utf-8") as f:
        f.write(content.strip())
    print("[+] inbox_dsl.txt へ書き込みました。開いているキャンバスが自動更新されます！")


def cmd_normalize(args):
    """DSL または canvas_state.json の LaTeX/detail を正規化"""
    path = args.input_path
    if not os.path.exists(path):
        print(f"[-] ファイルが見つかりません: {path}")
        sys.exit(1)

    with open(path, "r", encoding="utf-8") as f:
        raw = f.read()

    if path.endswith(".json") or args.format == "state":
        try:
            state = json.loads(raw)
        except json.JSONDecodeError as e:
            print(f"[-] JSON 解析失敗: {e}")
            sys.exit(1)
        new_state, n = normalize_state(state)
        if n == 0:
            print("[=] 変更なし（既に正規化済み）")
            if args.check:
                sys.exit(0)
        else:
            print(f"[+] {n} オブジェクトの latex/detail を正規化")
        out_text = json.dumps(new_state, ensure_ascii=False, indent=2) + "\n"
    else:
        out_text, n = normalize_dsl_text(raw)
        if n == 0:
            print("[=] 変更なし（既に正規化済み）")
            if args.check:
                sys.exit(0)
        else:
            print(f"[+] {n} 行を正規化")

    if args.check:
        sys.exit(1 if n else 0)

    if args.in_place:
        out_path = path
    elif args.output:
        out_path = args.output
    else:
        sys.stdout.write(out_text)
        return

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(out_text)
    print(f"[+] 保存しました ➔ {out_path}")


def cmd_clear(args):
    """キャンバスを全消去してリセット"""
    with open(INBOX_DSL, "w", encoding="utf-8") as f:
        f.write("clear")
    print("[+] キャンバスのクリア指示を送信しました！")


def cmd_reload(args):
    """キャンバス画面をリロード"""
    with open(INBOX_DSL, "w", encoding="utf-8") as f:
        f.write("reload")
    print("[+] キャンバスのリロード指示を送信しました！")


def cmd_build_export(args):
    """正本 index.html から export 用 minify シェル index.export.html を再生成"""
    from export_shell import build_export_shell

    try:
        path = build_export_shell()
    except RuntimeError as e:
        print(f"[-] ビルド失敗: {e}")
        print("    Node.js と npx が利用可能か確認してください。")
        return
    src = os.path.getsize(os.path.join(BASE_DIR, "index.html"))
    raw = path.stat().st_size
    print(f"[+] {path.name} を更新しました ({raw:,} B, 正本より {src - raw:,} B 削減)")


def cmd_export(args):
    """minify シェル（index.export.html）+ 埋め込み DSL で単体 HTML を生成"""
    import time

    from export_shell import inject_dsl_into_html, read_export_shell

    html_code = read_export_shell()

    dsl_content = ""
    for path in (INBOX_DSL, os.path.join(BASE_DIR, "quantum_demo.txt")):
        if not os.path.exists(path):
            continue
        with open(path, "r", encoding="utf-8") as f:
            dsl_content = f.read().strip()
        if dsl_content and dsl_content.lower() not in ("clear", "reload", "refresh"):
            break

    try:
        standalone_html = inject_dsl_into_html(html_code, dsl_content)
    except ValueError as e:
        print(f"[-] {e}")
        return

    out_name = args.output or f"ai_canvas_snapshot_{time.strftime('%Y%m%d_%H%M%S')}.html"
    out_path = os.path.join(BASE_DIR, out_name)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(standalone_html)

    # Windows ダウンロードフォルダにも同時配置
    downloads_dir = os.path.join(os.path.expanduser("~"), "Downloads")
    if os.path.exists(downloads_dir):
        dl_path = os.path.join(downloads_dir, "ai_canvas_snapshot.html")
        with open(dl_path, "w", encoding="utf-8") as f:
            f.write(standalone_html)
        print(f"[+] ダウンロードフォルダへ保存完了 ➔ {dl_path}")

    print(f"[+] 完全自己完結した単体HTMLを保存しました ➔ {out_path}")


def main():
    parser = argparse.ArgumentParser(description="AI-Canvas CLI Controller")
    subparsers = parser.add_subparsers(dest="command")

    # state
    subparsers.add_parser("state", help="キャンバスの現在配置・内容を確認")
    subparsers.add_parser("types", help="登録コンポーネント型の一覧")

    # show
    p_show = subparsers.add_parser("show", help="DSLテキストまたはファイルをキャンバスへ投入")
    p_show.add_argument("dsl_or_path", help="DSL文字列 または .txt ファイルパス")
    p_show.add_argument(
        "-n",
        "--normalize",
        action="store_true",
        help="投入前に latex/detail のバックスラッシュを正規化（推奨）",
    )

    p_norm = subparsers.add_parser(
        "normalize",
        help="DSL .txt または canvas_state.json の数式・detail を正規化",
    )
    p_norm.add_argument("input_path", help="入力ファイル (.txt / .json)")
    p_norm.add_argument("-o", "--output", help="出力先（未指定時は標準出力）")
    p_norm.add_argument(
        "--in-place",
        action="store_true",
        help="入力ファイルを上書き保存",
    )
    p_norm.add_argument(
        "--check",
        action="store_true",
        help="変更がある場合のみ終了コード 1（CI 用）",
    )
    p_norm.add_argument(
        "--format",
        choices=("auto", "dsl", "state"),
        default="auto",
        help="auto: 拡張子で判定",
    )

    # clear
    subparsers.add_parser("clear", help="キャンバスの全ノードを消去してリセット")

    # reload
    subparsers.add_parser("reload", help="キャンバス画面を再読み込み (ホットリロード)")

    # export
    p_exp = subparsers.add_parser("export", help="現在の状態から完全単体HTMLを生成")
    p_exp.add_argument("-o", "--output", help="出力ファイル名", default=None)

    subparsers.add_parser(
        "build-export",
        help="index.export.html を正本から minify 再生成（index.html 変更後に実行）",
    )

    args = parser.parse_args()
    if args.command == "state":
        cmd_state(args)
    elif args.command == "types":
        cmd_types(args)
    elif args.command == "show":
        cmd_show(args)
    elif args.command == "normalize":
        cmd_normalize(args)
    elif args.command == "clear":
        cmd_clear(args)
    elif args.command == "reload":
        cmd_reload(args)
    elif args.command == "export":
        cmd_export(args)
    elif args.command == "build-export":
        cmd_build_export(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

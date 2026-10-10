# -*- coding: utf-8 -*-
"""
AI-Canvas DSL Editor (canonical cockpit)

Windows WebView2 IPC 直結により、ローカルサーバーゼロで
人間がキーボードと思考のスピードで DSL を直打ちし、リアルタイムに AI-Canvas を操ります。

設計メモ:
- 正本エンジンは `editor.html`。`index.html` / `index.export.html` は export_shell が生成する。
- `webview` は遅延 import（GUI を伴わない純ロジックのテストを webview 未導入でも可能にする）。
- 旧 `canvas_app.py` の JS 契約（sync_canvas_state / get_export_shell）を後方互換で満たす。
"""

import json
import os
import sys
import threading
import time


# --- Windows コンソール / pythonw (ウィンドウモード) での入出力安全化 ---
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w", encoding="utf-8")
else:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

if sys.stderr is None:
    sys.stderr = open(os.devnull, "w", encoding="utf-8")
else:
    try:
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HTML_PATH = os.path.join(BASE_DIR, "editor.html")
STATE_FILE = os.path.join(BASE_DIR, "canvas_state.json")
INBOX_DSL = os.path.join(BASE_DIR, "inbox_dsl.txt")


def _reveal_in_explorer(path):
    """Windows のみ: エクスプローラーで対象ファイルを選択表示（他OS・失敗は黙殺）。

    AI_CANVAS_NO_REVEAL=1 で抑止（テスト・CI 用）。
    """
    if sys.platform != "win32" or os.environ.get("AI_CANVAS_NO_REVEAL"):
        return
    try:
        import subprocess

        subprocess.Popen(f'explorer /select,"{path}"')
    except Exception:
        pass


class CanvasAPI:
    """JavaScript から直接呼ばれる Python 側の受信用 API（WebView2 IPC 直結）。"""

    def get_startup_content(self):
        """起動・ホットリロード後に JS から呼ぶ復元用ペイロード。

        優先順: canvas_state.json（保存済み状態）→ inbox_dsl.txt → quantum_demo.txt。
        """
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, "r", encoding="utf-8") as f:
                    state = json.load(f)
                if state.get("objects"):
                    return {"mode": "state", "payload": state}
            except (json.JSONDecodeError, OSError) as e:
                print(f"[起動復元] canvas_state.json 読込スキップ: {e}")

        for label, path in (
            ("inbox", INBOX_DSL),
            ("demo", os.path.join(BASE_DIR, "quantum_demo.txt")),
        ):
            if not os.path.exists(path):
                continue
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
            except OSError as e:
                print(f"[起動復元] {label} 読込スキップ: {e}")
                continue
            if content.strip():
                return {"mode": "dsl", "payload": content, "source": label}

        return {"mode": "empty"}

    def get_export_shell(self):
        """単体 HTML 用テンプレート（index.export.html の minify 版があれば優先）。"""
        from export_shell import read_export_shell

        return read_export_shell()

    def sync_canvas_state(self, moved_id=None, moved_type=None, x=0, y=0, state=None):
        """キャンバス側の操作を canvas_state.json に即時保存（双方向同期）。

        旧 canvas_app.py の JS 契約。moved_id=="__EXPORT_HTML__" は export 経路。
        state は pywebview により dict で渡る。
        """
        if moved_id == "__EXPORT_HTML__":
            raw_html = (state or {}).get("raw_html", "")
            if raw_html:
                return self.export_html(raw_html)
            return False

        if not isinstance(state, dict):
            return False

        try:
            with open(STATE_FILE, "w", encoding="utf-8") as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
            node_count = len(state.get("objects", []))
            edge_count = len(state.get("edges", []))
            print(
                f"\r[状態自動保存 💾] {node_count} ノード / {edge_count} エッジ を "
                f"canvas_state.json に同期",
                end="",
                flush=True,
            )
            return "ok"
        except Exception as e:
            print(f"[状態保存エラー ⚠️] {e}")
            return str(e)

    def sync_state(self, state_json):
        """後方互換: JSON 文字列 または dict で state を受けて保存。"""
        try:
            state = json.loads(state_json) if isinstance(state_json, str) else state_json
        except (json.JSONDecodeError, TypeError) as e:
            return str(e)
        return self.sync_canvas_state(None, None, 0, 0, state)

    def save_dsl(self, dsl_content):
        """DSL テキストのネイティブファイル保存（BASE_DIR および Downloads + Explorer 表示）。"""
        try:
            filename = f"canvas_dsl_{time.strftime('%Y%m%d_%H%M%S')}.dsl"
            save_path = os.path.join(BASE_DIR, filename)
            with open(save_path, "w", encoding="utf-8") as f:
                f.write(dsl_content)

            downloads_dir = os.path.join(os.path.expanduser("~"), "Downloads")
            if os.path.exists(downloads_dir):
                with open(os.path.join(downloads_dir, filename), "w", encoding="utf-8") as f:
                    f.write(dsl_content)

            _reveal_in_explorer(save_path)
            return f"保存完了: {filename}"
        except Exception as e:
            return f"保存失敗: {e}"

    def open_dsl_file(self):
        """ネイティブファイル選択ダイアログで DSL/TXT を開き、内容を返す。"""
        try:
            webview = _import_webview()
            windows = webview.windows
            if windows:
                file_types = ("DSL files (*.dsl;*.txt)", "All files (*.*)")
                res = windows[0].create_file_dialog(
                    webview.OPEN_DIALOG, allow_multiple=False, file_types=file_types
                )
                if res and len(res) > 0:
                    with open(res[0], "r", encoding="utf-8") as f:
                        content = f.read()
                    return {
                        "success": True,
                        "content": content,
                        "filename": os.path.basename(res[0]),
                    }
            return {"success": False, "cancelled": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def export_html(self, html_content):
        """単体自己完結 HTML を保存（BASE_DIR および Downloads + Explorer 表示）。"""
        try:
            filename = f"ai_canvas_snapshot_{time.strftime('%Y%m%d_%H%M%S')}.html"
            save_path = os.path.join(BASE_DIR, filename)
            with open(save_path, "w", encoding="utf-8") as f:
                f.write(html_content)

            downloads_dir = os.path.join(os.path.expanduser("~"), "Downloads")
            if os.path.exists(downloads_dir):
                with open(os.path.join(downloads_dir, filename), "w", encoding="utf-8") as f:
                    f.write(html_content)

            _reveal_in_explorer(save_path)
            return f"保存完了: {filename}"
        except Exception as e:
            return f"保存失敗: {e}"


def _import_webview():
    """webview は遅延 import（未導入環境でもこのモジュールの import を壊さない）。"""
    import webview

    return webview


def external_watcher(window):
    """editor.html のホットリロード + inbox_dsl.txt からの外部 DSL 投入を監視。

    `canvas_cli.py show` 等が書く inbox_dsl.txt を検知し、開いている画面へ即時反映する。
    """
    last_html_mtime = os.path.getmtime(HTML_PATH) if os.path.exists(HTML_PATH) else 0
    # 起動時の inbox 既存内容は get_startup_content が扱うため、現在値を起点にする
    last_inbox_mtime = os.path.getmtime(INBOX_DSL) if os.path.exists(INBOX_DSL) else 0

    while True:
        try:
            if os.path.exists(HTML_PATH):
                html_mtime = os.path.getmtime(HTML_PATH)
                if html_mtime > last_html_mtime:
                    last_html_mtime = html_mtime
                    window.evaluate_js("location.reload();")

            if os.path.exists(INBOX_DSL):
                inbox_mtime = os.path.getmtime(INBOX_DSL)
                if inbox_mtime > last_inbox_mtime:
                    last_inbox_mtime = inbox_mtime
                    with open(INBOX_DSL, "r", encoding="utf-8") as f:
                        dsl = f.read().strip()
                    if dsl:
                        low = dsl.lower()
                        if low in ("reload", "refresh"):
                            window.evaluate_js("location.reload();")
                        elif low in ("export", "save"):
                            window.evaluate_js("Canvas.exportHTML();")
                        else:
                            window.evaluate_js(
                                "window.__applyCanvasDslFromHost(" + json.dumps(dsl) + ");"
                            )
        except Exception:
            pass
        time.sleep(0.5)


def main():
    webview = _import_webview()

    print("=" * 65)
    print("📝 AI-Canvas DSL Editor — Serverless Live Thinking Cockpit")
    print("=" * 65)
    print(f"正本パス : {BASE_DIR}")
    print(f"エンジン正本 : {HTML_PATH}")
    print("通信方式 : Windows WebView2 IPC 直結 (ポート使用ゼロ)")
    print("=" * 65)

    api = CanvasAPI()
    window = webview.create_window(
        title="AI-Canvas DSL Editor (Live Cockpit)",
        url=HTML_PATH,
        js_api=api,
        width=1280,
        height=800,
        background_color="#0b0f19",
    )

    t_watcher = threading.Thread(target=external_watcher, args=(window,), daemon=True)
    t_watcher.start()

    webview.start(debug=False)
    print("\n[終了 🌿] DSL Editor を終了しました。")


if __name__ == "__main__":
    main()

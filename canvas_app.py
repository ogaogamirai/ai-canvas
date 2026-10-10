# -*- coding: utf-8 -*-
"""
AI-Canvas — Serverless Interactive Thinking Canvas (Main App)
Windows WebView2 IPC直結により、ローカルサーバーゼロで
AIと人間が思考・数式・テキスト・図解をリアルタイムに共創・共有します。
"""

import os
import sys
import time
import json
import threading

# Windows コンソールおよび pythonw (ウィンドウモード) での入出力安全化
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

import webview

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HTML_PATH = os.path.join(BASE_DIR, "index.html")
STATE_FILE = os.path.join(BASE_DIR, "canvas_state.json")
INBOX_DSL = os.path.join(BASE_DIR, "inbox_dsl.txt")


class CanvasAPI:
    """JavaScriptから直接呼ばれるPython側の受信用API (IPC直結)"""

    def get_startup_content(self):
        """WebView 起動・index.html ホットリロード後に JS から呼ぶ復元用ペイロード。"""
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
                    dsl = f.read().strip()
            except OSError:
                continue
            low = dsl.lower()
            if dsl and low not in ("clear", "reset", "reload", "refresh", "export", "save"):
                return {"mode": "dsl", "payload": dsl, "source": label}

        return {"mode": "empty"}

    def get_export_shell(self):
        """単体 HTML 用テンプレート（index.export.html があれば minify 版）"""
        from export_shell import read_export_shell

        return read_export_shell()

    def sync_canvas_state(self, moved_id, moved_type, x, y, state):
        if moved_id == "__EXPORT_HTML__":
            raw_html = state.get("raw_html", "")
            if raw_html:
                return self.export_html(raw_html)
            return False

        if moved_id:
            print(f"\n[AI検知 🎯] キャプテンが 【{moved_type}】 '{moved_id}' を移動しました！ -> 座標: (x={x:.1f}, y={y:.1f})")
        
        try:
            with open(STATE_FILE, "w", encoding="utf-8") as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
            obj_count = len(state.get("objects", []))
            edge_count = len(state.get("edges", []))
            print(f"[状態保存 💾] canvas_state.json を更新しました（オブジェクト: {obj_count}件, エッジ: {edge_count}本）")
            return True
        except Exception as e:
            print(f"[保存エラー ⚠️] {e}")
            return False

    def export_html(self, html_content):
        """WebView2からの単体HTML保存リクエストをネイティブファイルとして安全に保存"""
        try:
            import subprocess
            filename = f"ai_canvas_snapshot_{time.strftime('%Y%m%d_%H%M%S')}.html"
            save_path = os.path.join(BASE_DIR, filename)
            with open(save_path, "w", encoding="utf-8") as f:
                f.write(html_content)

            # Windows ダウンロードフォルダにも同時に配置
            downloads_dir = os.path.join(os.path.expanduser("~"), "Downloads")
            if os.path.exists(downloads_dir):
                dl_path = os.path.join(downloads_dir, filename)
                with open(dl_path, "w", encoding="utf-8") as f:
                    f.write(html_content)
                print(f"[ダウンロード配置 📥] {dl_path}")

            # エクスプローラーで保存先ファイルを選択して自動ポップアップ
            subprocess.Popen(f'explorer /select,"{save_path}"')

            print(f"\n[エクスポート 💾] 単体HTMLを保存しました ➔ {save_path}")
            return f"保存完了: {filename} (ダウンロード & 正本フォルダ)"
        except Exception as e:
            print(f"[エクスポート失敗 ⚠️] {e}")
            return f"保存失敗: {e}"

    def save_dsl(self, dsl_content):
        """DSLテキストのネイティブファイル保存"""
        try:
            import subprocess
            filename = f"canvas_dsl_{time.strftime('%Y%m%d_%H%M%S')}.dsl"
            save_path = os.path.join(BASE_DIR, filename)
            with open(save_path, "w", encoding="utf-8") as f:
                f.write(dsl_content)

            downloads_dir = os.path.join(os.path.expanduser("~"), "Downloads")
            if os.path.exists(downloads_dir):
                dl_path = os.path.join(downloads_dir, filename)
                with open(dl_path, "w", encoding="utf-8") as f:
                    f.write(dsl_content)

            subprocess.Popen(f'explorer /select,"{save_path}"')
            print(f"\n[DSL保存 💾] DSLファイルを保存しました ➔ {save_path}")
            return f"保存完了: {filename}"
        except Exception as e:
            print(f"[DSL保存失敗 ⚠️] {e}")
            return f"保存失敗: {e}"

    def open_dsl_file(self):
        """ネイティブファイル選択ダイアログでDSL/TXTファイルを開く"""
        try:
            import webview
            windows = webview.windows
            if windows:
                file_types = ('DSL files (*.dsl;*.txt)', 'All files (*.*)')
                res = windows[0].create_file_dialog(webview.OPEN_DIALOG, allow_multiple=False, file_types=file_types)
                if res and len(res) > 0:
                    chosen_path = res[0]
                    with open(chosen_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    filename = os.path.basename(chosen_path)
                    return {"success": True, "content": content, "filename": filename}
            return {"success": False, "cancelled": True}
        except Exception as e:
            return {"success": False, "error": str(e)}


def external_inbox_watcher(window):
    """外部AIからの DSL 投入ファイル (inbox_dsl.txt) および index.html の変更を常時監視してホットリロード"""
    last_inbox_mtime = 0
    last_html_mtime = os.path.getmtime(HTML_PATH) if os.path.exists(HTML_PATH) else 0

    while True:
        try:
            # 1. index.html のホットリロード検知 (サーバーレス・ライブリロード)
            if os.path.exists(HTML_PATH):
                html_mtime = os.path.getmtime(HTML_PATH)
                if html_mtime > last_html_mtime:
                    last_html_mtime = html_mtime
                    print("\n[ホットリロード 🔄] index.html の更新を検知しました！画面を再読み込みします...")
                    window.evaluate_js("location.reload();")

            # 2. inbox_dsl.txt からのDSL投入検知
            if os.path.exists(INBOX_DSL):
                inbox_mtime = os.path.getmtime(INBOX_DSL)
                if inbox_mtime > last_inbox_mtime:
                    last_inbox_mtime = inbox_mtime
                    with open(INBOX_DSL, "r", encoding="utf-8") as f:
                        dsl_content = f.read().strip()
                    
                    if dsl_content:
                        if dsl_content.lower() in ["reload", "refresh"]:
                            print("\n[外部指示 🔄] 画面のリロード指示を受信しました！")
                            window.evaluate_js("location.reload();")
                        elif dsl_content.lower() in ["export", "save"]:
                            print("\n[外部指示 💾] 単体HTMLのエクスポート指示を受信しました！")
                            window.evaluate_js("Canvas.exportHTML();")
                        else:
                            print(f"\n[外部投入 📥] inbox_dsl.txt から新しいDSLを受信しました！キャンバスへ展開中...")
                            # テンプレートリテラルは \nu 等が改行化して DSL が壊れるため JSON 経由で渡す
                            js = (
                                "window.__applyCanvasDslFromHost("
                                + json.dumps(dsl_content)
                                + ");"
                            )
                            window.evaluate_js(js)
                            print("[展開完了 ✨] キャンバスに新しい図と論理関係を描画しました！\n")
        except Exception as e:
            print(f"[監視エラー] {e}")
        time.sleep(0.5)


def initial_demo_stream(window):
    """初期起動時のデモ投影 (光量子仮説〜ド・ブロイの完全7ノードを一発投入)"""
    time.sleep(1.5)
    demo_path = os.path.join(BASE_DIR, "quantum_demo.txt")
    if os.path.exists(demo_path):
        with open(demo_path, "r", encoding="utf-8") as f:
            initial_dsl = f.read().strip()
    else:
        initial_dsl = """
clear
card: origin [title="光の本質とは何か？", sub="キャプテンの問い", color="#c084fc"]
math: einstein [title="EINSTEIN (1905)", latex="E_{max} = h\\nu - W_0", to="origin", link="定式化"]
text: insight [title="光量子仮説の本質", content="光の強度ではなく「振動数」が電子の脱出エネルギーを決める。光はエネルギーの塊（光子）として振る舞う。", to="einstein", link="物理的意味"]
svg: model [title="衝突メカニズム", svg_content="<circle cx='0' cy='0' r='18' fill='#38bdf8' opacity='0.3'/><circle cx='0' cy='0' r='10' fill='#38bdf8'/><path d='M -35 -20 Q -15 -35 5 -20 T 45 -20' fill='none' stroke='#f59e0b' stroke-width='2.5'/><circle cx='28' cy='22' r='6' fill='#ec4899'/><text x='0' y='38' font-size='9' fill='#94a3b8' text-anchor='middle'>光子(hν) ➔ 放出</text>", to="origin", link="幾何モデル"]
card: debroglie_card [title="物質波の提唱", sub="ド・ブロイ (1924)", color="#38bdf8", to="origin", link="波粒子二重性"]
math: debroglie_eq [title="DE BROGLIE (1924)", latex="\\lambda = \\frac{h}{p}", to="debroglie_card", link="波長と運動量"]
text: matter_wave [title="二重性の拡張", content="光が粒子のように振る舞うなら、電子などの物質粒子もまた波としての性質を持つはずだ。", to="debroglie_eq", link="理論的帰結"]
"""
    with open(INBOX_DSL, "w", encoding="utf-8") as f:
        f.write(initial_dsl.strip())


def main():
    print("=" * 65)
    print("🎨 AI-Canvas — Serverless Interactive Thinking Canvas")
    print("=" * 65)
    print(f"正本パス : {BASE_DIR}")
    print(f"状態ファイル : {STATE_FILE}")
    print(f"外部投入口 : {INBOX_DSL}")
    print("通信方式 : Windows WebView2 IPC直結 (ローカルサーバー/ポート使用ゼロ)")
    print("=" * 65)
    print("AI-Canvas を起動します...\n")

    api = CanvasAPI()
    window = webview.create_window(
        title="AI-Canvas — Serverless Interactive Thinking Canvas",
        url=HTML_PATH,
        js_api=api,
        width=1080,
        height=720,
        background_color="#0b0f19"
    )

    # 外部受信タスクの開始
    t_watcher = threading.Thread(target=external_inbox_watcher, args=(window,), daemon=True)
    t_watcher.start()

    # 初期デモ投影
    t_demo = threading.Thread(target=initial_demo_stream, args=(window,), daemon=True)
    t_demo.start()

    webview.start(debug=False)

    print("\n[終了 🌿] AI-Canvas を終了しました。プロセス残骸ゼロ。")


if __name__ == "__main__":
    main()

# AI-Canvas v1.0 — 完成リリース（2026-10-09）

> **正本**: `G:\マイドライブ\Tools\ai-canvas`  
> **台帳**: `Tools/DRIVE_REGISTRY_v01.md`（id: `ai-canvas`）  
> **状態**: 三家・Captain 向け **運用可能な完成形**（サーバーレス・双方向同期・単体 HTML 配布）

> **v1.1（2026-10-10・Nova 整備）**: DSL Editor（人間コックピット）を本実装。エンジン正本を
> `editor.html` に一本化し、`index.html` / `index.export.html` はビルド生成物に。IPC 契約
> （`sync_canvas_state` / `get_export_shell`）を修復、重複死コード除去、回帰テスト拡充。

---

## v1 でできること

| 領域 | 内容 |
|------|------|
| **起動** | WebView2・ポートゼロ（`start_canvas.bat` / `canvas_app.py`） |
| **表現** | card / math / text / svg / table / sticky / group |
| **接続** | DSL `to` + 任意エッジ色・太さ・破線（`edge_*` / `edge:` 行） |
| **詳細** | 右パネル Markdown・表・KaTeX・ノード間ジャンプ |
| **AI 連携** | `inbox_dsl.txt` ホット投入、`canvas_cli.py`、`canvas_state.json` 同期 |
| **正規化** | `canvas_cli.py normalize`（`latex` / `detail`） |
| **配布** | GUI / CLI **export** — minify シェル + Base64 埋め込み DSL（約 55 KB 級・量子デモ） |

---

## クイックスタート（人間）

1. `start_canvas.bat` をダブルクリック  
2. 初回は `quantum_demo.txt` が inbox 経由で投影される  
3. ノードをドラッグ・クリックで詳細パネル・`?` でヘルプ  

## クイックスタート（AI / エージェント）

```bash
cd G:\マイドライブ\Tools\ai-canvas
python -X utf8 canvas_cli.py normalize my_draft.txt -o my_draft_fixed.txt
python -X utf8 canvas_cli.py show my_draft_fixed.txt
```

キャンバスは **起動済み**であること。DSL 仕様は [README.md](../README.md) §4。

---

## メンテナ（`editor.html` を直した人）

```bash
python -X utf8 canvas_cli.py build-export   # index.html / index.export.html を再生成
python -X utf8 -m unittest discover -q
```

- **エンジン正本は `editor.html`**（キャンバス + DSL Editor）  
- `index.html` / `index.export.html` は **生成物**（直接編集しない）  
- 人間コックピットは `start_editor.bat` / `editor_app.py`、canvas-only は `start_canvas.bat` / `canvas_app.py`  
- **export** は `index.export.html`（無いとき `index.html` にフォールバック）  

---

## v1 で意図的に含めないもの

- 常駐 HTTP / WebSocket  
- Phase 2 相当の複雑エッジ描画（二重線・直交ルーティング等はロールバック済み）  
- export 用 gzip（添付は minify `.html` で十分と判断）  

将来案は [BRUSHUP_ROADMAP.md](BRUSHUP_ROADMAP.md)。

---

## GitHub 正本（確定 2026-10-09）

- **リポジトリ**: [ogaogamirai/ai-canvas](https://github.com/ogaogamirai/ai-canvas)（public・**共有の正本**）
- **閉じ役**: Nova（[`GITHUB_CLOSER_ROLES_v01.md`](../../GITHUB_CLOSER_ROLES_v01.md) v01.7）
- ローカル `G:\マイドライブ\Tools\ai-canvas` で編集 → `commit` → `push origin master` で確定。push されるまで他 AP は正本とみなさない。

---

## 変更履歴（要約）

- エッジ Phase 1（色・太さ・破線・state 保存）  
- 詳細パネル Markdown 表（`CanvasTable`）  
- export: DOM clone 廃止 → シェル + DSL、minify シェル、Base64 埋め込み（`;` / `\nu` 安全）  
- inbox 投入: JSON 経由（`__applyCanvasDslFromHost`）  
- テスト: `unittest discover`（13 件目安）  

---

## 参照

- [USER_GUIDE.md](USER_GUIDE.md) — 共有・トラブルシュート  
- [README.md](../README.md) — DSL・CLI 一覧  

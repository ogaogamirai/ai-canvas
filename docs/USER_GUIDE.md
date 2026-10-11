# AI-Canvas — 共有利用ガイド（v1.1）

三家・Captain が同じ手順で使うための短い正本です。詳細 DSL は [`docs/DSL.md`](DSL.md)、開発者向けは [README.md](../README.md)。

---

## 1. どこにあるか

| 項目 | 値 |
|------|-----|
| ローカル正本 | `G:\マイドライブ\Tools\ai-canvas` |
| GitHub 正本 | [ogaogamirai/ai-canvas](https://github.com/ogaogamirai/ai-canvas) |
| ブラウザデモ | https://ogaogamirai.github.io/ai-canvas/ai-canvas.html |
| 台帳 id | `ai-canvas`（`Tools/DRIVE_REGISTRY_v01.md`） |
| **起動（推奨）** | **`start_editor.bat`** — 左 DSL / 右キャンバスの統合コックピット |
| 起動（canvas のみ） | `start_canvas.bat` — 旧経路・プレビュー用 |

**手で編集する正本**: `src/`（`template.html` / `styles.css` / `editor.css` / `canvas.js` / `editor.js`）。  
変更後は必ず `python -X utf8 canvas_cli.py build-export` で `ai-canvas.html` / `index.html` / `index.export.html` を再生成。

---

## 2. ファイルの意味（触る／触らない）

| ファイル | 誰が | 説明 |
|----------|------|------|
| `src/*` | 開発 | **唯一の手編集正本** |
| `ai-canvas.html` | ビルド | **DSL Editor 起動用**（canvas + editor） |
| `index.html` | ビルド | canvas-only（配布・軽量プレビュー） |
| `index.export.html` | ビルド | export 用 minify シェル |
| `editor_app.py` | 起動 | WebView2 + IPC（`start_editor.bat`） |
| `canvas_state.json` | 自動 | ドラッグ後の配置・エッジ |
| `inbox_dsl.txt` | AI / CLI | ホット投入（`show`）。Editor 起動中は左ペインも同期 |
| `quantum_demo.txt` | 参照 | デモ DSL 正本 |
| `vendor/katex/` | 同梱 | オフライン数式 |

---

## 3. 人間の基本操作（DSL Editor）

1. `start_editor.bat` を実行（初回: `pip install pywebview`）  
2. 左ペインで DSL を編集 → 右キャンバスが約 20ms デバウンスで追従  
3. キャンバスでドラッグ・詳細編集 → ツールバー **キャンバス→DSL** で左へ戻せる  
4. AI から `canvas_cli.py show` した DSL も inbox 経由で **左右とも** 更新  

---

## 4. AI・エージェント向けフロー

```bash
cd G:\マイドライブ\Tools\ai-canvas
python -X utf8 canvas_cli.py check my_draft.txt
python -X utf8 canvas_cli.py normalize my_draft.txt -o my_draft_fixed.txt
python -X utf8 canvas_cli.py show my_draft_fixed.txt
```

**前提**: `start_editor.bat`（または `editor_app.py`）で **起動済み**。`show` は `inbox_dsl.txt` を更新し、画面へ即反映。

---

## 5. 単体 HTML を渡すとき

1. 内容を整える（Editor または `show`）  
2. メニュー **HTML エクスポート** または `canvas_cli.py export`  
3. 相手に `.html` を渡す  

**成功の目安**: ログに「単体スナップショットを正常に復元しました！」、グラフが表示される。

| 相手の環境 | おすすめ |
|------------|----------|
| ネットあり | `.html` 1 枚（KaTeX CDN フォールバック） |
| オフライン | フォルダ zip（`vendor` 込み） |

**注意**: `src/` を直したら `build-export` → 必要なら再 export。

---

## 6. よくあるトラブル

| 症状 | 原因の例 | 対処 |
|------|----------|------|
| `show` 後真っ黒 | 未起動 / 旧ビルド | `start_editor.bat`・`build-export`・再起動 |
| 左 DSL と右がずれる | キャンバス操作のみ | ツールバー「キャンバス→DSL」または `canvas_cli.py dsl` |
| export が空グラフ | 古い export | 再 export（Base64 埋め込み） |
| 数式が出ない | KaTeX 未読込 | オンライン or `vendor` 同梱 |
| `start_editor` が即終了 | pywebview 未導入 | `start_editor.bat --check` で Python を確認 → `pip install pywebview` |

---

## 7. テスト（変更後）

```bash
cd G:\マイドライブ\Tools\ai-canvas
python -X utf8 canvas_cli.py build-export
python -X utf8 -m unittest discover -q
```

（任意）`node tools/check_*.mjs` — レイアウト・detail 編集などの回帰。

---

## 8. エージェント向けチェックリスト

- [ ] 正本は `Tools/ai-canvas`（家内に複製しない）  
- [ ] コード変更は `src/` → `build-export`  
- [ ] DSL は `check` → `normalize` → `show`  
- [ ] 起動は **`start_editor.bat` 推奨**（AI 連携は `ai-canvas.html` 経路）  
- [ ] push は [GITHUB_CLOSER_ROLES](https://github.com/ogaogamirai/ai-canvas) に従う  

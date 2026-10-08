# AI-Canvas — 共有利用ガイド（v1）

三家・Captain が同じ手順で使うための短い正本です。詳細 DSL は [README.md](../README.md)。

---

## 1. どこにあるか

| 項目 | 値 |
|------|-----|
| ローカル正本 | `G:\マイドライブ\Tools\ai-canvas` |
| 台帳 id | `ai-canvas`（`Tools/DRIVE_REGISTRY_v01.md`） |
| 起動 | `start_canvas.bat` |

**編集するファイル**: 主に `index.html`（本体）、DSL は `*.txt` や AI 生成物を `show` で投入。

---

## 2. ファイルの意味（触る／触らない）

| ファイル | 誰が | 説明 |
|----------|------|------|
| `index.html` | 開発 | 起動・ホットリロード用 **正本** |
| `index.export.html` | ビルド成果 | **export だけ**（`build-export` で更新） |
| `canvas_state.json` | 自動 | ドラッグ後の配置・エッジ（AI が `state` で読める） |
| `inbox_dsl.txt` | AI / CLI | ホット投入ポスト（`show` が書く） |
| `quantum_demo.txt` | 参照 | デモ DSL 正本 |
| `vendor/katex/` | 同梱 | オフライン数式用（export 単体＋オンラインなら未同梱でも可） |

---

## 3. 単体 HTML を渡すとき

1. キャンバスで内容を整える（または `show` で DSL 投入）  
2. メニュー **HTML エクスポート** または `canvas_cli.py export`  
3. 相手に `.html` を渡す  

**成功の目安**: 開いた直後ログに「単体スナップショットを正常に復元しました！」、グラフが表示される。

| 相手の環境 | おすすめ |
|------------|----------|
| ネットあり | `.html` 1 枚で可（KaTeX は CDN フォールバック） |
| オフライン | `ai-canvas` フォルダごと zip（`vendor` 込み） |

**注意**: `index.html` 変更後に export だけ古い場合 → `build-export` を実行してから再 export。

---

## 4. よくあるトラブル

| 症状 | 原因の例 | 対処 |
|------|----------|------|
| `show` 後真っ黒 | inbox JS が壊れた（旧バージョン） | 本体を v1 に更新・再起動 |
| export が空グラフ | 古い export / 埋め込み失敗 | **再 export**（v1 Base64 埋め込み） |
| 数式が出ない | KaTeX 未読込 | オンライン確認 or `vendor` 同梱 |
| エッジが全部グレー | 正本が古い | `index.html` 更新・リロード |
| export が大きい | 長い `detail=` | 正常。minify でエンジンは約 55 KB 級 |

---

## 5. テスト（変更後）

```bash
cd G:\マイドライブ\Tools\ai-canvas
python -X utf8 canvas_cli.py build-export
python -X utf8 -m unittest discover -q
```

---

## 6. エージェント向けチェックリスト

- [ ] 作業前に `DRIVE_REGISTRY` で正本パスを確認  
- [ ] DSL は `normalize` → `show` の二段  
- [ ] `index.html` を直したら `build-export`  
- [ ] コミット・push は閉じ役ルールに従う（Git 化後）  

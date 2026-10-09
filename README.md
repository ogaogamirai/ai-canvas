# AI-Canvas — Serverless Interactive Thinking Canvas

> **v1.0 完成（2026-10-09）** — サーバーレス・双方向同期・minify export・エッジ装飾・詳細 Markdown 表。  
> **共有ガイド**: [`docs/USER_GUIDE.md`](docs/USER_GUIDE.md) / **リリース記録**: [`docs/RELEASE_v1.md`](docs/RELEASE_v1.md)

> **「ローカルサーバーゼロで動く、人間とAIのための多角的思考キャンバス」**  
> 思考カード・KaTeX数式・解説テキスト・動的SVGベクター図形が、超簡易DSLと自動整列によって軽やかに共創される共有空間。

- **ローカル正本**: `G:\マイドライブ\Tools\ai-canvas`
- **台帳**: `Tools/DRIVE_REGISTRY_v01.md`（id: `ai-canvas`）
- **起案**: Eleanor Arroway (Ellie) / Captain GO (2026-10-08)
- **将来案**: [`docs/BRUSHUP_ROADMAP.md`](docs/BRUSHUP_ROADMAP.md)

---

## 1. 核心理念（美学と制約）

1. **ローカルサーバー完全禁止（ゼロ・ポート）**:
   - `http.server` や WebSocket などの常駐デーモンを一切使いません。
   - Windows WebView2 の内部 IPC 直結により、ポート衝突や終了後のプロセス残骸を根絶。
2. **多角的思考表現（Multi-Object）**:
   - 単なる「ノードとエッジ」にとどまらず、**思考カード**、**KaTeX 美麗数式**、**解説テキスト**、**自由ベクター図形（SVG）** が等しく配置され、相互にエッジで結ばれます。
3. **AIの思考負荷ゼロ（Auto-Layout & 簡易DSL）**:
   - AIはピクセル座標 `(x, y)` を考えず、論理関係と内容だけを記述したDSLを投げるだけ。
   - キャンバス側のエンジンが水平（LR）または垂直（TB）に自動で整列します。
4. **完全な双方向性**:
   - 人間がマウスでドラッグ移動した最新の配置と内容は、リアルタイムに `canvas_state.json` に同期され、外部のAIエージェント（エリー等）が即座に把握できます。
   - 外部から `inbox_dsl.txt` または `canvas_cli.py` で追記すれば、開いている画面がリロードなしで即時描画されます。

---

## 2. ファイル構成

```text
Tools/ai-canvas/
├── index.html        # キャンバス本体 (Core + プラグイン + DSL) — 開発・起動用正本
├── index.export.html # export 用 minify シェル（build-export で再生成）
├── export_shell.py   # minify シェル読込・DSL 埋め込み・ビルド
├── canvas_app.py     # WebView2 起動 & 双方向同期 & 外部DSLホット監視
├── canvas_cli.py     # 外部AI・ターミナル用CLI操作ツール
├── dsl_normalize.py  # DSL / state の latex・detail 正規化（CLI と同じ規則）
├── start_canvas.bat  # ワンクリック起動バッチ (ASCII純粋)
├── canvas_state.json # 共有状態ファイル (全オブジェクト座標・内容・接続)
├── inbox_dsl.txt     # 外部からのDSL注入ポスト
├── quantum_demo.txt  # デモ DSL 正本
├── docs/             # RELEASE_v1, USER_GUIDE, BRUSHUP_ROADMAP
├── tools/            # build 計測スクリプト（任意）
├── vendor/katex/     # オフライン数式（export 同梱は任意）
└── README.md         # 本書
```

---

## 3. 使い方

### 起動
```bat
start_canvas.bat
```
または
```bash
python -X utf8 canvas_app.py
```

### AI・外部エージェント向け — 推奨フロー（2段 CLI）

**書く → 直す → 送る** の順が標準です。正規化と投入を分けると、diff で確認でき、表示不具合の切り分けも楽です。

```bash
cd G:\マイドライブ\Tools\ai-canvas

# ① AI が DSL をファイルに書く（例: my_draft.txt）

# ② 正規化（latex / detail 内の数式エスケープを表示向けに整える）
python -X utf8 canvas_cli.py normalize my_draft.txt -o my_draft_fixed.txt
# 差分確認: my_draft.txt と my_draft_fixed.txt を比較してから次へ

# ③ キャンバスへ投入（AI-Canvas を起動した状態で）
python -X utf8 canvas_cli.py show my_draft_fixed.txt
```

キャンバス保存済みの `canvas_state.json` だけ直す場合:

```bash
python -X utf8 canvas_cli.py normalize canvas_state.json --in-place
```

変更が必要かだけ調べる（CI・事前チェック）:

```bash
python -X utf8 canvas_cli.py normalize my_draft.txt --check
# 直すべき行があるとき終了コード 1
```

### 省略経路（急ぎ・試し）

投入の直前にだけ正規化する場合は `show -n` も使えます。**本番・共有用の正本は②でファイルを残す二段フローを推奨**します。

```bash
python -X utf8 canvas_cli.py show -n my_draft.txt
```

### その他の CLI

```bash
python -X utf8 canvas_cli.py state    # 現在の配置・接続の概要
python -X utf8 canvas_cli.py clear    # キャンバス全消去
python -X utf8 canvas_cli.py reload   # 画面リロード指示
python -X utf8 canvas_cli.py export        # 単体 HTML（minify シェル + inbox/demo の DSL）
python -X utf8 canvas_cli.py build-export  # index.html 変更後に index.export.html を再生成
python -X utf8 canvas_cli.py types    # 登録コンポーネント型一覧
```

ワンライン投入（正規化なし・対話用）:

```bash
python -X utf8 canvas_cli.py show "card: c1 [title='仮説']"
```

### データ作成の注意（normalize でも直らないもの）

| 項目 | 書き方 |
|------|--------|
| **ノード上の数式** | `math:` の `latex=` を使う。`text:` の `content` はプレーン／HTML想定（詳細パネル用の式は `detail=`） |
| **詳細パネルの式** | `detail=` 内の `$…$` / `$$…$$`。改行は `\n`（`\nu` など TeX コマンドは一重 `\` が無難） |
| **ディスプレイ数式** | `$$…$$` は **1行** にまとめる |
| **詳細内 SVG** | **1行** の `<svg …></svg>`（長い場合は別ノード `svg:`） |
| **正規化の対象** | CLI / 画面とも **`latex` と `detail` のみ**（`text` の本文は自動修正しない） |

表示は `index.html` 側でも同系の正規化を行いますが、**投入前の `normalize` を通すと AI 生成データのブレを先に吸収**できます。

---

## 4. 簡易DSL構文

```text
# 思考カード
card: <id> [title="タイトル", sub="サブタイトル", color="#38bdf8"]

# 数式 (KaTeX)
math: <id> [label="ラベル", latex="LaTeX文字列", to="接続先id", label="矢印ラベル"]

# 解説テキスト
text: <id> [title="見出し", content="本文...", to="接続先id", label="矢印ラベル"]

# 自由SVG図形
svg:  <id> [title="見出し", svg_content="<circle ... />", to="接続先id", label="矢印ラベル"]
```

### 任意 — エッジの見た目（Phase 1・省略可）

ノードの `to` 接続に付ける（**すべて省略可**。省略時はテーマ既定の実線）。

```text
math: m1 [latex="E=mc^2", to="origin", link="定式化", edge_color="#10b981", edge_width=2.5, edge_dash="6,4"]
```

独立行（`from` / `to` 必須）:

```text
edge: e1 [from="origin", to="einstein", label="定式化", color="#10b981", width=2.5, dash="8,4"]
```

`canvas_state.json` は `schema_version: 1` と、エッジごとの任意 `style: { stroke, width, dash, arrow }` を保存します。

### 操作 — 詳細パネルとフォーカス

- **クリック**: 詳細パネルを開く。接続一覧から相手ノードへジャンプ可能。
- **矢印キー**: 空間的にフォーカス移動。**パネルを閉じた状態ではパネルは開かない**（選択リングのみ更新）。
- **`?`**: ショートカットヘルプ。

### 単体 HTML エクスポートのサイズ

- **起動は正本 `index.html`**、**export / GUI 保存は `index.export.html`（minify）＋ 埋め込み DSL** です（ライブ DOM の二重コピーはしません）。
- `index.html` を直したら **`canvas_cli.py build-export`**（または `python export_shell.py`）で minify シェルを更新してください。無い場合は正本にフォールバックします。
- 量子デモ程度の DSL では export 全体は **おおよそ 55 KB 前後**（正本のみ export だと約 90 KB）。`detail=` が長いと DSL 分だけ増えます。
- 各ノードの **現在の `x` / `y`** を DSL に含めるため、ドラッグ後の配置もスナップショットで復元されます。
- KaTeX は **ローカル `vendor/` 優先・失敗時 CDN**（HTML 1 枚送付＋オンラインなら vendor 同梱不要のことが多い）。
- 埋め込み DSL は **Base64**（`;` や `\nu` を含む長い `detail=` でも壊れない）。開いたとき **「単体スナップショットを正常に復元しました！」** が出れば成功。

---

## 5. v1 完成後のメンテナ

| 作業 | コマンド |
|------|----------|
| 本体を直したあと | `python -X utf8 canvas_cli.py build-export` |
| 回帰テスト | `python -X utf8 -m unittest discover -q` |
| 単体 HTML 配布 | GUI export または `canvas_cli.py export` |

**Git**: ローカル正本は本フォルダ。**共有の正本**は [ogaogamirai/ai-canvas](https://github.com/ogaogamirai/ai-canvas)（public）。`index.html` 等を直したら `canvas_cli.py build-export` → `git commit` → `git push origin master`。**閉じ役: Nova**（[`GITHUB_CLOSER_ROLES_v01.md`](../GITHUB_CLOSER_ROLES_v01.md)）。

# AI-Canvas DSL 文法・使い方（コンパクト版）

> AI も人間も読む 1 枚リファレンス。正本パーサーは `src/canvas.js` の `applyDSL`。
> 書き方 → `check` → `normalize` → `show` の順が標準（詳細は [README §3](../README.md)）。

---

## 1. 基本

- **1 行 = 1 文**。空行は無視。
- `# コメント`（行頭 `#`）は無視。
- `clear` または `reset` の行でキャンバス全消去（途中にあってもよい）。
- ノード行の形:

```text
type: id [key="value", key=value, ...]
```

| 要素 | 規則 |
|---|---|
| `type` | 半角小文字のみ（`card` `text` `math` `svg` `sticky` `table` `group` `edge`） |
| `id` | `[A-Za-z0-9_-]+`（英数・`_`・`-`） |
| `key` | `[A-Za-z0-9_-]+` |
| `value` | `"..."`（`\"` エスケープ可）／ `'...'` ／ 素の値（空白・`,`・`]` を含まない） |

- **平文の行**（`:` も `->` も無い行）は **自動で `card`** になる（id は内容から自動生成）。
- `[タイトル]` だけの行も `card` の `title` になる。

---

## 2. ノード型と主なプロパティ

| 型 | 主なプロパティ | 既定サイズ | 用途 |
|---|---|---|---|
| `card` | `title`, `sub`, `tag`, `color` | 200×84 | 思考カード（`tag` は左上の小見出し、既定は id） |
| `text` | `title`, `content`, `color` | 250×100 | 解説段落（`content` は素の文/HTML） |
| `math` | `title`（別名 `label`）, `latex`, `color` | 230×92 | KaTeX 数式 |
| `svg` | `title`, `svg_content` | 150×150 | 自由ベクター図形 |
| `sticky` | `title`, `content`（別名 `text`）, `color`, `author` | 180×120 | 付箋メモ（既定色 `#fef08a`） |
| `table` | `title`, `headers`（別名 `cols`）, `rows`, `color` | 内容に応じ可変 | 比較表 |
| `group` | `title`, `sub`, `contains`, `color`, `bg` | 380×240 | 領域枠（背面に描画。`contains` に id を並べる） |

- `color` は `#rgb` / `#rrggbb`。
- `table` の書き方: `headers="項目A, 項目B"`, `rows="値1|値2; 値3|値4"`（`|`＝セル、`;`＝行）。
- `svg` の `svg_content` は **1 行** の `<svg …>…</svg>` か断片（`<rect/>` 等）。

### 全ノード共通

| プロパティ | 意味 |
|---|---|
| `x=`, `y=` | 手動座標（数値）。付けると「手動配置」扱い |
| `w=`, `h=` | サイズ上書き（数値） |
| `detail="…"` | 詳細パネル用 Markdown（次節） |

---

## 3. `detail` の書き方（最重要）

詳細パネルに表示する Markdown。**`$…$` / `$$…$$` の KaTeX、1 行 `<svg>` も展開**される。

| 項目 | 書き方 |
|---|---|
| 改行 | `\n`（実際の改行を入れると DSL が壊れる） |
| 二重引用符 | `\"` |
| バックスラッシュ | **そのまま**（`\frac` `\nu` 等の LaTeX を保持） |
| ディスプレイ数式 `$$…$$` | **1 行**にまとめる |
| 数式内の TeX コマンド | `$…$` の内側なら `\n` 系コマンドも安全 |

```text
card: idea [title="仮説", detail="# 見出し\nこれは**要点**。\n$$\nE = mc^2\n$$\n"]
```

> パネル右上の **✏️**（DSL Editor のみ）で `detail` を直接編集・保存できます。

---

## 4. エッジ（3 通り）

### (a) 独立行（推奨・明示的）

```text
edge: e1 [from="origin", to="einstein", label="定式化", color="#10b981", width=2.5, dash="8,4", arrow=double]
```

| プロパティ | 意味 |
|---|---|
| `from`（別名 `u`）, `to`（別名 `v`） | 端点 id（必須） |
| `label`（別名 `link`） | エッジラベル |
| `color`（別名 `stroke`） | 線色 `#hex` |
| `width` | 太さ（既定 1.6） |
| `dash`（別名 `edge_dash`） | 破線パターン（`"5,4"` 等）。`edge_style="dashed"` も可 |
| `arrow` | `none`（なし）/ `double`（両）/ 省略で片矢印 |
| `arrow_color` | 矢印色 |

### (b) ノード行のインライン接続（`to=`）

`to="接続元id"` を書くと「接続元 → このノード」のエッジが張られる。スタイルは `edge_*` 接頭辞。

```text
math: m1 [latex="E=mc^2", to="origin", link="定式化", edge_color="#10b981", edge_width=2.5, edge_dash="6,4"]
```

### (c) 矢印ショートハンド

```text
origin -> einstein
origin -> debroglie : 波粒子二重性
```

---

## 5. 座標と自動整列

- `x` / `y` が無いノードは、**エッジ階層に沿って自動整列**される。
- 整列方向は ツールバーの **`→`（横）/ `↑`（下から上）/ `↓`（上から下）**。直近の方向を記憶。
- **エッジを追加すると直後に再整列**（重なり防止）。手動配置ノードは再整列で上書きされる点に注意。

---

## 6. 最小例

```text
clear

card: origin [title="光の本質とは何か？", sub="キャプテンの問い", color="#c084fc", detail="# 20世紀の転換点\n光は波か粒子か。"]
math: einstein [title="EINSTEIN (1905)", latex="E_{max} = h\nu - W_0"]
text: insight [title="光量子仮説", content="強度ではなく振動数が脱出エネルギーを決める。"]
sticky: memo [title="TODO", content="ド・ブロイを調べる", color="#fef08a"]

edge: e1 [from="origin", to="einstein", label="定式化", color="#10b981", width=2.5]
edge: e2 [from="einstein", to="insight", label="意味"]
```

---

## 7. つまずきやすい点

- **`label` の二重用途**: ノードに `to=` を付けたとき、`label=` は**エッジラベル**としても解釈される。ノード自身のラベルとエッジラベルを分けたいときは、ノードは `title=`、エッジは `link=` を使う。
- **`detail` に生の改行**を入れると行が壊れる → 必ず `\n`。
- **`"` を含む値**は `\"`。素の `"` はそこで文字列が終わる。
- **`$$…$$` と `<svg>` は 1 行**。
- 正規化できるのは `latex` と `detail` のみ（`text.content` は自動修正されない）。

---

## 8. 検証・投入（CLI）

```bash
python -X utf8 canvas_cli.py check  draft.txt        # 行番号付き error/warning（error で exit 1）
python -X utf8 canvas_cli.py normalize draft.txt -o fixed.txt   # latex/detail を表示向けに整形
python -X utf8 canvas_cli.py show   fixed.txt        # キャンバスへ投入（起動中）
python -X utf8 canvas_cli.py jsoncanvas-export -o board.canvas   # state → JSON Canvas（Obsidian 等で開ける）
python -X utf8 canvas_cli.py jsoncanvas-import board.canvas -o out.dsl   # JSON Canvas → DSL
```

その他のコマンド（`state` / `dsl` / `diff` / `apply` / `neighbors` / `path` / `tree` / `types` / `jsoncanvas-*` など）は [README §3](../README.md) を参照。

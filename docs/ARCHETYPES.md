# AI-Canvas 認知工学設計ガイド（5大アーキタイプと二重符号化原則）

> **「誰が見ても3秒で直感的に構造が伝わるグラフを作るための認知工学プロトコル」**  
> 単なるフローチャート（四角い文字カードの羅列）を脱却し、人間の脳が最も理解しやすい幾何学構造と視覚要素（SVG・数式・表・付箋）を組み合わせるための実践ガイドです。

---

## 1. 認知工学の2大原則

### 原則①：二重符号化（Dual Coding）— 文字と絵の協調
- **理論背景**: 人間の脳は「言語ルート（テキスト）」と「非言語ルート（図解・色・空間配置）」の2つの回路を並行して動かします。テキストだけを並べると言語処理に過大な負荷がかかります。
- **実践ルール**:
  - **四角い `card:` の単調な羅列を禁止**します。
  - 1つのダイアグラム内に、必ず **SVG図解（`svg:`）**、**美麗数式（`math:`）**、**比較表（`table:`）**、**付箋メモ（`sticky:`）** のいずれかを最低1〜2個アクセントとして配置してください。
  - これにより、読者は0.5秒で「何が起きているか（力学・核）」を直感し、その後に安心してテキストを読むことができます。

### 原則②：段階的開示（Progressive Disclosure）— 地図と辞書の分離
- **理論背景**: 初見で情報量が多すぎると認知過負荷（Cognitive Overload）を起こし、読者は読むのを諦めます。
- **実践ルール**:
  - **カード表面は「3秒認知の地図」**:
    - `title`: 15文字以内（要約・キーワード）
    - `sub` または本文: 2〜3行以内（核心の一言）
  - **カード裏面（詳細パネル `detail`）は「辞書・詳細レポート」**:
    - カードをクリックしたときに開く `detail` プロパティの中に、Markdown・KaTeX数式・表形式で本格的な解説・背景・エビデンスをふんだんに格納します。

---

## 2. 5大アーキタイプ選定チャート

ダイアグラムを作成する目的・テーマに応じて、以下の5つの型から最適な幾何学構造を選択してください。

```text
[グラフの目的は何ですか？]
  │
  ├─ 人材育成・成長プロセス・公的支援を描きたい
  │    └─➔ ① 【ライフサイクル／主血流型】（三層コア＆オービット）
  │
  ├─ 賛否両論・二項対立・トレードオフを乗り越えたい
  │    └─➔ ② 【対立・止揚型】（ダイヤモンド／砂時計構造）
  │
  ├─ 原因と結果が巡る好循環・悪循環・システムを解き明かしたい
  │    └─➔ ③ 【循環エコシステム型】（インフィニティループ／システムダイナミクス）
  │
  ├─ 多角的な監査・多面評価・総合判定を下したい
  │    └─➔ ④ 【ハブ＆スポーク／多角評価型】（360度多角監査モデル）
  │
  └─ 難解な学術概念・数理モデル・技術の本質を噛み砕いて教えたい
       └─➔ ⑤ 【学習・探究型】（Inquiry & Essence Model / 直感比喩＋数式＋図解）
```

---

## 3. 各アーキタイプの構造とDSL骨格

### ① ライフサイクル／主血流型（三層コア＆オービット）
- **用途**: 政策ロードマップ、人材育成、プロダクト成長。
- **幾何学構造**: 中央に「個人の内発的動機・成長」の太い主血流（LRフロー）を通し、周囲を「公的支援・インフラ」が同心円（オービット）状に取り囲む構造。
- **骨格例**:
```dsl
# 中央の主血流（本質的な成長パス）
card: c_spark [title="内発的動機（熱源）", color="#ec4899", to="c_inquiry"]
card: c_inquiry [title="自発的探究", color="#38bdf8", to="c_implement"]
card: c_implement [title="社会実装・挑戦", color="#10b981"]

# 外周オービット（環境・インフラによる支え）
group: g_infra [title="公的インフラ・支援基盤", contains="inf_base,inf_finance", color="#6366f1"]
card: inf_base [title="心理的安全性・生活保障"]
card: inf_finance [title="挑戦資金・セーフティネット"]

edge: e_sup1 [from="inf_base", to="c_spark", label="安心の担保", style="straight", color="#6366f1"]
```

---

### ② 対立・止揚型（ダイヤモンド／砂時計構造）
- **用途**: 政策論争、事業戦略の対立、意思決定。
- **幾何学構造**: 上部の「共通課題」から二大陣営（A案 vs B案）に分岐（発散）し、両者のトレードオフを突き合わせた上で、下部の「止揚（第三の道・統合パッケージ）」へと収束（アウフヘーベン）するダイヤモンド構造。
- **骨格例**:
```dsl
card: root_issue [title="中核課題：限られたリソースの配分", color="#f59e0b"]

# 対立する二大陣営
group: g_side_a [title="立場A：積極投資派", contains="a1,a2", color="#38bdf8"]
card: a1 [title="大胆な未来投資"]
card: a2 [title="経済成長による解決"]

group: g_side_b [title="立場B：規律重視派", contains="b1,b2", color="#f43f5e"]
card: b1 [title="財政バランスの維持"]
card: b2 [title="将来世代への負担回避"]

# 止揚（第三の道）
card: synthesis [title="統合解決策（賢い支出）", color="#10b981", detail="# 合意パッケージの根拠..."]

edge: ed1 [from="root_issue", to="a1", style="straight"]
edge: ed2 [from="root_issue", to="b1", style="straight"]
edge: ed3 [from="a2", to="synthesis", label="成長の果実", style="straight", color="#10b981"]
edge: ed4 [from="b2", to="synthesis", label="規律の担保", style="straight", color="#10b981"]
```

---

### ③ 循環エコシステム型（インフィニティループ／システムダイナミクス）
- **用途**: 「悪貨は良貨を駆逐する」、賃金と物価の好循環、プラットフォームのフライホイール。
- **幾何学構造**: 原因と結果が自己強化していく環状ループ（正/負のフィードバック）。中央に天秤や対照表などの**核となる視覚要素**を置き、両翼にスパイラルを描く。
- **骨格例**:
```dsl
# 中央アイキャッチ（直感図解）
svg: visual_scale [w="440", h="200", title="天秤図解：良貨退蔵 vs 悪貨放出", svg_content="<svg ...>...</svg>"]

# 悪循環ループ
card: loop_1 [title="① 評価の単純化（均一額面）", color="#0ea5e9"]
card: loop_2 [title="② 粗悪品の低コスト大量投入", color="#f43f5e"]
card: loop_3 [title="③ 誠実な作り手の撤退（退蔵）", color="#6366f1"]
card: loop_4 [title="④ 空間のゴミ屋敷化", color="#dc2626"]

edge: el1 [from="loop_1", to="loop_2", width=2.4]
edge: el2 [from="loop_2", to="loop_3", width=2.4]
edge: el3 [from="loop_3", to="loop_4", width=2.4]
edge: el4 [from="loop_4", to="loop_1", label="悪化の固定化", dash="5,4", color="#dc2626"]

# 抑止レバー（ループを断ち切る介入杭）
card: sol_lever [title="抑止杭：透明化とシグナリング", color="#10b981"]
edge: es1 [from="sol_lever", to="loop_2", label="粗悪品を不採算化", dash="6,3", color="#10b981"]
```

---

### ④ ハブ＆スポーク／多角評価型（360度多角監査モデル）
- **用途**: 新技術の導入評価（自動運転、ライドシェア、AI導入）、総合アセスメント。
- **幾何学構造**: 中央に評価対象の「中核命題（ハブ）」を置き、周囲に多角的な評価軸（安全性・経済・法制・倫理・共生など）を放射状（スポーク）に展開。最後に右側の「総合判定」カードへエビデンスを結集させる。
- **骨格例**:
```dsl
card: target_hub [title="監査対象：自動運転＆ライドシェア解禁", color="#c084fc"]

# 周囲の多角評価軸
card: ax_safe [title="安全・運行責任：条件付許容", color="#10b981"]
card: ax_econ [title="利用者便益：高評価", color="#38bdf8"]
card: ax_labor [title="既存事業者共生：要調整", color="#f59e0b"]
card: ax_local [title="地方交通維持：最重要課題", color="#f43f5e"]

# 総合判定
card: final_verdict [title="総合判定：フェーズ分け段階導入（GO）", color="#10b981", detail="# 監査報告書..."]

edge: eh1 [from="target_hub", to="ax_safe", style="straight"]
edge: eh2 [from="target_hub", to="ax_econ", style="straight"]
edge: eh3 [from="target_hub", to="ax_labor", style="straight"]
edge: eh4 [from="target_hub", to="ax_local", style="straight"]

edge: ev1 [from="ax_safe", to="final_verdict", label="監査パス", color="#10b981"]
edge: ev2 [from="ax_labor", to="final_verdict", label="移行猶予付与", color="#f59e0b"]
```

---

### ⑤ 学習・探究型（Inquiry & Essence Model）
- **用途**: フーリエ変換、量子力学、アルゴリズムなど難解な概念の教育・解説。
- **幾何学構造**:
  1. **日常の直感比喩（WHY）**: 「ミックスジュースの成分分析」「音のプリズム」
  2. **中核数理（WHAT）**: KaTeX 数式ブロック（`math:`）
  3. **視覚図解（VISUAL）**: プリズムや波形の SVG ベクター図（`svg:`）
  4. **現実の応用（HOW）**: MP3/JPEG、Wi-Fi、MRI などの実用例
  5. **落とし穴（CAUTION）**: 初学者が陥りやすい誤解や限界
- **骨格例**:
```dsl
card: inq_metaphor [title="直感比喩：音を分ける「数学のプリズム」", color="#38bdf8"]
math: inq_math [title="連続フーリエ変換", latex="F(\\omega) = \\int_{-\\infty}^{\\infty} f(t) e^{-i\\omega t} dt"]
svg: inq_svg [w="420", h="180", title="図解：波のスペクトル分解", svg_content="<svg ...>...</svg>"]
card: inq_app [title="現代応用：MP3圧縮とWi-Fi通信", color="#a855f7"]
card: inq_pitfall [title="⚠️ 落とし穴：時間情報が消える", color="#f59e0b"]

edge: e_learn1 [from="inq_metaphor", to="inq_math", label="数学的定式化"]
edge: e_learn2 [from="inq_math", to="inq_svg", label="視覚的理解"]
edge: e_learn3 [from="inq_svg", to="inq_app", label="実社会実装"]
edge: e_learn4 [from="inq_math", to="inq_pitfall", label="注意点", style="dashed", color="#f59e0b"]
```

---

## 4. 実践Tips（落とし穴の防止と美しい仕上げ）

### 1. SVGコンポーネントの正しい書き方
- **プロパティ名**: `svg_content="..."` または `svg="..."` のどちらでも認識されます。
- **viewBox の指定**: `<svg viewBox="0 0 W H" ...>` を必ず含めてください。カード枠内に `preserveAspectRatio="xMidYMid meet"` で自動アスペクトフィットされます。
- **カードサイズの明示**: SVG を綺麗に見せるため、`w="440", h="200"` のように幅と高さを指定してください。
- **テーマ連動**: SVG の背景は `fill="none"` または `fill="var(--card-bg)"` にしておくと、ライトテーマ（Natural）とダークテーマ（Cool Cyber）の両方に自動連動します。

### 2. エディタ版でのマウスレイアウト保存
- AI-Canvas をエディタ付き（`ai-canvas.html`）で開いた場合、キャンバス上でノードを自由にマウスドラッグして気持ちいい位置に並べ替えることができます。
- 配置が決まったら、**エディタ上部ヘッダーの「📥（キャンバスから最新化）」ボタン** をクリックしてください。
- ドラッグ移動した最新の絶対座標（`x=..., y=...`）が DSL テキスト内に一発で焼き込まれ、そのまま「💾（DSL保存）」で手元に保管できます。

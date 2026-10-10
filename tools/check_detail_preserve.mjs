// 詳細パネルでの detail 保存が、他パラメーター（latex / headers / rows / svg_content / title / color 等）を
// 壊さないことを、実物の updateNodePropDetail + applyDSL で検証する。
// 使い方: node tools/check_detail_preserve.mjs
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.dirname(here);
const html = fs.readFileSync(path.join(root, 'editor.html'), 'utf8');

let failed = 0;
function check(name, cond) {
  if (!cond) { console.error(`FAIL: ${name}`); failed++; }
}

function extract(marker) {
  const i = html.indexOf(marker);
  if (i < 0) return null;
  const b = html.indexOf('{', i);
  let depth = 0;
  for (let j = b; j < html.length; j++) {
    const c = html[j];
    if (c === '{') depth++;
    else if (c === '}') { depth--; if (depth === 0) return html.slice(i, j + 1); }
  }
  return null;
}

const esc = extract('function escapeDetailMarkdown');
const sq = extract('function setQuotedProp');
const qp = html.match(/const QUOTED_PROP_SRC = `[^`]*`;/)[0];
const upd = extract('updateNodePropDetail: function');
const applySrc = extract('applyDSL: function');

const { escapeDetailMarkdown, setQuotedProp } =
  new Function(`${qp}\n${esc}\n${sq}\nreturn { escapeDetailMarkdown, setQuotedProp };`)();
const updateNodePropDetail =
  new Function('escapeDetailMarkdown', 'setQuotedProp', `return ({ ${upd} }).updateNodePropDetail;`)(escapeDetailMarkdown, setQuotedProp);
const applyDSL =
  new Function('objects', 'edges', 'safeNum', 'normalizeEdgeStyle', 'edgeStyleFromNodeProps', 'updateEdges', 'updateGroups', 'document', 'logBar',
    `return ({ ${applySrc} }).applyDSL;`)(new Map(), [], (v, f = 0) => (isFinite(Number(v)) ? Number(v) : f), () => null, () => null, () => {}, () => {}, { getElementById: () => null }, { innerText: '' });

const DETAIL = '# 解説\nこれは**テスト**。\n$h\\nu$ と "引用"';

const cases = [
  ['math latex', 'math: einstein [title="EINSTEIN (1905)", latex="E_{max} = h\\nu - W_0"]', ['title', 'latex']],
  ['math latex with quote', 'math: q [title="Q", latex="\\text{\\"hi\\"}"]', ['title', 'latex']],
  ['table', 'table: t1 [title="比較", headers="A, B", rows="1|2; 3|4"]', ['title', 'headers', 'rows']],
  ['svg', 'svg: s1 [title="図", svg_content="<rect width=\'10\' height=\'10\'/>"]', ['title', 'svg_content']],
  ['card color', 'card: c1 [title="カード", color="#38bdf8", sub="サブ"]', ['title', 'color', 'sub']],
  ['text', 'text: tx1 [title="解説", content="本文"]', ['title', 'content']],
];

for (const [name, line, keep] of cases) {
  const id = line.match(/^[a-z]+:\s*([a-zA-Z0-9_-]+)/)[1];
  const ctx = { textareaEl: { value: line }, updateLineNumbers() {}, updateCursorPos() {}, applyToCanvas() {} };
  const ok = updateNodePropDetail.call(ctx, id, DETAIL);
  check(`${name}: returns true`, ok === true);
  const spawn = [];
  const ctx2 = { clear() {}, spawn(t, p) { spawn.push(p); }, connect() {}, fitView() {}, autoLayout() {} };
  applyDSL.call(ctx2, ctx.textareaEl.value);
  const parsed = spawn[0] || {};
  for (const k of keep) {
    check(`${name}: keeps ${k}`, parsed[k] !== undefined && parsed[k] !== '');
  }
  check(`${name}: detail added`, typeof parsed.detail === 'string' && parsed.detail.length > 0);
}

// 既存 detail の置換でも他パラメーターを保つ
{
  const line = 'math: m [title="T", latex="x", detail="old"]';
  const ctx = { textareaEl: { value: line }, updateLineNumbers() {}, updateCursorPos() {}, applyToCanvas() {} };
  updateNodePropDetail.call(ctx, 'm', 'new detail');
  const spawn = [];
  const ctx2 = { clear() {}, spawn(t, p) { spawn.push(p); }, connect() {}, fitView() {}, autoLayout() {} };
  applyDSL.call(ctx2, ctx.textareaEl.value);
  const parsed = spawn[0] || {};
  check('replace: latex kept', parsed.latex === 'x');
  check('replace: detail updated', parsed.detail === 'new detail');
}

// 空で detail を除去しても他は残る
{
  const line = 'math: m2 [title="T", latex="y", detail="old"]';
  const ctx = { textareaEl: { value: line }, updateLineNumbers() {}, updateCursorPos() {}, applyToCanvas() {} };
  updateNodePropDetail.call(ctx, 'm2', '');
  const spawn = [];
  const ctx2 = { clear() {}, spawn(t, p) { spawn.push(p); }, connect() {}, fitView() {}, autoLayout() {} };
  applyDSL.call(ctx2, ctx.textareaEl.value);
  const parsed = spawn[0] || {};
  check('remove: latex kept', parsed.latex === 'y');
  check('remove: detail gone', parsed.detail === undefined);
}

if (failed === 0) {
  console.log('PASS: detail save preserves other params (math/table/svg/card/text)');
} else {
  process.exit(1);
}

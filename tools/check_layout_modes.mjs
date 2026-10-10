// 自動整列の3方向（→ LR / ↑ BT / ↓ TB）と直近方向の記憶、スラッシュ /sticky の存在確認。
// ai-canvas.html から実物の autoLayout を抽出して走らせる。
// 使い方: node tools/check_layout_modes.mjs
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.dirname(here);
const html = fs.readFileSync(path.join(root, 'ai-canvas.html'), 'utf8');

function extract(marker) {
  const i = html.indexOf(marker);
  if (i < 0) return null;
  const braceStart = html.indexOf('{', i);
  let depth = 0;
  for (let j = braceStart; j < html.length; j++) {
    const c = html[j];
    if (c === '{') depth++;
    else if (c === '}') {
      depth--;
      if (depth === 0) return html.slice(i, j + 1);
    }
  }
  return null;
}

const fnSrc = extract('autoLayout: function');
if (!fnSrc) {
  console.error('FAIL: autoLayout not found in ai-canvas.html');
  process.exit(2);
}

function buildGraph() {
  const objects = new Map();
  ['a', 'b', 'c'].forEach((id) =>
    objects.set(id, { id, type: 'card', x: 0, y: 0, w: 100, h: 50, data: {} })
  );
  const edges = [{ u: 'a', v: 'b' }, { u: 'b', v: 'c' }];
  const factory = new Function(
    'objects', 'edges', 'safeNum', 'updateEdges', 'updateGroups', 'document', 'logBar',
    `const m = ({ ${fnSrc} }); return m.autoLayout;`
  );
  const autoLayout = factory(
    objects, edges,
    (v, f = 0) => (isFinite(Number(v)) ? Number(v) : f),
    () => {}, () => {},
    { getElementById: () => null },
    { innerText: '' }
  );
  return { objects, autoLayout };
}

let failed = 0;
function check(name, cond) {
  if (!cond) { console.error(`FAIL: ${name}`); failed++; }
}

// --- 3方向の座標 ---
{
  const { objects, autoLayout } = buildGraph();
  const ctx = { syncToPython: () => {}, fitView: () => {} };
  autoLayout.call(ctx, 'LR');
  check('LR: x increases with level', objects.get('a').x < objects.get('b').x && objects.get('b').x < objects.get('c').x);
  check('LR: same rank => same y', objects.get('a').y === objects.get('b').y && objects.get('b').y === objects.get('c').y);
}
{
  const { objects, autoLayout } = buildGraph();
  autoLayout.call({ syncToPython: () => {}, fitView: () => {} }, 'TB');
  check('TB: y increases with level (top->down)', objects.get('a').y < objects.get('b').y && objects.get('b').y < objects.get('c').y);
}
{
  const { objects, autoLayout } = buildGraph();
  autoLayout.call({ syncToPython: () => {}, fitView: () => {} }, 'BT');
  check('BT: y decreases with level (bottom->top)', objects.get('a').y > objects.get('b').y && objects.get('b').y > objects.get('c').y);
}
{
  // 直近方向の記憶: 引数なし呼び出しは前回方向を再利用する
  const { objects, autoLayout } = buildGraph();
  const ctx = { syncToPython: () => {}, fitView: () => {} };
  autoLayout.call(ctx, 'BT');
  autoLayout.call(ctx);
  check('default reuse: layoutDirection=BT', ctx.layoutDirection === 'BT');
  check('default reuse: BT geometry applied', objects.get('a').y > objects.get('c').y);
}

// --- 生成物の静的確認 ---
check('ai-canvas.html: 3 layout buttons', (html.match(/layout-dir-btn/g) || []).length >= 3);
check('ai-canvas.html: /sticky command', html.includes("'/sticky'"));
check('ai-canvas.html: no hardcoded autoLayout(\'LR\') left in applyDSL', !html.includes("this.autoLayout('LR')"));

if (failed === 0) {
  console.log('PASS: layout modes (LR/TB/BT) + default reuse + /sticky');
} else {
  process.exit(1);
}

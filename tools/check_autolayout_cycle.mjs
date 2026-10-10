// autoLayout のサイクル安全テスト。
// editor.html から実物の autoLayout を抽出し、閉路グラフで走らせて
// 有限時間で終了することを確認する（従来は閉路で無限ループ＝フリーズ）。
// 使い方: node tools/check_autolayout_cycle.mjs
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.dirname(here);
const html = fs.readFileSync(path.join(root, 'editor.html'), 'utf8');

const marker = 'autoLayout: function';
const i = html.indexOf(marker);
if (i < 0) {
  console.error('autoLayout not found in editor.html');
  process.exit(2);
}
const braceStart = html.indexOf('{', i);
let depth = 0;
let end = -1;
for (let j = braceStart; j < html.length; j++) {
  const c = html[j];
  if (c === '{') depth++;
  else if (c === '}') {
    depth--;
    if (depth === 0) { end = j + 1; break; }
  }
}
const fnSrc = html.slice(i, end);

const objects = new Map();
const edges = [];
['a', 'b', 'c'].forEach((id) =>
  objects.set(id, { id, type: 'card', x: 0, y: 0, w: 100, h: 50, data: {} })
);
edges.push({ u: 'a', v: 'b' }, { u: 'b', v: 'c' }, { u: 'c', v: 'a' }); // cycle

const factory = new Function(
  'objects', 'edges', 'safeNum', 'updateEdges', 'updateGroups', 'document', 'logBar',
  `const m = ({ ${fnSrc} }); return m.autoLayout;`
);
const autoLayout = factory(
  objects,
  edges,
  (v, f = 0) => (isFinite(Number(v)) ? Number(v) : f),
  () => {},
  () => {},
  { getElementById: () => null },
  { innerText: '' }
);

const t0 = Date.now();
autoLayout.call({ syncToPython: () => {}, fitView: () => {} }, 'LR');
const dt = Date.now() - t0;
console.log(`autoLayout on cycle finished in ${dt} ms`);
if (dt >= 3000) {
  console.error('FAIL: autoLayout did not terminate promptly (cycle hang?)');
  process.exit(1);
}
console.log('PASS: cycle-safe');

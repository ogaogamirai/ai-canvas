// JSON Canvas 書き出し（buildJsonCanvas）の検証。ai-canvas.html から実物を抽出して走らせる。
// 使い方: node tools/check_jsoncanvas_js.mjs
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.dirname(here);
const html = fs.readFileSync(path.join(root, 'ai-canvas.html'), 'utf8');

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

const fnHex = extract('function jcHex16');
const fnTable = extract('function jcMdTable');
const fnMd = extract('function jcMdForObject');
const fnBuild = extract('buildJsonCanvas: function');
check('has jcHex16', !!fnHex);
check('has jcMdTable', !!fnTable);
check('has jcMdForObject', !!fnMd);
check('has buildJsonCanvas', !!fnBuild);

const objects = new Map();
objects.set('origin', { id: 'origin', type: 'card', x: 80, y: 120, w: 200, h: 84,
  data: { id: 'origin', title: '光の本質', sub: '問い', color: '#c084fc', detail: 'line1\nline2' } });
objects.set('einstein', { id: 'einstein', type: 'math', x: 420, y: 120, w: 230, h: 92,
  data: { id: 'einstein', title: 'EINSTEIN', latex: 'E_{max} = h\\nu - W_0' } });
objects.set('tbl', { id: 'tbl', type: 'table', x: 80, y: 300, w: 300, h: 120,
  data: { id: 'tbl', title: '対比', headers: '対象, 波動性', rows: '光|干渉; 電子|回折' } });
objects.set('grp', { id: 'grp', type: 'group', x: 60, y: 100, w: 600, h: 340,
  data: { id: 'grp', title: '領域', color: '#38bdf8', contains: 'origin' } });
const edges = [
  { u: 'origin', v: 'einstein', label: '定式化', style: { stroke: '#10b981', width: 2.5, dash: '5,4', arrow: 'double' } }
];
const safeNum = (v, f = 0) => (isFinite(Number(v)) ? Number(v) : f);

const factory = new Function('objects', 'edges', 'safeNum',
  `${fnHex}\n${fnTable}\n${fnMd}\nconst api = ({ ${fnBuild} }); return api.buildJsonCanvas;`);
const buildJsonCanvas = factory(objects, edges, safeNum);
const jc = buildJsonCanvas.call({});

check('nodes count', jc.nodes.length === 4);
check('edges count', jc.edges.length === 1);
for (const n of jc.nodes) {
  check(`node ${n.id} type`, n.type === 'text' || n.type === 'group');
  for (const k of ['id', 'x', 'y', 'width', 'height']) check(`node ${n.id} has ${k}`, n[k] !== undefined);
}
const byId = Object.fromEntries(jc.nodes.map(n => [n.id, n]));
check('group type+label', byId.grp.type === 'group' && byId.grp.label === '領域');
check('math → text $$', byId.einstein.type === 'text' && /\$\$/.test(byId.einstein.text));
check('table → md table', /\| 対象 \|/.test(byId.tbl.text));
check('ai_canvas ext on node', byId.origin.ai_canvas && byId.origin.ai_canvas.type === 'card');
const e = jc.edges[0];
check('edge fromNode/toNode', e.fromNode === 'origin' && e.toNode === 'einstein');
check('edge arrow double', e.fromEnd === 'arrow' && e.toEnd === 'arrow');
check('edge ext width', e.ai_canvas && e.ai_canvas.width === 2.5);
check('edge id 16hex', /^[0-9a-f]{16}$/.test(e.id));

if (failed === 0) {
  console.log('PASS: jsoncanvas JS (buildJsonCanvas)');
} else {
  process.exit(1);
}

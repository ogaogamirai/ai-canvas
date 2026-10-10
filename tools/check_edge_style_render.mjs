// エッジの width / dash / color が inline style で適用されることの回帰テスト。
// SVG presentation 属性は CSS に負けるため、applyEdgeAppearance は inline style を使う。
// 使い方: node tools/check_edge_style_render.mjs
import fs from 'fs';
import vm from 'vm';
import path from 'path';
import { fileURLToPath } from 'url';

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.dirname(here);
const canvasJs = fs.readFileSync(path.join(root, 'src', 'canvas.js'), 'utf8');

function mkStyle() {
  const s = {};
  s.setProperty = (k, v) => { s[k] = v; };
  s.removeProperty = (k) => { delete s[k]; };
  return s;
}
function stub() {
  return {
    classList: { add() {}, remove() {}, contains() { return false; } },
    style: mkStyle(), value: '', textContent: '', innerHTML: '',
    _attrs: {}, setAttribute(k, v) { this._attrs[k] = v; }, getAttribute(k) { return this._attrs[k] ?? null; }, removeAttribute(k) { delete this._attrs[k]; },
    appendChild() {}, remove() {}, insertBefore() {}, addEventListener() {},
    querySelector() { return null; }, querySelectorAll() { return []; },
    getBoundingClientRect() { return { width: 800, height: 600, left: 0, top: 0 }; },
    setPointerCapture() {}, releasePointerCapture() {}, focus() {}, select() {}, replaceChildren() {}
  };
}
const els = {};
const document = {
  getElementById: (id) => (els[id] || (els[id] = stub())),
  createElementNS: () => stub(), createElement: () => stub(), createDocumentFragment: () => stub(),
  querySelector: () => null, querySelectorAll: () => [], addEventListener() {},
  body: { classList: { add() {}, remove() {} }, style: {} }
};
const window = { addEventListener() {}, innerWidth: 1080, innerHeight: 720 };
const context = vm.createContext({ window, document, console, setTimeout, clearTimeout, setInterval, clearInterval, Math, Array, Object, String, Number, RegExp, Set, Map, JSON, Date, isFinite });
vm.runInContext(canvasJs, context);
const Canvas = window.Canvas;

let failed = 0;
function check(name, cond, extra = '') {
  if (!cond) { console.error(`FAIL ${name}: ${extra}`); failed++; }
}

Canvas.applyDSL('clear\ncard: a [title="A"]\ncard: b [title="B"]\n\nedge: e1 [from="a", to="b", width=2, dash="5,4", color="#10b981"]');
const styled = els['path_edge_a_b_0'].style;
check('width applied as inline style', styled['stroke-width'] === '2', JSON.stringify(styled));
check('dash applied as inline style', styled['stroke-dasharray'] === '5,4', JSON.stringify(styled));
check('color applied as inline style', styled['stroke'] === '#10b981', JSON.stringify(styled));

Canvas.applyDSL('clear\ncard: a [title="A"]\ncard: b [title="B"]\n\nedge: e1 [from="a", to="b"]');
const plain = els['path_edge_a_b_0'].style;
check('no width leaves style empty', plain['stroke-width'] === undefined, JSON.stringify(plain));
check('no dash leaves style empty', plain['stroke-dasharray'] === undefined, JSON.stringify(plain));
check('no color leaves style empty', plain['stroke'] === undefined, JSON.stringify(plain));

// 並行エッジ（同ノード対）は少しずれて描画される
Canvas.applyDSL('clear\ncard: a [title="A"]\ncard: b [title="B"]\n\nedge: e1 [from="a", to="b"]');
const singleD = els['path_edge_a_b_0']._attrs['d'];
Canvas.applyDSL('clear\ncard: a [title="A"]\ncard: b [title="B"]\n\nedge: e1 [from="a", to="b"]\nedge: e2 [from="b", to="a"]');
const pairedD = els['path_edge_a_b_0']._attrs['d'];
check('parallel edge offset shifts path', singleD !== pairedD, `${singleD} vs ${pairedD}`);

// 矢印の種類（片=既定 / 両 / なし）
Canvas.applyDSL('clear\ncard: a [title="A"]\ncard: b [title="B"]\n\nedge: e1 [from="a", to="b"]');
const a1 = els['path_edge_a_b_0']._attrs;
check('default = single arrow (end only)', !!a1['marker-end'] && !a1['marker-start'], JSON.stringify(a1));
Canvas.applyDSL('clear\ncard: a [title="A"]\ncard: b [title="B"]\n\nedge: e1 [from="a", to="b", arrow=double]');
const a2 = els['path_edge_a_b_0']._attrs;
check('double arrow (both ends)', !!a2['marker-end'] && !!a2['marker-start'], JSON.stringify(a2));
Canvas.applyDSL('clear\ncard: a [title="A"]\ncard: b [title="B"]\n\nedge: e1 [from="a", to="b", arrow=none]');
const a3 = els['path_edge_a_b_0']._attrs;
check('no arrow', !a3['marker-end'] && !a3['marker-start'], JSON.stringify(a3));

if (failed) process.exit(1);
console.log('PASS: edge style render (inline style)');

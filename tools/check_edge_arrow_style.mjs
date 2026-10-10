// 矢印ショートハンド（A -> B）エッジのスタイル編集の回帰テスト。
// editor.js の EditorApp を DOM モックで読み込み、破線トグルが効くことを確認する。
// 使い方: node tools/check_edge_arrow_style.mjs
import fs from 'fs';
import vm from 'vm';
import path from 'path';
import { fileURLToPath } from 'url';

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.dirname(here);
const canvasJs = fs.readFileSync(path.join(root, 'src', 'canvas.js'), 'utf8');
const editorJs = fs.readFileSync(path.join(root, 'src', 'editor.js'), 'utf8');

function stub() {
  return {
    classList: { add() {}, remove() {}, contains() { return false; } },
    style: {}, value: '', textContent: '', innerHTML: '', scrollTop: 0, selectionStart: 0, selectionEnd: 0,
    setAttribute() {}, getAttribute() { return null; }, removeAttribute() {},
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
const window = { addEventListener() {}, innerWidth: 1080, innerHeight: 720, EditorApp: null };
const context = vm.createContext({ window, document, console, setTimeout, clearTimeout, setInterval, clearInterval, Math, Array, Object, String, Number, RegExp, Set, Map, JSON, Date, isFinite });
vm.runInContext(canvasJs, context);
vm.runInContext(editorJs, context);
const EditorApp = window.EditorApp;
EditorApp.setStatus = () => {};
EditorApp.scheduleSync = () => {};

let failed = 0;
function check(name, cond, extra = '') {
  if (!cond) { console.error(`FAIL ${name}: ${extra}`); failed++; }
}

EditorApp.textareaEl = { value: 'clear\ncard: now [title="今"]\ncard: armor [title="装甲"]\n\nnow -> armor' };
window.selectedEdge = { u: 'now', v: 'armor' };
EditorApp.toggleSelectedEdgeStyle();
check('arrow -> dashed decl', /edge: e\d+ \[from="now", to="armor", dash="5,4"\]/.test(EditorApp.textareaEl.value), EditorApp.textareaEl.value);

EditorApp.textareaEl = { value: 'clear\ncard: now [title="今"]\ncard: armor [title="装甲"]\n\nnow -> armor : 護る' };
window.selectedEdge = { u: 'now', v: 'armor' };
EditorApp.toggleSelectedEdgeStyle();
check('arrow label preserved', /edge: e\d+ \[from="now", to="armor", label="護る", dash="5,4"\]/.test(EditorApp.textareaEl.value), EditorApp.textareaEl.value);

EditorApp.textareaEl = { value: 'clear\ncard: now [title="今"]\ncard: armor [title="装甲"]\n\nedge: e1 [from="now", to="armor"]' };
window.selectedEdge = { u: 'now', v: 'armor' };
EditorApp.toggleSelectedEdgeStyle();
check('standalone still dashed', /edge: e1 \[from="now", to="armor", dash="5,4"\]/.test(EditorApp.textareaEl.value), EditorApp.textareaEl.value);

if (failed) process.exit(1);
console.log('PASS: edge arrow style');

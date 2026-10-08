/* eslint-disable no-console */
const fs = require('fs');
const path = require('path');

function normalizeLatexForKatex(expr) {
  if (expr == null) return '';
  let s = String(expr).replace(/\u00a5/g, '\\').replace(/¥/g, '\\').trim();
  let prev;
  do {
    prev = s;
    s = s.replace(/\\{2}(?=[a-zA-Z])/g, '\\');
  } while (s !== prev);
  return s;
}

const state = JSON.parse(
  fs.readFileSync(path.join(__dirname, 'canvas_state.json'), 'utf8')
);
const detail = state.objects.find((o) => o.id === 'einstein').data.detail;
const un = detail.replace(/\\n(?![a-zA-Z])/g, '\n');
const planck = un.split('\n').find((l) => l.includes('プランク'));
const m = planck.match(/\$([^\$]+)\$/g)[1];
const inner = normalizeLatexForKatex(m.slice(1, -1));
if (!inner.includes('\\times') || inner.includes('\\\\times')) {
  console.error('planck normalize fail', inner);
  process.exit(1);
}
const nuLine = un.split('\n').find((l) => l.includes('振動数'));
const nuInner = nuLine.match(/\*\*([^*]+)\*\*/)[1];
const nu = normalizeLatexForKatex(nuInner.slice(1, -1));
if (nu !== '\\nu') {
  console.error('nu normalize fail', nu);
  process.exit(1);
}
console.log('[ok] detail math normalize:', inner.slice(0, 40), '| nu=', nu);

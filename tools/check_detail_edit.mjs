// detail 編集の往復（エスケープ/パース/改行復元）と配線の検証。
// ai-canvas.html から実物の escapeDetailMarkdown / setQuotedProp / unescapeDetailMarkdown を抽出して走らせる。
// 使い方: node tools/check_detail_edit.mjs
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.dirname(here);
const html = fs.readFileSync(path.join(root, 'ai-canvas.html'), 'utf8');
const canvas = fs.readFileSync(path.join(root, 'src', 'canvas.js'), 'utf8');
const editor = fs.readFileSync(path.join(root, 'src', 'editor.js'), 'utf8');

let failed = 0;
function check(name, cond) {
  if (!cond) { console.error(`FAIL: ${name}`); failed++; }
}

function extractFn(src, marker) {
  const i = src.indexOf(marker);
  if (i < 0) return null;
  const braceStart = src.indexOf('{', i);
  let depth = 0;
  for (let j = braceStart; j < src.length; j++) {
    const c = src[j];
    if (c === '{') depth++;
    else if (c === '}') { depth--; if (depth === 0) return src.slice(i, j + 1); }
  }
  return null;
}

const escSrc = extractFn(html, 'function escapeDetailMarkdown');
const sqSrc = extractFn(html, 'function setQuotedProp');
const unSrc = extractFn(html, 'function unescapeDetailMarkdown');
const qp = html.match(/const QUOTED_PROP_SRC = `[^`]*`;/);
check('ai-canvas.html has escapeDetailMarkdown', !!escSrc);
check('ai-canvas.html has setQuotedProp', !!sqSrc);
check('ai-canvas.html has unescapeDetailMarkdown', !!unSrc);
check('ai-canvas.html has QUOTED_PROP_SRC', !!qp);

// reader regex（applyDSL / normalizeDslText と同一のものをテスト側にも固定）
const READER_SRC = '(?:"((?:\\\\.|[^"\\\\])*)"|\'([^\']*)\'|([^\\s,\\]]+))';
check('canvas.js reader regex in sync', canvas.includes(READER_SRC));
check('editor.js normalize reader regex in sync', editor.includes(READER_SRC));

const factory = new Function(
  `${qp ? qp[0] : ''}\n${escSrc}\n${sqSrc}\n${unSrc}\n` +
  `return { escapeDetailMarkdown, setQuotedProp, unescapeDetailMarkdown };`
);
const { escapeDetailMarkdown, setQuotedProp, unescapeDetailMarkdown } = factory();

// フル往復: 値 → escape → setQuotedProp → reader regex → \" 解除 → \n 解除
function roundTrip(value) {
  const escaped = escapeDetailMarkdown(value);
  const props = setQuotedProp('title="T"', 'detail', escaped);
  const re = new RegExp('([a-zA-Z0-9_-]+)=' + READER_SRC, 'g');
  let detail;
  let m;
  while ((m = re.exec(props)) !== null) {
    if (m[1] === 'detail') detail = m[2] !== undefined ? m[2].replace(/\\"/g, '"') : m[3];
  }
  return unescapeDetailMarkdown(detail);
}

const cases = [
  'plain text',
  'with "quotes" inside',
  'line1\nline2\nline3',
  'English line one\nEnglish line two',
  'LaTeX $\\frac{a}{b} + \\alpha$',
  '$h\\nu$ stays literal',
  'mix: say "hi"\n$\\alpha \\times \\beta$',
  ''
];
for (const c of cases) {
  check(`round-trip: ${JSON.stringify(c).slice(0, 34)}`, roundTrip(c) === c);
}

// 除去: 空値で detail プロップが消える
{
  const props = setQuotedProp('title="T", detail="old"', 'detail', '');
  check('empty removes detail prop', !/detail=/.test(props) && /title="T"/.test(props));
}
// 再設定: 既存の \" を含む detail を置換できる（truncate しない）
{
  const props = setQuotedProp('title="T", detail="a\\"b"', 'detail', 'new\\"val');
  check('replace escaped detail prop', props.includes('detail="new\\"val"') && !props.includes('a\\"b'));
}
// 後方互換: 旧来の \n（次が英字）も数式外なら改行に戻る
{
  check('legacy \\n before letter -> newline', unescapeDetailMarkdown('a\\nb') === 'a\nb');
  check('LaTeX \\nu in math kept', unescapeDetailMarkdown('$h\\nu$') === '$h\\nu$');
}

if (failed === 0) {
  console.log('PASS: detail edit round-trip + wiring');
} else {
  process.exit(1);
}

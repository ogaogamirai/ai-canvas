// setQuotedProp / setLineProp の回帰テスト。
// editor.js から実物を抽出して検証する（色/属性編集の重複排除が挙動を変えていないこと）。
// 使い方: node tools/check_dsl_props.mjs
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.dirname(here);
const js = fs.readFileSync(path.join(root, 'src', 'editor.js'), 'utf8');

function extractFn(src, name) {
  const i = src.indexOf('function ' + name);
  if (i < 0) throw new Error(name + ' not found');
  const b = src.indexOf('{', i);
  let depth = 0;
  let end = -1;
  for (let j = b; j < src.length; j++) {
    const c = src[j];
    if (c === '{') depth++;
    else if (c === '}') {
      depth--;
      if (depth === 0) { end = j + 1; break; }
    }
  }
  return src.slice(i, end);
}

const code =
  extractFn(js, 'setQuotedProp') + '\n' +
  extractFn(js, 'setLineProp') + '\n' +
  'return { setQuotedProp, setLineProp };';
const { setQuotedProp, setLineProp } = new Function(code)();

const cases = [
  // setQuotedProp
  ['setQuotedProp add', setQuotedProp('title="x"', 'color', '#fff'), 'title="x", color="#fff"'],
  ['setQuotedProp replace', setQuotedProp('title="x", color="#000"', 'color', '#fff'), 'title="x", color="#fff"'],
  ['setQuotedProp remove', setQuotedProp('title="x", color="#000"', 'color', ''), 'title="x"'],
  ['setQuotedProp remove-only', setQuotedProp('color="#000"', 'color', ''), ''],
  ['setQuotedProp add-empty', setQuotedProp('', 'color', '#fff'), 'color="#fff"'],
  ['setQuotedProp remove-absent', setQuotedProp('title="x"', 'color', ''), 'title="x"'],
  // setLineProp
  ['setLineProp add', setLineProp('edge: e1 [from="a", to="b"]', 'color', '#fff'), 'edge: e1 [from="a", to="b", color="#fff"]'],
  ['setLineProp replace', setLineProp('edge: e1 [from="a", color="#000"]', 'color', '#fff'), 'edge: e1 [from="a", color="#fff"]'],
  ['setLineProp remove', setLineProp('edge: e1 [from="a", color="#000"]', 'color', ''), 'edge: e1 [from="a"]'],
];

let failed = 0;
for (const [name, got, want] of cases) {
  if (got !== want) {
    console.error(`FAIL ${name}: got ${JSON.stringify(got)} want ${JSON.stringify(want)}`);
    failed++;
  }
}
if (failed) process.exit(1);
console.log(`PASS: ${cases.length} prop cases`);

// detail を持つノードだけ詳細パネルを開くオプションの配線確認。
// 実 DOM 依存のため静的検証（ゲート条件・メニュー・矢印ナビ連動）。
// 使い方: node tools/check_detail_gate.mjs
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.dirname(here);

let failed = 0;
function check(name, cond) {
  if (!cond) { console.error(`FAIL: ${name}`); failed++; }
}

for (const file of ['editor.html', 'index.html']) {
  const html = fs.readFileSync(path.join(root, file), 'utf8');
  check(`${file}: detail gate condition`, html.includes('detailOnlyWithData && !(obj.data && obj.data.detail)'));
  check(`${file}: arrow nav honors option`, html.includes('openDetail: keepPanelOpen || detailOnlyWithData'));
  check(`${file}: toggle method`, html.includes('toggleDetailOnly: function'));
  check(`${file}: menu toggle item`, html.includes('id="menu-detail-only"'));
  check(`${file}: init on load`, html.includes('Canvas.initDetailOption()'));
}

if (failed === 0) {
  console.log('PASS: detail-only gate wired (editor + canvas-only)');
} else {
  process.exit(1);
}

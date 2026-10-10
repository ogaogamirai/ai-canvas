    // ==========================================
    // 📝 DSL Editor App (Phase 1: コアエディタ & リアルタイム同期)
    // ==========================================

    // 🎨 頭上ツールバーの色パレット（node / edge / group 共通・重複排除）
    const TOOLBAR_COLORS = [
      { c: '#38bdf8', t: '水色' },
      { c: '#10b981', t: 'エメラルド' },
      { c: '#f43f5e', t: 'ローズ' },
      { c: '#f59e0b', t: 'アンバー' },
      { c: '#a855f7', t: 'パープル' },
      { c: '#cbd5e1', t: 'デフォルト (解除)', reset: true }
    ];
    function buildColorPalette(method) {
      const frag = document.createDocumentFragment();
      TOOLBAR_COLORS.forEach(({ c, t, reset }) => {
        const span = document.createElement('span');
        span.className = 'color-btn';
        span.style.background = c;
        span.title = reset ? t : `${t} (${c})`;
        span.addEventListener('click', (e) => {
          e.stopPropagation();
          if (window.EditorApp && typeof window.EditorApp[method] === 'function') {
            window.EditorApp[method](reset ? '' : c);
          }
        });
        frag.appendChild(span);
      });
      return frag;
    }

    // 🖊️ エッジ太さプリセット（エッジ頭上ツールバー）
    const EDGE_WIDTHS = [1.0, 1.6, 2.5, 4.0];
    function buildWidthPalette(method) {
      const frag = document.createDocumentFragment();
      EDGE_WIDTHS.forEach(w => {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'tb-btn width-btn';
        btn.title = `太さ ${w}`;
        btn.innerHTML = `<span style="display:block;width:14px;height:${w}px;background:currentColor;border-radius:2px;"></span>`;
        btn.addEventListener('click', (e) => {
          e.stopPropagation();
          if (window.EditorApp && typeof window.EditorApp[method] === 'function') {
            window.EditorApp[method](w);
          }
        });
        frag.appendChild(btn);
      });
      return frag;
    }

    // ↔ エッジ矢印の種類（片 / 両 / なし）
    const EDGE_ARROWS = [
      { v: 'single', label: '→', title: '片矢印（既定）' },
      { v: 'double', label: '↔', title: '両矢印' },
      { v: 'none', label: '—', title: '矢印なし' }
    ];
    function buildArrowPalette(method) {
      const frag = document.createDocumentFragment();
      EDGE_ARROWS.forEach(({ v, label, title }) => {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'tb-btn';
        btn.title = title;
        btn.textContent = label;
        btn.addEventListener('click', (e) => {
          e.stopPropagation();
          if (window.EditorApp && typeof window.EditorApp[method] === 'function') {
            window.EditorApp[method](v);
          }
        });
        frag.appendChild(btn);
      });
      return frag;
    }

    // DSL 行のプロパティ（[ ] の中身）に key="value" を設定/除去する（value 空で除去）。
    // node / edge / group の色・属性編集で共用（重複排除）。
    function setQuotedProp(props, key, value, quote) {
      const re = new RegExp(`${key}=(?:"[^"]*"|'[^']*'|[^\\s,\\]]+)`);
      if (value !== '' && value != null) {
        const token = quote === false ? `${key}=${value}` : `${key}="${value}"`;
        if (re.test(props)) return props.replace(re, token);
        return props.trim() ? `${props}, ${token}` : token;
      }
      if (re.test(props)) {
        return props
          .replace(new RegExp(`,?\\s*${key}=(?:"[^"]*"|'[^']*'|[^\\s,\\]]+)`), '')
          .replace(/^,\s*/, '');
      }
      return props;
    }

    // DSL 行全体（prefix[id props]）に対してプロパティを設定/除去する。
    function setLineProp(line, key, value) {
      const m = line.match(/^(.*?)\[(.*)\]$/);
      if (!m) return line;
      return `${m[1]}[${setQuotedProp(m[2], key, value)}]`;
    }

    const EditorApp = {
      paneEl: null,
      splitterEl: null,
      textareaEl: null,
      lineNumbersEl: null,
      statusDotEl: null,
      statusTextEl: null,
      cursorInfoEl: null,
      openBtnEl: null,
      syncTimer: null,
      isApplyingFromCanvas: false,

      slashMenuEl: null,
      slashListEl: null,
      slashActiveIdx: 0,
      slashQuery: '',
      filteredSlashItems: [],
      autoCounter: 1,

      // スラッシュコマンド定義 (Phase 4 & Phase 5)
      slashCommands: [
        // ノード作成
        { id: 'card', icon: '📦', name: 'Card (思考カード)', key: '/card', template: 'card: c${id} [title="${title}"]' },
        { id: 'math', icon: '🔢', name: 'Math (数式ブロック)', key: '/math', template: 'math: m${id} [title="数式名", latex="E = mc^2"]' },
        { id: 'table', icon: '📊', name: 'Table (比較表)', key: '/table', template: 'table: t${id} [title="比較表", headers="項目A, 項目B", rows="値1|値2; 値3|値4"]' },
        { id: 'text', icon: '📝', name: 'Text (解説ブロック)', key: '/text', template: 'text: tx${id} [title="解説", content="ここに説明文"]' },
        { id: 'group', icon: '🔲', name: 'Group (領域・クラスタ枠)', key: '/group', template: 'group: g${id} [title="グループ名", contains="origin,einstein", color="#38bdf8"]' },
        { id: 'connect', icon: '🔗', name: 'Connect (ノード接続)', key: '/connect', isConnect: true },
        // 思考テンプレート (Phase 5)
        { id: 'prep', icon: '📐', name: 'Template: PREP論旨骨格', key: '/prep', insertRaw: 'card: p1 [title="結論 (Point)"]\ncard: p2 [title="理由 (Reason)"]\ncard: p3 [title="具体例 (Example)"]\ncard: p4 [title="結論の再確認 (Point)"]\nedge: e1 [from="p1", to="p2"]\nedge: e2 [from="p2", to="p3"]\nedge: e3 [from="p3", to="p4"]' },
        { id: 'cause', icon: '🔄', name: 'Template: 因果ループ', key: '/cause', insertRaw: 'card: c_cause [title="要因 (Cause)"]\ncard: c_mech [title="メカニズム"]\ncard: c_effect [title="結果 (Effect)"]\nedge: ec1 [from="c_cause", to="c_mech"]\nedge: ec2 [from="c_mech", to="c_effect"]\nedge: ec3 [from="c_effect", to="c_cause", label="フィードバック"]' },
        { id: 'matrix', icon: '🔲', name: 'Template: 2x2 マトリクス', key: '/matrix', insertRaw: 'card: m_hh [title="高価値・高実現性 (本命)", color="#10b981"]\ncard: m_hl [title="高価値・低実現性 (戦略投資)", color="#38bdf8"]\ncard: m_lh [title="低価値・高実現性 (手軽な改善)", color="#f59e0b"]\ncard: m_ll [title="低価値・低実現性 (見送り)", color="#f43f5e"]' },
        { id: 'tree', icon: '🌲', name: 'Template: 課題解決ツリー', key: '/tree', insertRaw: 'card: tr_problem [title="中核課題 (Problem)", color="#f43f5e"]\ncard: tr_c1 [title="要因1: 技術課題"]\ncard: tr_c2 [title="要因2: プロセス課題"]\ncard: tr_s1 [title="対策A: 自動化"]\ncard: tr_s2 [title="対策B: 標準化"]\nedge: et1 [from="tr_problem", to="tr_c1", label="なぜ？"]\nedge: et2 [from="tr_problem", to="tr_c2", label="なぜ？"]\nedge: et3 [from="tr_c1", to="tr_s1", label="解決策", color="#10b981"]\nedge: et4 [from="tr_c2", to="tr_s2", label="解決策", color="#10b981"]' },
        { id: 'clear', icon: '🧹', name: 'Clear (白紙リセット)', key: '/clear', insertRaw: 'clear\n' },
        // 行内プロパティ修飾 (Phase 4)
        { id: 'contains', icon: '🎯', name: 'Prop: 包含ノード (contains)', key: '/contains', isInlineProp: true, propSnippet: 'contains="origin,einstein"' },
        { id: 'color', icon: '🎨', name: 'Prop: 水色 (#38bdf8)', key: '/color', isInlineProp: true, propSnippet: 'color="#38bdf8"' },
        { id: 'color_green', icon: '🟢', name: 'Prop: エメラルド (#10b981)', key: '/green', isInlineProp: true, propSnippet: 'color="#10b981"' },
        { id: 'color_rose', icon: '🔴', name: 'Prop: ローズ (#f43f5e)', key: '/rose', isInlineProp: true, propSnippet: 'color="#f43f5e"' },
        { id: 'color_amber', icon: '🟡', name: 'Prop: アンバー (#f59e0b)', key: '/amber', isInlineProp: true, propSnippet: 'color="#f59e0b"' },
        { id: 'color_purple', icon: '🟣', name: 'Prop: パープル (#a855f7)', key: '/purple', isInlineProp: true, propSnippet: 'color="#a855f7"' },
        { id: 'sub', icon: '🏷️', name: 'Prop: サブタイトル (sub)', key: '/sub', isInlineProp: true, propSnippet: 'sub="サブタイトル"' },
        { id: 'detail', icon: '📝', name: 'Prop: 詳細Markdown (detail)', key: '/detail', isInlineProp: true, propSnippet: 'detail="# 詳細説明\\nここに内容"' },
        { id: 'dash', icon: '〰️', name: 'Prop: 破線エッジ (dashed)', key: '/dash', isInlineProp: true, propSnippet: 'edge_style="dashed"' },
        { id: 'label', icon: '💬', name: 'Prop: エッジラベル (label)', key: '/label', isInlineProp: true, propSnippet: 'label="関係ラベル"' }
      ],

      // 初期化
      init: function() {
        this.paneEl = document.getElementById('editor-pane');
        this.splitterEl = document.getElementById('splitter');
        this.textareaEl = document.getElementById('dsl-input');
        this.lineNumbersEl = document.getElementById('editor-line-numbers');
        this.statusDotEl = document.getElementById('sync-status-dot');
        this.statusTextEl = document.getElementById('sync-status-text');
        this.cursorInfoEl = document.getElementById('cursor-pos-info');
        this.openBtnEl = document.getElementById('open-editor-btn');
        this.slashMenuEl = document.getElementById('slash-menu');
        this.slashListEl = document.getElementById('slash-menu-list');

        if (!this.textareaEl || this._inited) return;
        this._inited = true;

        this.initSplitter();
        this.initTextareaEvents();
        this.initButtons();
        this.initToolbarPalettes();
        this.updateLineNumbers();

        // 初期DSLをエディタにロード
        setTimeout(() => {
          if (!this.textareaEl.value.trim()) {
            this.loadInitialContent();
          }
        }, 120);
      },

      // スプリッタードラッグ制御
      initSplitter: function() {
        let isDragging = false;
        let startX = 0;
        let startWidth = 0;

        this.splitterEl.addEventListener('mousedown', (e) => {
          isDragging = true;
          startX = e.clientX;
          startWidth = this.paneEl.offsetWidth;
          this.splitterEl.classList.add('dragging');
          document.body.style.cursor = 'col-resize';
          document.body.style.userSelect = 'none';
        });

        window.addEventListener('mousemove', (e) => {
          if (!isDragging) return;
          const dx = e.clientX - startX;
          const newWidth = Math.max(260, Math.min(window.innerWidth * 0.8, startWidth + dx));
          this.paneEl.style.width = newWidth + 'px';
          if (typeof Canvas !== 'undefined' && Canvas.updateViewBox) Canvas.updateViewBox();
        });

        window.addEventListener('mouseup', () => {
          if (!isDragging) return;
          isDragging = false;
          this.splitterEl.classList.remove('dragging');
          document.body.style.cursor = '';
          document.body.style.userSelect = '';
          if (typeof Canvas !== 'undefined' && Canvas.fitView) Canvas.fitView();
        });

        this.splitterEl.addEventListener('dblclick', () => {
          this.paneEl.style.width = '380px';
          if (typeof Canvas !== 'undefined' && Canvas.fitView) Canvas.fitView();
        });
      },

      // エディタの開閉トグル
      toggleCollapse: function(collapse) {
        if (!this.paneEl) this.paneEl = document.getElementById('editor-pane');
        if (!this.splitterEl) this.splitterEl = document.getElementById('splitter');
        if (!this.openBtnEl) this.openBtnEl = document.getElementById('open-editor-btn');
        if (!this.paneEl) return;

        if (collapse === undefined) {
          collapse = !this.paneEl.classList.contains('collapsed');
        }
        if (collapse) {
          const currentWidth = this.paneEl.offsetWidth || 380;
          this.paneEl.style.marginLeft = `-${currentWidth}px`;
          this.paneEl.classList.add('collapsed');
          if (this.splitterEl) this.splitterEl.style.display = 'none';
          if (this.openBtnEl) this.openBtnEl.style.display = 'block';
        } else {
          this.paneEl.classList.remove('collapsed');
          this.paneEl.style.marginLeft = '0px';
          if (this.splitterEl) this.splitterEl.style.display = 'block';
          if (this.openBtnEl) this.openBtnEl.style.display = 'none';
        }
        setTimeout(() => {
          if (typeof Canvas !== 'undefined' && Canvas.fitView) Canvas.fitView();
        }, 260);
      },

      // テキストエリアのイベントリスナー
      initTextareaEvents: function() {
        this.textareaEl.addEventListener('input', () => {
          this.updateLineNumbers();
          this.updateCursorPos();
          this.checkSlashTrigger();
          this.scheduleSync();
        });

        this.textareaEl.addEventListener('scroll', () => {
          this.lineNumbersEl.scrollTop = this.textareaEl.scrollTop;
          this.hideSlashMenu();
        });

        this.textareaEl.addEventListener('keydown', (e) => {
          this.handleKeydown(e);
        });

        ['click', 'keyup', 'focus'].forEach(ev => {
          this.textareaEl.addEventListener(ev, () => {
            this.updateCursorPos();
            this.checkSlashTrigger();
          });
        });

        // 📂 ファイルのドラッグ＆ドロップ読み込み
        this.textareaEl.addEventListener('dragover', (e) => {
          e.preventDefault();
          e.dataTransfer.dropEffect = 'copy';
          this.textareaEl.style.boxShadow = 'inset 0 0 0 2px var(--brand-color)';
        });
        this.textareaEl.addEventListener('dragleave', (e) => {
          e.preventDefault();
          this.textareaEl.style.boxShadow = '';
        });
        this.textareaEl.addEventListener('drop', (e) => {
          e.preventDefault();
          this.textareaEl.style.boxShadow = '';
          const file = e.dataTransfer.files && e.dataTransfer.files[0];
          if (file) {
            const reader = new FileReader();
            reader.onload = (evt) => {
              this.loadDslContent(evt.target.result, file.name);
            };
            reader.onerror = () => {
              this.setStatus('error', 'ファイル読込に失敗しました');
            };
            reader.readAsText(file, 'utf-8');
          }
        });

        document.addEventListener('click', (e) => {
          if (!this.slashMenuEl.contains(e.target) && e.target !== this.textareaEl) {
            this.hideSlashMenu();
          }
        });
      },

      // ボタン操作
      initButtons: function() {
        document.getElementById('btn-collapse-editor')?.addEventListener('click', () => this.toggleCollapse(true));
        document.getElementById('open-editor-btn')?.addEventListener('click', () => this.toggleCollapse(false));
        document.getElementById('btn-load-demo')?.addEventListener('click', () => this.loadDemoDsl());
        document.getElementById('btn-normalize-dsl')?.addEventListener('click', () => this.normalizeDsl());
        document.getElementById('btn-sync-from-canvas')?.addEventListener('click', () => this.syncFromCanvas());
        document.getElementById('btn-import-dsl')?.addEventListener('click', () => this.importDsl());
        document.getElementById('btn-copy-dsl')?.addEventListener('click', () => this.copyDsl());
        document.getElementById('btn-download-dsl')?.addEventListener('click', () => this.downloadDsl());
        document.getElementById('btn-toggle-wrap')?.addEventListener('click', () => this.toggleWrap());

        // ブラウザ用ファイル入力 change イベント
        const fileInput = document.getElementById('dsl-file-input');
        if (fileInput) {
          fileInput.addEventListener('change', (e) => {
            const file = e.target.files && e.target.files[0];
            if (!file) return;
            const reader = new FileReader();
            reader.onload = (evt) => {
              this.loadDslContent(evt.target.result, file.name);
            };
            reader.onerror = () => {
              this.setStatus('error', 'ファイル読込に失敗しました');
            };
            reader.readAsText(file, 'utf-8');
          });
        }
      },

      // 頭上ツールバーの色パレットを生成（node/edge/group の重複を排除）
      initToolbarPalettes: function() {
        document.querySelectorAll('.tb-palette').forEach(el => {
          el.replaceChildren(buildColorPalette(el.dataset.method));
        });
        document.querySelectorAll('.tb-widths').forEach(el => {
          el.replaceChildren(buildWidthPalette(el.dataset.widthMethod));
        });
        document.querySelectorAll('.tb-arrows').forEach(el => {
          el.replaceChildren(buildArrowPalette(el.dataset.arrowMethod));
        });
      },

      // 行番号更新
      updateLineNumbers: function() {
        const lines = this.textareaEl.value.split('\n');
        let nums = '';
        for (let i = 1; i <= lines.length; i++) {
          nums += i + '\n';
        }
        this.lineNumbersEl.textContent = nums;
        this.lineNumbersEl.scrollTop = this.textareaEl.scrollTop;
      },

      // カーソル位置情報表示
      updateCursorPos: function() {
        const text = this.textareaEl.value;
        const selStart = this.textareaEl.selectionStart;
        const textUpToCursor = text.substring(0, selStart);
        const lines = textUpToCursor.split('\n');
        const line = lines.length;
        const col = lines[lines.length - 1].length + 1;
        this.cursorInfoEl.textContent = `Ln ${line}, Col ${col}`;
      },

      // スラッシュメニューの出現判定
      checkSlashTrigger: function() {
        const selStart = this.textareaEl.selectionStart;
        const text = this.textareaEl.value;
        const textUpToCursor = text.substring(0, selStart);
        const lastLineStart = textUpToCursor.lastIndexOf('\n') + 1;
        const currentLine = textUpToCursor.substring(lastLineStart);

        const slashMatch = currentLine.match(/\/([a-zA-Z0-9_-]*)$/);
        if (slashMatch) {
          this.slashQuery = slashMatch[1].toLowerCase();
          this.showSlashMenu();
        } else {
          this.hideSlashMenu();
        }
      },

      showSlashMenu: function() {
        if (!this.slashMenuEl) return;
        this.filteredSlashItems = this.slashCommands.filter(item => {
          return item.key.toLowerCase().includes(this.slashQuery) || item.name.toLowerCase().includes(this.slashQuery);
        });

        if (this.filteredSlashItems.length === 0) {
          this.hideSlashMenu();
          return;
        }

        this.slashActiveIdx = 0;
        this.renderSlashList();

        // 簡易カーソル位置追従
        const selStart = this.textareaEl.selectionStart;
        const textUpToCursor = this.textareaEl.value.substring(0, selStart);
        const lineCount = textUpToCursor.split('\n').length;
        const topPos = Math.min(this.paneEl.offsetHeight - 260, Math.max(48, lineCount * 20 + 20 - this.textareaEl.scrollTop));
        this.slashMenuEl.style.top = topPos + 'px';
        this.slashMenuEl.style.left = '48px';
        this.slashMenuEl.classList.add('open');
      },

      hideSlashMenu: function() {
        if (this.slashMenuEl) this.slashMenuEl.classList.remove('open');
      },

      renderSlashList: function() {
        this.slashListEl.innerHTML = '';
        this.filteredSlashItems.forEach((item, idx) => {
          const div = document.createElement('div');
          div.className = 'slash-item' + (idx === this.slashActiveIdx ? ' active' : '');
          div.innerHTML = `
            <div class="slash-item-left">
              <span class="slash-icon">${item.icon}</span>
              <span>${item.name}</span>
            </div>
            <span class="slash-item-key">${item.key}</span>
          `;
          div.addEventListener('click', () => {
            this.executeSlashCommand(item);
          });
          this.slashListEl.appendChild(div);
        });
      },

      executeSlashCommand: function(item) {
        const selStart = this.textareaEl.selectionStart;
        const val = this.textareaEl.value;
        const textUpToCursor = val.substring(0, selStart);
        const lastLineStart = textUpToCursor.lastIndexOf('\n') + 1;
        const lineBeforeSlash = textUpToCursor.substring(lastLineStart).replace(/\/([a-zA-Z0-9_-]*)$/, '');

        let insertText = '';
        const idNum = this.autoCounter++;

        if (item.id === 'group') {
          this.hideSlashMenu();
          this.openGroupPicker(lastLineStart, lineBeforeSlash, selStart);
          return;
        }

        if (item.isInlineProp) {
          // 行内プロパティ修飾 (Phase 4)
          if (lineBeforeSlash.includes('[')) {
            const hasPropBefore = /\[\s*[^\]\s]/.test(lineBeforeSlash);
            insertText = hasPropBefore ? `, ${item.propSnippet}` : item.propSnippet;
          } else {
            insertText = ` [${item.propSnippet}]`;
          }
        } else if (item.isConnect) {
          // 既存ノード一覧から接続行を自動生成
          const existingIds = [];
          if (window.Canvas && typeof objects !== 'undefined') {
            objects.forEach(o => { if (o.type !== 'group') existingIds.push(o.id); });
          }
          const fromId = existingIds[0] || 'node1';
          const toId = existingIds[1] || 'node2';
          insertText = `edge: e${idNum} [from="${fromId}", to="${toId}"]`;
        } else if (item.insertRaw) {
          insertText = item.insertRaw;
        } else {
          insertText = item.template.replace('${id}', idNum).replace('${title}', '新規ノード');
        }

        const newText = val.substring(0, lastLineStart) + lineBeforeSlash + insertText + val.substring(selStart);
        this.textareaEl.value = newText;
        const newCursor = lastLineStart + lineBeforeSlash.length + insertText.length;
        this.textareaEl.selectionStart = this.textareaEl.selectionEnd = newCursor;

        this.hideSlashMenu();
        this.updateLineNumbers();
        this.scheduleSync();
        this.textareaEl.focus();
      },

      // Tabキー & 自動インデント & 平文の即時DSL補正
      handleKeydown: function(e) {
        // スラッシュメニュー展開時のキーナビゲーション
        if (this.slashMenuEl && this.slashMenuEl.classList.contains('open')) {
          if (e.key === 'ArrowDown') {
            e.preventDefault();
            this.slashActiveIdx = (this.slashActiveIdx + 1) % this.filteredSlashItems.length;
            this.renderSlashList();
            return;
          } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            this.slashActiveIdx = (this.slashActiveIdx - 1 + this.filteredSlashItems.length) % this.filteredSlashItems.length;
            this.renderSlashList();
            return;
          } else if (e.key === 'Enter' || e.key === 'Tab') {
            e.preventDefault();
            const chosen = this.filteredSlashItems[this.slashActiveIdx];
            if (chosen) this.executeSlashCommand(chosen);
            return;
          } else if (e.key === 'Escape') {
            e.preventDefault();
            this.hideSlashMenu();
            return;
          }
        }

        if (e.key === 'Tab') {
          e.preventDefault();
          const start = this.textareaEl.selectionStart;
          const end = this.textareaEl.selectionEnd;
          const val = this.textareaEl.value;

          if (e.shiftKey) {
            const lineStart = val.lastIndexOf('\n', start - 1) + 1;
            if (val.substring(lineStart, lineStart + 2) === '  ') {
              this.textareaEl.value = val.substring(0, lineStart) + val.substring(lineStart + 2);
              this.textareaEl.selectionStart = this.textareaEl.selectionEnd = Math.max(lineStart, start - 2);
            }
          } else {
            this.textareaEl.value = val.substring(0, start) + '  ' + val.substring(end);
            this.textareaEl.selectionStart = this.textareaEl.selectionEnd = start + 2;
          }
          this.updateLineNumbers();
          this.scheduleSync();
        } else if (e.key === 'Enter') {
          // 🌟 平文の即時DSL補正（B派・即時補正）
          const start = this.textareaEl.selectionStart;
          const val = this.textareaEl.value;
          const lastLineStart = val.lastIndexOf('\n', start - 1) + 1;
          const currentLine = val.substring(lastLineStart, start);
          const trimmed = currentLine.trim();

          // まだ正規DSLになっておらず、平文（コロンも矢印もない単語）の場合
          if (trimmed && !trimmed.includes(':') && !trimmed.includes('->') && !trimmed.startsWith('#') && trimmed !== 'clear') {
            e.preventDefault();
            const idNum = this.autoCounter++;
            const cleanTitle = trimmed.replace(/^\[(.*)\]$/, '$1');
            const dslReplacement = `card: c${idNum} [title="${cleanTitle}"]`;
            this.textareaEl.value = val.substring(0, lastLineStart) + dslReplacement + '\n' + val.substring(start);
            this.textareaEl.selectionStart = this.textareaEl.selectionEnd = lastLineStart + dslReplacement.length + 1;
            this.updateLineNumbers();
            this.scheduleSync();
            return;
          }

          // 自動インデント
          const match = currentLine.match(/^(\s+)/);
          if (match) {
            e.preventDefault();
            const indent = match[1];
            this.textareaEl.value = val.substring(0, start) + '\n' + indent + val.substring(start);
            this.textareaEl.selectionStart = this.textareaEl.selectionEnd = start + 1 + indent.length;
            this.updateLineNumbers();
            this.scheduleSync();
          }
        }
      },

      // キャンバス上のエッジクリック時にエディタ該当行をハイライト
      highlightEdgeLine: function(fromId, toId, idx) {
        if (!this.textareaEl) return;
        const lines = this.textareaEl.value.split('\n');
        let targetLineIdx = -1;

        // 1. edge: ... [from="...", to="..."] を探す
        lines.forEach((line, i) => {
          if (targetLineIdx !== -1) return;
          if (line.includes(`from="${fromId}"`) && line.includes(`to="${toId}"`)) {
            targetLineIdx = i;
          } else if (line.includes(`${fromId} -> ${toId}`) || line.includes(`${fromId}->${toId}`)) {
            targetLineIdx = i;
          } else if (line.includes(`to="${toId}"`) && line.includes(fromId)) {
            targetLineIdx = i;
          }
        });

        if (targetLineIdx !== -1) {
          let charPos = 0;
          for (let i = 0; i < targetLineIdx; i++) {
            charPos += lines[i].length + 1;
          }
          const lineLength = lines[targetLineIdx].length;
          this.textareaEl.focus();
          this.textareaEl.setSelectionRange(charPos, charPos + lineLength);
          this.updateCursorPos();

          // スクロール位置合わせ
          const lineHeight = 20;
          this.textareaEl.scrollTop = Math.max(0, targetLineIdx * lineHeight - 60);
          this.lineNumbersEl.scrollTop = this.textareaEl.scrollTop;
          this.setStatus('ready', `[エッジ行選択] Ln ${targetLineIdx + 1}`);
        }
      },

      // 🌟 キャンバスドラッグ結線からの自動追記 (Phase 3)
      appendEdgeLine: function(fromId, toId) {
        if (!this.textareaEl) return;
        const idNum = this.autoCounter++;
        const newEdge = `edge: e${idNum} [from="${fromId}", to="${toId}"]`;
        const val = this.textareaEl.value.trimEnd();
        this.textareaEl.value = val + '\n' + newEdge + '\n';
        this.updateLineNumbers();
        this.updateCursorPos();
        this.scheduleSync();
        this.setStatus('ready', `[結線追記 🔗] ${fromId} ➔ ${toId}`);
      },

      // 🌟 クイックツールバーからの色変更 (Phase 4)
      changeSelectedNodeColor: function(color) {
        const targetId = window.selectedNodeId;
        if (!targetId || !this.textareaEl) return;
        const lines = this.textareaEl.value.split('\n');
        let modified = false;

        for (let i = 0; i < lines.length; i++) {
          const m = lines[i].trim().match(/^([a-zA-Z0-9_-]+):\s*([a-zA-Z0-9_-]+)\s*\[(.*)\]$/);
          if (m && m[2] === targetId) {
            lines[i] = `${m[1]}: ${m[2]} [${setQuotedProp(m[3], 'color', color)}]`;
            modified = true;
            break;
          }
        }

        if (modified) {
          this.textareaEl.value = lines.join('\n');
          this.scheduleSync();
          this.setStatus('ready', `[ノード色更新 🎨] #${targetId} ➔ ${color || 'デフォルト'}`);
        }
      },

      // 🌟 クイックツールバーからのノード削除 (Phase 4)
      deleteSelectedNode: function() {
        const targetId = window.selectedNodeId || (typeof selectedNodeId !== 'undefined' ? selectedNodeId : null);
        if (!targetId || !this.textareaEl) return;
        const val = this.textareaEl.value;
        const lines = val.split('\n');
        const newLines = [];

        for (let i = 0; i < lines.length; i++) {
          const line = lines[i].trim();
          const m = line.match(/^([a-zA-Z0-9_-]+):\s*([a-zA-Z0-9_-]+)\s*\[(.*)\]$/);
          if (m && m[2] === targetId) continue;
          if (line.includes(`from="${targetId}"`) || line.includes(`to="${targetId}"`) || line.includes(`${targetId} ->`) || line.includes(`-> ${targetId}`)) {
            continue;
          }
          newLines.push(lines[i]);
        }

        this.textareaEl.value = newLines.join('\n');
        if (typeof selectNode === 'function') selectNode(null);
        this.updateLineNumbers();
        this.updateCursorPos();
        this.scheduleSync();
        this.setStatus('ready', `[ノード削除 🗑️] #${targetId} を削除しました`);
      },

      // 🌟 クイックツールバーからのグループ色変更 (Phase 5)
      changeSelectedGroupColor: function(color) {
        const targetId = window.selectedNodeId;
        if (!targetId || !this.textareaEl) return;
        const lines = this.textareaEl.value.split('\n');
        let modified = false;

        for (let i = 0; i < lines.length; i++) {
          const m = lines[i].trim().match(/^(?:group:\s*|group\s+)([a-zA-Z0-9_-]+)\s*(?:\[(.*)\])?$/);
          if (m && m[1] === targetId) {
            lines[i] = `group: ${targetId} [${setQuotedProp(m[2] || '', 'color', color)}]`;
            modified = true;
            break;
          }
        }

        if (modified) {
          this.textareaEl.value = lines.join('\n');
          this.scheduleSync();
          this.setStatus('ready', `[グループ色更新 🎨] #${targetId} ➔ ${color || 'デフォルト'}`);
        }
      },

      // 🌟 クイックツールバーからのグループ枠解除（ノードは一切削除せず領域のみ解除）
      deleteSelectedGroup: function() {
        const targetId = window.selectedNodeId;
        if (!targetId || !this.textareaEl) return;
        const lines = this.textareaEl.value.split('\n');
        const newLines = [];
        let deleted = false;

        for (let i = 0; i < lines.length; i++) {
          const line = lines[i].trim();
          const m = line.match(/^(?:group:\s*|group\s+)([a-zA-Z0-9_-]+)\b/);
          if (m && m[1] === targetId) {
            deleted = true;
            continue; // グループ行のみスキップ（削除）
          }
          newLines.push(lines[i]);
        }

        if (deleted) {
          this.textareaEl.value = newLines.join('\n');
          if (typeof Canvas !== 'undefined' && typeof Canvas.selectNode === 'function') {
            Canvas.selectNode(null);
          }
          this.updateLineNumbers();
          this.updateCursorPos();
          this.scheduleSync();
          this.setStatus('ready', `[グループ解除 🗑️] グループ #${targetId} を解除しました（所属ノードは残置）`);
        }
      },

      // 🌟 既存グループ編集ピッカー起動
      openEditGroupPicker: function(groupId) {
        const targetId = groupId || window.selectedNodeId;
        if (!targetId) return;
        this.openGroupPicker({ editingGroupId: targetId });
      },

      // 🌟 ノード/グループ選択時のエディタ行フォーカス
      highlightNodeLine: function(nodeId) {
        if (!this.textareaEl || !nodeId) return;
        const lines = this.textareaEl.value.split('\n');
        let targetLineIdx = -1;
        let charOffset = 0;
        for (let i = 0; i < lines.length; i++) {
          const line = lines[i].trim();
          const m = line.match(/^(?:[a-zA-Z0-9_-]+:\s*|[a-zA-Z0-9_-]+\s+)([a-zA-Z0-9_-]+)\b/);
          if (m && m[1] === nodeId) {
            targetLineIdx = i;
            break;
          }
          charOffset += lines[i].length + 1;
        }
        if (targetLineIdx !== -1) {
          try {
            this.textareaEl.selectionStart = charOffset;
            this.textareaEl.selectionEnd = charOffset + lines[targetLineIdx].length;
            const lineHeight = 19;
            this.textareaEl.scrollTop = Math.max(0, targetLineIdx * lineHeight - 60);
            this.updateCursorPos();
          } catch (_) {}
        }
      },

      // 🌟 エッジ情報の特定 (独立 edge 行 & ノード行内インライン定義の両方を完全サポート)
      findSelectedEdgeInfo: function() {
        const edge = window.selectedEdge || null;
        if (!edge) return null;
        const u = edge.u;
        const v = edge.v;
        const lines = this.textareaEl.value.split('\n');

        // 1. 独立した edge: 行を探す (edge: eX [from="u", to="v"])
        for (let i = 0; i < lines.length; i++) {
          const line = lines[i];
          if (/^edge:\s*/.test(line)) {
            if (line.includes(`from="${u}"`) && line.includes(`to="${v}"`)) {
              return { lineIdx: i, type: 'edge_decl', u, v };
            }
          }
          if (line.includes(`${u} -> ${v}`) || line.includes(`${u}->${v}`)) {
            return { lineIdx: i, type: 'edge_arrow', u, v };
          }
        }

        // 2. ノード行内のインラインエッジ (u の定義行に to="v" がある)
        for (let i = 0; i < lines.length; i++) {
          const line = lines[i];
          const m = line.match(/^([a-z]+):\s*([a-zA-Z0-9_-]+)\s*\[(.*)\]$/);
          if (m && m[2] === u) {
            if (line.includes(`to="${v}"`)) {
              return { lineIdx: i, type: 'inline_node', u, v, nodeId: u };
            }
          }
        }

        // 3. 逆方向インライン (v の定義行に to="u" がある場合)
        for (let i = 0; i < lines.length; i++) {
          const line = lines[i];
          const m = line.match(/^([a-z]+):\s*([a-zA-Z0-9_-]+)\s*\[(.*)\]$/);
          if (m && m[2] === v) {
            if (line.includes(`to="${u}"`)) {
              return { lineIdx: i, type: 'inline_node_rev', u, v, nodeId: v };
            }
          }
        }

        return null;
      },

      // edge_arrow（A -> B 形式）を standalone edge: 行へ正規化し、スタイル編集を可能にする
      toEdgeDecl: function(info, lines) {
        if (info.type !== 'edge_arrow') return;
        const m = lines[info.lineIdx].match(/^\s*([^\s\-]+)\s*->\s*([^\s:]+)(?:\s*:\s*(.*))?$/);
        const label = m && m[3] ? m[3].trim() : '';
        const props = [`from="${info.u}"`, `to="${info.v}"`];
        if (label) props.push(`label="${label}"`);
        lines[info.lineIdx] = `edge: e${this.autoCounter++} [${props.join(', ')}]`;
        info.type = 'edge_decl';
      },

      changeSelectedEdgeColor: function(color) {
        const info = this.findSelectedEdgeInfo();
        if (!info) return;
        const lines = this.textareaEl.value.split('\n');
        this.toEdgeDecl(info, lines);
        const inline = (info.type === 'inline_node' || info.type === 'inline_node_rev');
        // インラインは edge_color、独立 edge 行は color を使う
        lines[info.lineIdx] = setLineProp(lines[info.lineIdx], inline ? 'edge_color' : 'color', color);
        this.textareaEl.value = lines.join('\n');
        this.scheduleSync();
        this.setStatus('ready', `[エッジ色更新 🎨] ${info.u} ➔ ${info.v} (${color || 'デフォルト'})`);
      },

      // エッジの太さを設定（プリセットボタンから）
      setSelectedEdgeWidth: function(w) {
        const info = this.findSelectedEdgeInfo();
        if (!info) return;
        const lines = this.textareaEl.value.split('\n');
        this.toEdgeDecl(info, lines);
        const inline = (info.type === 'inline_node' || info.type === 'inline_node_rev');
        const m = lines[info.lineIdx].match(/^(.*?)\[(.*)\]$/);
        if (m) {
          const key = inline ? 'edge_width' : 'width';
          lines[info.lineIdx] = `${m[1]}[${setQuotedProp(m[2], key, String(w), false)}]`;
        }
        this.textareaEl.value = lines.join('\n');
        this.scheduleSync();
        this.setStatus('ready', `[エッジ太さ 🖊️] ${info.u} ➔ ${info.v} (${w})`);
      },

      // エッジ矢印の種類（片 / 両 / なし）を設定
      setSelectedEdgeArrow: function(kind) {
        const info = this.findSelectedEdgeInfo();
        if (!info) return;
        const lines = this.textareaEl.value.split('\n');
        this.toEdgeDecl(info, lines);
        const inline = (info.type === 'inline_node' || info.type === 'inline_node_rev');
        const key = inline ? 'edge_arrow' : 'arrow';
        const m = lines[info.lineIdx].match(/^(.*?)\[(.*)\]$/);
        if (m) {
          // 片矢印は既定なので prop を除去
          const val = (kind === 'single') ? '' : kind;
          lines[info.lineIdx] = `${m[1]}[${setQuotedProp(m[2], key, val, false)}]`;
        }
        this.textareaEl.value = lines.join('\n');
        this.scheduleSync();
        const label = kind === 'double' ? '両矢印 ↔' : (kind === 'none' ? '矢印なし —' : '片矢印 →');
        this.setStatus('ready', `[エッジ矢印 ${label}] ${info.u} ➔ ${info.v}`);
      },

      toggleSelectedEdgeStyle: function() {
        const info = this.findSelectedEdgeInfo();
        if (!info) return;
        const lines = this.textareaEl.value.split('\n');
        this.toEdgeDecl(info, lines);
        let line = lines[info.lineIdx];

        if (info.type === 'inline_node' || info.type === 'inline_node_rev') {
          if (line.includes('edge_dash=') || line.includes('edge_style="dashed"')) {
            line = line.replace(/,?\s*edge_dash="[^"]*"/, '')
                       .replace(/,?\s*edge_dash=[^\s,\]]+/, '')
                       .replace(/,?\s*edge_style="[^"]*"/, '')
                       .replace(/\[\s*,/, '[');
            this.setStatus('ready', '[エッジ実線化 〰️] 実線に切り替えました');
          } else {
            line = line.replace(/\]$/, ', edge_dash="5,4"]').replace(/\[\s*,/, '[');
            this.setStatus('ready', '[エッジ破線化 〰️] 破線に切り替えました');
          }
        } else {
          if (line.includes('dash=') || line.includes('edge_style="dashed"')) {
            line = line.replace(/,?\s*dash="[^"]*"/, '')
                       .replace(/,?\s*dash=[^\s,\]]+/, '')
                       .replace(/,?\s*edge_style="[^"]*"/, '')
                       .replace(/\[\s*,/, '[');
            this.setStatus('ready', '[エッジ実線化 〰️] 実線に切り替えました');
          } else {
            line = line.replace(/\]$/, ', dash="5,4"]').replace(/\[\s*,/, '[');
            this.setStatus('ready', '[エッジ破線化 〰️] 破線に切り替えました');
          }
        }

        lines[info.lineIdx] = line;
        this.textareaEl.value = lines.join('\n');
        this.scheduleSync();
      },

      promptSelectedEdgeLabel: function() {
        const info = this.findSelectedEdgeInfo();
        if (!info) return;
        const lines = this.textareaEl.value.split('\n');
        this.toEdgeDecl(info, lines);
        let line = lines[info.lineIdx];
        const match = line.match(/(?:label|link)="([^"]*)"/);
        const currentLabel = match ? match[1] : '';
        const newLabel = window.prompt('エッジのラベルを入力してください:', currentLabel);
        if (newLabel === null) return;

        const propKey = (info.type === 'inline_node' || info.type === 'inline_node_rev') ? 'link' : 'label';

        if (/(?:label|link)="[^"]*"/.test(line)) {
          if (newLabel.trim()) {
            line = line.replace(/(?:label|link)="[^"]*"/, `${propKey}="${newLabel.trim()}"`);
          } else {
            line = line.replace(/,?\s*(?:label|link)="[^"]*"/, '').replace(/\[\s*,/, '[');
          }
        } else if (newLabel.trim()) {
          line = line.replace(/\]$/, `, ${propKey}="${newLabel.trim()}"]`).replace(/\[\s*,/, '[');
        }

        lines[info.lineIdx] = line;
        this.textareaEl.value = lines.join('\n');
        this.scheduleSync();
        this.setStatus('ready', `[エッジラベル更新 🏷️] ${newLabel || '削除'}`);
      },

      deleteSelectedEdge: function() {
        const info = this.findSelectedEdgeInfo();
        if (!info) return;
        const lines = this.textareaEl.value.split('\n');
        this.toEdgeDecl(info, lines);

        if (info.type === 'inline_node' || info.type === 'inline_node_rev') {
          // ノード本体は削除せず、エッジ関連属性のみを綺麗に除去！
          let line = lines[info.lineIdx];
          line = line.replace(/,?\s*to="[^"]*"/, '')
                     .replace(/,?\s*link="[^"]*"/, '')
                     .replace(/,?\s*label="[^"]*"/, '')
                     .replace(/,?\s*edge_color="[^"]*"/, '')
                     .replace(/,?\s*edge_width=[^\s,\]]+/, '')
                     .replace(/,?\s*edge_style="[^"]*"/, '')
                     .replace(/\[\s*,/, '[');
          lines[info.lineIdx] = line;
        } else {
          // 独立 edge 行の場合は行ごと削除
          lines.splice(info.lineIdx, 1);
        }

        this.textareaEl.value = lines.join('\n');
        if (typeof selectEdge === 'function') selectEdge(null);
        this.updateLineNumbers();
        this.updateCursorPos();
        this.scheduleSync();
        this.setStatus('ready', '[エッジ削除 🗑️] 結線を削除しました');
      },

      // ↩ 折り返しトグル (Wrap)
      isWrapEnabled: true,
      toggleWrap: function() {
        this.isWrapEnabled = !this.isWrapEnabled;
        const btn = document.getElementById('btn-toggle-wrap');
        if (this.isWrapEnabled) {
          this.textareaEl.classList.remove('no-wrap');
          if (btn) btn.textContent = '↩ 折り返し: ON';
          this.setStatus('ready', '折り返し表示を有効にしました');
        } else {
          this.textareaEl.classList.add('no-wrap');
          if (btn) btn.textContent = '↩ 折り返し: OFF';
          this.setStatus('ready', '折り返し表示を無効（横スクロール）にしました');
        }
      },

      // 🌟 DSLコピー & 保存 (Phase 5)
      copyDsl: function() {
        if (!this.textareaEl) return;
        navigator.clipboard.writeText(this.textareaEl.value)
          .then(() => this.setStatus('ready', 'DSLをクリップボードにコピーしました 📋'))
          .catch(() => this.setStatus('error', 'コピーに失敗しました'));
      },

      // 🌟 DSL保存 (WebView2 IPC & ブラウザ両対応)
      downloadDsl: function() {
        if (!this.textareaEl) return;
        const dslText = this.textareaEl.value;
        const api = (window.pywebview && window.pywebview.api) ? window.pywebview.api : null;
        const fn = api ? (api.save_dsl || api.saveDsl) : null;
        if (fn) {
          fn.call(api, dslText)
            .then(res => {
              this.setStatus('ready', `[保存成功 💾] ${res}`);
            })
            .catch(err => {
              this.setStatus('error', `[保存エラー ⚠️] ${err}`);
            });
          return;
        }

        // ブラウザ単体フォールバック (Blob download)
        try {
          const blob = new Blob([dslText], { type: 'text/plain;charset=utf-8' });
          const url = URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = `canvas_diagram_${new Date().toISOString().slice(0, 10)}.dsl`;
          document.body.appendChild(a);
          a.click();
          document.body.removeChild(a);
          URL.revokeObjectURL(url);
          this.setStatus('ready', 'DSLテキストをダウンロード保存しました 💾');
        } catch (e) {
          this.setStatus('error', '保存処理に失敗しました');
        }
      },

      // 🌟 DSLインポート (WebView2 IPC & ブラウザ両対応)
      importDsl: function() {
        const api = (window.pywebview && window.pywebview.api) ? window.pywebview.api : null;
        const fn = api ? (api.open_dsl_file || api.openDslFile) : null;
        if (fn) {
          fn.call(api)
            .then(res => {
              if (res && res.success && res.content) {
                this.loadDslContent(res.content, res.filename || '選択ファイル');
              } else if (res && res.cancelled) {
                // キャンセル時は静かに終了
              } else if (res && res.error) {
                this.setStatus('error', `読込エラー: ${res.error}`);
              }
            })
            .catch(() => {
              // IPC失敗時はブラウザ用inputにフォールバック
              const fileInput = document.getElementById('dsl-file-input');
              if (fileInput) {
                fileInput.value = '';
                fileInput.click();
              }
            });
          return;
        }

        const fileInput = document.getElementById('dsl-file-input');
        if (fileInput) {
          fileInput.value = '';
          fileInput.click();
        }
      },

      // DSLテキストをエディタに展開・キャンバス反映
      loadDslContent: function(content, filename) {
        if (typeof content !== 'string') return;
        this.textareaEl.value = content;
        this.updateLineNumbers();
        this.updateCursorPos();
        this.applyToCanvas();
        this.setStatus('ready', `DSLを読込完了 📂 (${filename || 'インポート'})`);
      },

      // 🔲 グループ作成ピッカーモーダル制御 (Phase 5: 案A 実装)
      groupPickerContext: null,

      openGroupPicker: function(contextOrOpts, lineBeforeSlash, selStart) {
        let isEditing = false;
        let editingGroupId = null;
        let initialTitle = '新規グループ';
        const existingContainsSet = new Set();
        let existingColor = '#38bdf8';

        if (contextOrOpts && typeof contextOrOpts === 'object' && contextOrOpts.editingGroupId) {
          isEditing = true;
          editingGroupId = contextOrOpts.editingGroupId;
          this.groupPickerContext = { editingGroupId };
        } else if (contextOrOpts !== undefined && typeof contextOrOpts === 'number') {
          // スラッシュコマンド等からの呼出 (lastLineStart, lineBeforeSlash, selStart)
          this.groupPickerContext = { lastLineStart: contextOrOpts, lineBeforeSlash, selStart };
        } else {
          // クイックツールバー等の通常呼び出し
          // もし現在選択中のノードがグループなら自動で編集モードにする！
          if (window.selectedNodeId) {
            const st = typeof Canvas !== 'undefined' && Canvas.getFullState ? Canvas.getFullState() : null;
            const maybeGroup = st && st.objects && st.objects.find(o => o.id === window.selectedNodeId && o.type === 'group');
            if (maybeGroup) {
              isEditing = true;
              editingGroupId = window.selectedNodeId;
              this.groupPickerContext = { editingGroupId };
            } else {
              this.groupPickerContext = null;
            }
          } else {
            this.groupPickerContext = null;
          }
        }

        const overlay = document.getElementById('group-picker-overlay');
        const listEl = document.getElementById('group-picker-node-list');
        const titleInput = document.getElementById('group-picker-title');
        const modalTitle = document.querySelector('#group-picker-overlay .group-picker-header h3');
        const submitBtn = document.getElementById('btn-submit-group-picker');
        if (!overlay || !listEl) return;

        if (isEditing) {
          if (typeof Canvas !== 'undefined' && typeof Canvas.getFullState === 'function') {
            const st = Canvas.getFullState();
            const gObj = st && st.objects && st.objects.find(o => o.id === editingGroupId);
            if (gObj && gObj.data) {
              if (gObj.data.title) initialTitle = gObj.data.title;
              if (gObj.data.color) existingColor = gObj.data.color;
              if (gObj.data.contains) {
                String(gObj.data.contains).split(/[\s,]+/).filter(Boolean).forEach(id => existingContainsSet.add(id));
              }
            }
          }
          if (modalTitle) modalTitle.innerHTML = `<span>🔲</span> グループ構成を編集 (#${editingGroupId})`;
          if (submitBtn) submitBtn.innerHTML = `💾 更新`;
        } else {
          if (modalTitle) modalTitle.innerHTML = `<span>🔲</span> グループ（領域）作成`;
          if (submitBtn) submitBtn.innerHTML = `🔲 作成`;
        }

        // 現在キャンバス上の実在ノード一覧を取得
        let existingNodes = [];
        if (typeof Canvas !== 'undefined' && typeof Canvas.getNodeList === 'function') {
          existingNodes = Canvas.getNodeList();
        } else if (typeof Canvas !== 'undefined' && typeof Canvas.getFullState === 'function') {
          const state = Canvas.getFullState();
          if (state && Array.isArray(state.objects)) {
            existingNodes = state.objects
              .filter(o => o.type !== 'group')
              .map(o => {
                const d = o.data || {};
                const title = d.title || d.name || d.label || d.expr || o.id;
                const color = d.color || d.border || '#38bdf8';
                return { id: o.id, title, color };
              });
          }
        }
        // 万が一キャンバス上に見当たらない場合、DSLテキストからノードIDを抽出するフォールバック
        if (existingNodes.length === 0 && this.textareaEl && this.textareaEl.value) {
          const dslLines = this.textareaEl.value.split('\n');
          dslLines.forEach(line => {
            const trimmed = line.trim();
            if (!trimmed || trimmed.startsWith('#')) return;
            const parts = trimmed.split(/\s+/);
            const cmd = parts[0].toLowerCase();
            if (['card', 'math', 'svg', 'table', 'text'].includes(cmd) && parts[1]) {
              existingNodes.push({
                id: parts[1],
                title: parts[1],
                color: cmd === 'math' ? '#10b981' : (cmd === 'table' ? '#6366f1' : '#38bdf8')
              });
            }
          });
        }

        listEl.innerHTML = '';
        if (existingNodes.length === 0) {
          listEl.innerHTML = '<div style="padding:12px; text-align:center; color:var(--log-color); font-size:11px;">現在キャンバスにノードがありません。<br>空のグループを作成します。</div>';
        } else {
          existingNodes.forEach(node => {
            const item = document.createElement('div');
            item.className = 'group-node-item';
            const isInitiallyChecked = isEditing ? existingContainsSet.has(node.id) : (window.selectedNodeId === node.id);
            item.innerHTML = `
              <input type="checkbox" id="chk_grp_${node.id}" value="${node.id}" ${isInitiallyChecked ? 'checked' : ''}>
              <span class="group-node-color-dot" style="background:${node.color};"></span>
              <span class="group-node-id">#${node.id}</span>
              <span class="group-node-title">${node.title}</span>
            `;
            item.addEventListener('click', (e) => {
              if (e.target.tagName !== 'INPUT') {
                const chk = item.querySelector('input[type="checkbox"]');
                if (chk) chk.checked = !chk.checked;
              }
              this.updateGroupPickerCount();
            });
            listEl.appendChild(item);
          });
        }

        if (titleInput) {
          titleInput.value = initialTitle;
          setTimeout(() => {
            titleInput.focus();
            titleInput.select();
          }, 50);
        }

        this.updateGroupPickerCount();
        overlay.classList.add('open');

        // キーバインド（Enterで作成/更新、Escapeでキャンセル）
        if (this._pickerKeyHandler) {
          window.removeEventListener('keydown', this._pickerKeyHandler);
        }
        const onPickerKey = (e) => {
          if (e.key === 'Enter') {
            e.preventDefault();
            this.submitGroupPicker();
          } else if (e.key === 'Escape') {
            e.preventDefault();
            this.closeGroupPicker();
          }
        };
        this._pickerKeyHandler = onPickerKey;
        window.addEventListener('keydown', onPickerKey);
      },

      closeGroupPicker: function() {
        const overlay = document.getElementById('group-picker-overlay');
        if (overlay) overlay.classList.remove('open');
        if (this._pickerKeyHandler) {
          window.removeEventListener('keydown', this._pickerKeyHandler);
          this._pickerKeyHandler = null;
        }
        if (this.textareaEl) this.textareaEl.focus();
      },

      toggleSelectAllGroupNodes: function(checked) {
        const checkboxes = document.querySelectorAll('#group-picker-node-list input[type="checkbox"]');
        checkboxes.forEach(chk => { chk.checked = checked; });
        this.updateGroupPickerCount();
      },

      updateGroupPickerCount: function() {
        const countEl = document.getElementById('group-picker-count');
        const checkboxes = document.querySelectorAll('#group-picker-node-list input[type="checkbox"]');
        let selectedCount = 0;
        checkboxes.forEach(chk => { if (chk.checked) selectedCount++; });
        if (countEl) countEl.textContent = `選択: ${selectedCount} / ${checkboxes.length} 件`;
      },

      submitGroupPicker: function() {
        const titleInput = document.getElementById('group-picker-title');
        const title = (titleInput && titleInput.value.trim()) || '新規グループ';
        const checkboxes = document.querySelectorAll('#group-picker-node-list input[type="checkbox"]');
        const selectedIds = [];
        checkboxes.forEach(chk => {
          if (chk.checked) selectedIds.push(chk.value);
        });

        const isEditing = !!(this.groupPickerContext && this.groupPickerContext.editingGroupId);

        if (isEditing) {
          const editingGroupId = this.groupPickerContext.editingGroupId;
          const lines = this.textareaEl.value.split('\n');
          let updated = false;

          for (let i = 0; i < lines.length; i++) {
            const line = lines[i].trim();
            const m = line.match(/^(?:group:\s*|group\s+)([a-zA-Z0-9_-]+)\s*(?:\[(.*)\])?$/);
            if (m && m[1] === editingGroupId) {
              let props = m[2] || '';
              // title 更新
              if (/title="[^"]*"/.test(props)) {
                props = props.replace(/title="[^"]*"/, `title="${title}"`);
              } else {
                props = props.trim() ? `title="${title}", ${props}` : `title="${title}"`;
              }
              // contains 更新
              if (/contains="[^"]*"/.test(props)) {
                if (selectedIds.length > 0) {
                  props = props.replace(/contains="[^"]*"/, `contains="${selectedIds.join(', ')}"`);
                } else {
                  props = props.replace(/,?\s*contains="[^"]*"/, '');
                }
              } else if (selectedIds.length > 0) {
                props = `${props}, contains="${selectedIds.join(', ')}"`;
              }
              // カンマ整形
              props = props.replace(/^,\s*|,\s*$/g, '').replace(/,\s*,/g, ',');
              lines[i] = `group: ${editingGroupId} [${props}]`;
              updated = true;
              break;
            }
          }

          if (!updated) {
            const containsProp = selectedIds.length > 0 ? `, contains="${selectedIds.join(', ')}"` : '';
            lines.push(`group: ${editingGroupId} [title="${title}"${containsProp}]`);
          }

          this.textareaEl.value = lines.join('\n');
          this.closeGroupPicker();
          this.updateLineNumbers();
          this.updateCursorPos();
          this.applyToCanvas();
          if (typeof Canvas !== 'undefined' && typeof Canvas.selectNode === 'function') {
            setTimeout(() => Canvas.selectNode(editingGroupId), 50);
          }
          this.setStatus('ready', `[グループ構成更新 🔲] #${editingGroupId} : ${title} (${selectedIds.length}ノード)`);
          return;
        }

        // --- 新規作成モード ---
        const idNum = this.autoCounter++;
        const containsProp = selectedIds.length > 0 ? `, contains="${selectedIds.join(', ')}"` : '';
        const dslLine = `group: g${idNum} [title="${title}"${containsProp}, color="#38bdf8"]`;

        if (this.groupPickerContext && this.groupPickerContext.lastLineStart !== undefined) {
          const { lastLineStart, lineBeforeSlash, selStart } = this.groupPickerContext;
          const val = this.textareaEl.value;
          const newText = val.substring(0, lastLineStart) + lineBeforeSlash + dslLine + val.substring(selStart);
          this.textareaEl.value = newText;
          const newCursor = lastLineStart + lineBeforeSlash.length + dslLine.length;
          this.textareaEl.selectionStart = this.textareaEl.selectionEnd = newCursor;
        } else {
          const currentVal = this.textareaEl.value;
          this.textareaEl.value = currentVal.trim() ? `${currentVal.trim()}\n${dslLine}` : dslLine;
        }

        this.closeGroupPicker();
        this.updateLineNumbers();
        this.updateCursorPos();
        this.applyToCanvas();
        if (typeof Canvas !== 'undefined' && typeof Canvas.selectNode === 'function') {
          setTimeout(() => Canvas.selectNode(`g${idNum}`), 50);
        }
        this.setStatus('ready', `[グループ作成 🔲] ${title} (${selectedIds.length}ノード包含)`);
      },

      // マイクロデバウンス同期（20ms）
      scheduleSync: function() {
        if (this.isApplyingFromCanvas) return;
        this.setStatus('syncing', '同期中...');
        clearTimeout(this.syncTimer);
        this.syncTimer = setTimeout(() => {
          this.applyToCanvas();
        }, 20);
      },

      // キャンバスへDSL適用（完全全画面再描画）
      applyToCanvas: function() {
        const dsl = this.textareaEl.value;
        const prevNodeId = window.selectedNodeId;
        const prevEdge = window.selectedEdge;
        try {
          if (typeof Canvas !== 'undefined' && Canvas.applyDSL) {
            // エディタからの全反映時は一旦クリアして完全同期
            Canvas.clear(true);
            Canvas.applyDSL(dsl);
            const st = (typeof Canvas.getFullState === 'function') ? Canvas.getFullState() : { objects: [], edges: [] };
            const nodeCount = st.objects ? st.objects.length : 0;
            const edgeCount = st.edges ? st.edges.length : 0;
            this.setStatus('ready', `同期完了 (${nodeCount}ノード, ${edgeCount}エッジ)`);

            // 選択状態の復元 (色変更後も頭上ツールバーを維持)
            if (prevNodeId && st.objects && st.objects.some(o => o.id === prevNodeId)) {
              if (typeof Canvas.selectNode === 'function') {
                Canvas.selectNode(prevNodeId, { openDetail: false });
              }
            } else if (prevEdge && st.edges) {
              const matchedIdx = st.edges.findIndex(e => e.u === prevEdge.u && e.v === prevEdge.v);
              if (matchedIdx !== -1 && typeof Canvas.selectEdge === 'function') {
                Canvas.selectEdge(matchedIdx);
              }
            }
          }
        } catch (err) {
          console.error('[EditorSyncError]', err);
          this.setStatus('error', '構文解析エラー');
        }
      },

      // キャンバス最新状態からDSLを逆同期
      syncFromCanvas: function() {
        this.isApplyingFromCanvas = true;
        try {
          if (typeof Canvas !== 'undefined' && Canvas.buildExportDsl) {
            const exportDsl = Canvas.buildExportDsl();
            if (exportDsl && exportDsl.trim()) {
              this.textareaEl.value = exportDsl;
              this.updateLineNumbers();
              this.updateCursorPos();
              this.setStatus('ready', 'キャンバス配置をDSLに反映しました');
            }
          }
        } finally {
          this.isApplyingFromCanvas = false;
        }
      },

      // ステータス表示更新
      setStatus: function(type, text) {
        if (!this.statusDotEl) return;
        this.statusDotEl.className = 'status-dot';
        if (type === 'syncing') this.statusDotEl.classList.add('syncing');
        else if (type === 'error') this.statusDotEl.classList.add('error');
        this.statusTextEl.textContent = text;
      },

      // デモDSL読込（独立edge形式）
      loadDemoDsl: function() {
        const demoDsl = `clear
card: origin [title="光の本質とは何か？", sub="キャプテンの問い", color="#c084fc", detail="# 20世紀最大の物理学の転換点\\n光が波なのか粒子なのかという問いは、物理学を大きく変革しました。"]
math: einstein [title="EINSTEIN (1905)", latex="E_{max} = h\\nu - W_0"]
text: insight [title="光量子仮説の本質", content="光の強度ではなく「振動数」が電子の脱出エネルギーを決める。"]
card: debroglie [title="物質波の提唱", sub="ド・ブロイ (1924)", color="#38bdf8"]
math: debroglie_eq [title="DE BROGLIE (1924)", latex="\\lambda = \\frac{h}{p}"]
table: tbl_duality [title="波動性と粒子性の対比", headers="対象, 波動性, 粒子性", rows="光|干渉・回折|光電効果 (E=hν); 電子|電子線回折|質量 m・電荷 e"]

edge: e1 [from="origin", to="einstein", label="定式化", color="#10b981", width=2.5]
edge: e2 [from="einstein", to="insight", label="物理的意味", color="#38bdf8", width=2]
edge: e3 [from="origin", to="debroglie", label="波粒子二重性", color="#0ea5e9", width=2.2]
edge: e4 [from="debroglie", to="debroglie_eq", label="波長と運動量", color="#06b6d4", width=1.8]
edge: e5 [from="origin", to="tbl_duality", label="対比", color="#a855f7", width=2.2]`;
        this.textareaEl.value = demoDsl;
        this.updateLineNumbers();
        this.updateCursorPos();
        this.applyToCanvas();
      },

      // DSLテキスト正規化（相乗りto/link/edge_*を独立edge:行に分離抽出）
      normalizeDslText: function(dslText) {
        const lines = dslText.split('\n');
        const nodeLines = [];
        const edgeLines = [];
        let edgeCount = 1;

        lines.forEach(line => {
          const trimmed = line.trim();
          if (!trimmed || trimmed.startsWith('#') || trimmed.toLowerCase() === 'clear' || trimmed.toLowerCase() === 'reset') {
            nodeLines.push(line);
            return;
          }

          // 矢印ショートハンド: A -> B [: ラベル]
          const arrowMatch = trimmed.match(/^([^\s\-]+)\s*->\s*([^\s:]+)(?:\s*:\s*(.*))?$/);
          if (arrowMatch) {
            const from = arrowMatch[1].trim();
            const to = arrowMatch[2].trim();
            const label = arrowMatch[3] ? arrowMatch[3].trim() : '';
            const eprops = [`from="${from}"`, `to="${to}"`];
            if (label) eprops.push(`label="${label}"`);
            edgeLines.push(`edge: e${edgeCount++} [${eprops.join(', ')}]`);
            return;
          }

          // 正規ノード/エッジ構文: type: id [props]
          const m = trimmed.match(/^([a-z]+):\s*([a-zA-Z0-9_-]+)\s*\[(.*)\]$/);
          if (!m) {
            nodeLines.push(line);
            return;
          }

          const type = m[1];
          const id = m[2];
          const rawProps = m[3];

          if (type === 'edge') {
            edgeLines.push(trimmed);
            return;
          }

          // ノード行: props をパースして相乗りエッジプロパティを分離
          const propMatches = Array.from(rawProps.matchAll(/([a-zA-Z0-9_-]+)=(?:"([^"]*)"|'([^']*)'|([^\s,\]]+))/g));
          const cleanProps = [];
          const edgeAttrs = {};

          for (const pm of propMatches) {
            const k = pm[1];
            const v = pm[2] !== undefined ? pm[2] : (pm[3] !== undefined ? pm[3] : pm[4]);
            if (k === 'to') {
              edgeAttrs.to = v;
            } else if (k === 'link' || k === 'edge') {
              edgeAttrs.label = v;
            } else if (k === 'edge_color' || k === 'edge_stroke') {
              edgeAttrs.color = v;
            } else if (k === 'edge_width') {
              edgeAttrs.width = v;
            } else if (k === 'edge_dash') {
              edgeAttrs.dash = v;
            } else if (k === 'edge_style') {
              if (v === 'dashed') edgeAttrs.dash = '5,4';
            } else if (k === 'edge_arrow') {
              edgeAttrs.arrow = v;
            } else {
              if (pm[2] !== undefined || pm[3] !== undefined) {
                cleanProps.push(`${k}="${String(v).replace(/"/g, '\\"')}"`);
              } else {
                cleanProps.push(`${k}=${v}`);
              }
            }
          }

          nodeLines.push(`${type}: ${id} [${cleanProps.join(', ')}]`);

          if (edgeAttrs.to) {
            const eprops = [`from="${edgeAttrs.to}"`, `to="${id}"`];
            if (edgeAttrs.label) eprops.push(`label="${edgeAttrs.label}"`);
            if (edgeAttrs.color) eprops.push(`color="${edgeAttrs.color}"`);
            if (edgeAttrs.width) eprops.push(`width=${edgeAttrs.width}`);
            if (edgeAttrs.dash) eprops.push(`dash="${edgeAttrs.dash}"`);
            if (edgeAttrs.arrow === 'false' || edgeAttrs.arrow === false) eprops.push('arrow=false');
            edgeLines.push(`edge: e${edgeCount++} [${eprops.join(', ')}]`);
          }
        });

        // 結合（ノード群とエッジ群の間に空行を配置）
        const result = [];
        result.push(...nodeLines);
        if (edgeLines.length > 0) {
          result.push('');
          result.push(...edgeLines);
        }
        return result.join('\n');
      },

      // 正規化実行
      normalizeDsl: function() {
        const currentText = this.textareaEl.value;
        if (!currentText.trim()) return;
        const normalized = this.normalizeDslText(currentText);
        if (normalized !== currentText) {
          this.textareaEl.value = normalized;
          this.updateLineNumbers();
          this.updateCursorPos();
          this.applyToCanvas();
          this.setStatus('ready', 'DSLを独立edge形式に正規化しました ✨');
        } else {
          this.setStatus('ready', 'DSLは既に正規化されています');
        }
      },

      // 初期コンテンツロード
      loadInitialContent: function() {
        const st = (typeof Canvas !== 'undefined' && typeof Canvas.getFullState === 'function') ? Canvas.getFullState() : null;
        if (st && st.objects && st.objects.length > 0) {
          this.syncFromCanvas();
        } else {
          this.loadDemoDsl();
        }
      }
    };
    window.EditorApp = EditorApp;
    
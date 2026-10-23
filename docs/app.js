'use strict';

(() => {
  const $ = (selector, context = document) => context.querySelector(selector);
  const $$ = (selector, context = document) => [...context.querySelectorAll(selector)];
  const platformNames = { independent_web: '独立网站', reddit: 'Reddit', mercury_official: 'Mercury 官方', v2ex: 'V2EX', linkedin: 'LinkedIn', hacker_news: 'Hacker News', medium: 'Medium', youtube: 'YouTube', bilibili: '哔哩哔哩', github: 'GitHub', linuxdo: 'Linux DO', x: 'X' };
  const statusNames = { verified: '正文已核验', metadata_verified: '仅元数据', blocked: '访问受限', excluded: '已排除' };
  const gradeNames = { strong: '强证据', medium: '中等证据', weak: '弱证据' };
  const viewDescriptions = { research: '本次研究的样本范围、证据等级与主要限制。', conclusions: '大陆居民企业户资格、个人户门槛、材料与拒绝风险。', 'full-process': '公司类型、注册州、EIN、银行申请与后续维护。', checklist: '面向大陆居民、无 SSN / ITIN 的 Wyoming 单成员 LLC 路线。' };
  const state = { catalogue: [], filtered: [], limit: 30, summary: null, budget: null, route: 'self', contentIndex: [], contentCache: new Map(), view: 'research', readRequest: 0 };
  const taskKey = 'mercury-field-guide:tasks:v1';
  const budgetKey = 'mercury-field-guide:budget:v1';
  const extraFields = [ ['P', '结账、支付及处理附加费'], ['F', '传真、回传或邮寄'], ['A', '合格地址与邮件服务'], ['D', '网站、域名、邮箱与电话'], ['B', '记账、额外税表与专业服务'], ['T', '实际美国及中国适用税款'], ['U', '交易、非基础银行与运营费用'], ['V', '注销或特殊处理费用'] ];
  const taskDefinitions = [
    ['business', '明确真实业务与美国业务联系', '写清产品、客户、收费和实际关系或具体计划。'],
    ['name', '查询 Wyoming 公司名称', '核对可用名称，并准备备选名称及 LLC 后缀。'],
    ['agent', '核对注册代理与续费', '确认首年、次年价格、服务范围及地址用途。'],
    ['address', '区分四种地址', '确认法定、经营、股东居住与收件地址各自要求。'],
    ['formation', '提交公司成立申请', '自行提交或委托代办，避免重复注册。'],
    ['documents', '保存成立及内部文件', '核对成立文件，保存 Operating Agreement 与股权记录。'],
    ['ss4', '按真实情况填写 SS-4', '核对负责人、经营地、税务分类与回函安排。'],
    ['ein', '取得并保存 EIN 证明', '保留 IRS 正式证明；不要重复申请同一主体 EIN。'],
    ['bank-materials', '整理 Mercury 申请材料', '护照、公司与 EIN 文件、地址证明、业务及资金说明。'],
    ['apply', '通过官方入口申请并补件', '查看 In Review 状态、邮箱及垃圾邮件。'],
    ['filing', '安排联邦申报与州年报', '确认 5472＋pro forma 1120 等适用义务与服务范围。'],
    ['calendar', '建立续费与维护日历', '记录年报、注册代理、税务和实际业务凭证。']
  ];
  const defaultTemplate = `[FULL LEGAL COMPANY NAME INCLUDING LLC] is a Wyoming single-member company wholly owned and managed by [FULL LEGAL NAME], who resides in China.

We provide [SPECIFIC PRODUCT OR SERVICE] to [CUSTOMER TYPE] in [ACTUAL OR TARGET MARKETS]. We charge [PRICING MODEL]. Our principal place of business is [CITY, PROVINCE, CHINA], where [ACTUAL WORK PERFORMED].

Our U.S. business connection is [EXISTING U.S. CUSTOMER/PARTNER/SUPPLIER RELATIONSHIP OR A CONCRETE U.S. LAUNCH PLAN]. Our current stage is [PRE-REVENUE / OPERATING]. Available supporting information includes [REAL WEBSITE, PRODUCT DEMO, CONTRACT, ORDER OR OTHER RELEVANT EVIDENCE].

Initial funding will come from [ACTUAL DOCUMENTED SOURCE]. Ongoing receipts are expected from [CUSTOMER PAYMENTS / OTHER ACTUAL BUSINESS SOURCE] through [ACTUAL PAYMENT CHANNELS].

We expect approximately USD [AMOUNT] in monthly incoming payments, [NUMBER] incoming transactions per month, and payments involving [COUNTRIES]. These are [FORECASTS / ESTIMATES BASED ON EXISTING OPERATIONS].

We intend to use Mercury to [ACTUAL BUSINESS PURPOSES], including paying [REAL BUSINESS EXPENSE CATEGORIES].`;
  const officialSources = [
    ['WYOMING', '公司名称查询', '核对名称与现有主体记录', 'https://wyobiz.wyo.gov/Business/FilingSearch.aspx'],
    ['WYOMING', '公司注册入口', '州官方注册流程与政府费用', 'https://wyobiz.wyo.gov/Business/RegistrationInstr.aspx'],
    ['WYOMING', '年报与 License Tax', '确认年度截止日期及最低费用', 'https://wyobiz.wyo.gov/Business/AnnualReport.aspx'],
    ['IRS', 'SS-4 正式表格', '直接下载 IRS 发布的 PDF', 'https://www.irs.gov/pub/irs-pdf/fss4.pdf'],
    ['IRS', 'SS-4 填写说明', '按真实经营与税务情况逐行核对', 'https://www.irs.gov/instructions/iss4'],
    ['IRS', 'EIN 申请与处理进度', 'EIN 官方申请免费', 'https://www.irs.gov/help/processing-status-for-tax-forms'],
    ['MERCURY', '企业账户入口', '查看申请资格及基础费用', 'https://mercury.com/business-banking'],
    ['MERCURY', '公司地址要求', '区分法定地址与实际经营地址', 'https://support.mercury.com/hc/en-us/articles/28769699533588-Company-address-requirements'],
    ['IRS', 'Form 5472 规则', '检查关联交易与申报义务', 'https://www.irs.gov/instructions/i5472']
  ];

  function element(tag, className, value) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (value !== undefined) node.textContent = String(value);
    return node;
  }

  function asText(value) {
    if (value == null) return '';
    return Array.isArray(value) ? value.map(asText).join(' · ') : typeof value === 'object' ? '' : String(value);
  }

  function safeURL(value) {
    if (typeof value !== 'string' || value.length > 5000) return null;
    try {
      const url = new URL(value);
      return /^https?:$/.test(url.protocol) && !url.username && !url.password ? url.href : null;
    } catch { return null; }
  }

  function externalLink(label, url, className) {
    const safe = safeURL(url);
    const link = element(safe ? 'a' : 'span', className, label);
    if (safe) { link.href = safe; link.target = '_blank'; link.rel = 'noopener noreferrer'; }
    return link;
  }

  async function fetchFile(path, type = 'json') {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 15000);
    try {
      const response = await fetch(path, { signal: controller.signal, credentials: 'same-origin' });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return type === 'json' ? await response.json() : await response.text();
    } finally { clearTimeout(timeout); }
  }

  function readLocal(key, fallback) {
    try { return JSON.parse(localStorage.getItem(key)) || fallback; } catch { return fallback; }
  }

  function saveLocal(key, value) {
    try { localStorage.setItem(key, JSON.stringify(value)); } catch { /* Storage may be unavailable in private mode. */ }
  }

  function showError(container, message, retry) {
    const box = element('div', 'error-state', message);
    if (retry) {
      const button = element('button', '', '重试载入');
      button.type = 'button';
      button.addEventListener('click', retry);
      box.append(button);
    }
    container.replaceChildren(box);
  }

  function validDate(value) { return typeof value === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(value); }

  async function loadSummary() {
    try {
      const data = await fetchFile('data/summary.json');
      state.summary = data;
      if (Number.isFinite(Number(data.total_candidates))) $('#stat-candidates').textContent = String(data.total_candidates);
      const verified = data.by_curator_status?.verified ?? data.accepted_body_count;
      if (Number.isFinite(Number(verified))) $('#stat-verified').textContent = String(verified);
      if (Number.isFinite(Number(data.distinct_source_domains))) $('#stat-domains').textContent = String(data.distinct_source_domains);
      if (validDate(data.as_of)) $$('.as-of').forEach(node => { node.textContent = data.as_of; });
    } catch { /* The published snapshot counters remain visible if metadata cannot load. */ }
  }

  async function loadPublications() {
    try {
      const data = await fetchFile('data/publication.json');
      const root = $('#publication-links');
      for (const [label, values] of [ ['GitHub ↗', [data.github_url, data.github, data.repository_url]], ['飞书文档 ↗', [data.feishu_url, data.feishu, data.feishu_document_url]] ]) {
        const url = values.find(value => safeURL(value));
        if (url) root.append(externalLink(label, url));
      }
    } catch { /* Publication links are optional during deployment. */ }
  }

  function sanitizeFragment(html) {
    const parsed = new DOMParser().parseFromString(html, 'text/html');
    $$('script, iframe, object, embed, form, style, link, meta, base, svg, math', parsed).forEach(node => node.remove());
    $$('*', parsed.body).forEach(node => {
      [...node.attributes].forEach(attribute => {
        if (/^on/i.test(attribute.name) || ['srcdoc', 'style', 'formaction'].includes(attribute.name.toLowerCase())) node.removeAttribute(attribute.name);
      });
      if (node.tagName === 'A') {
        const href = node.getAttribute('href') || '';
        if (/^#(?:read-)?[a-zA-Z0-9_-]+$/.test(href)) {
          node.removeAttribute('target');
        } else {
          const safe = safeURL(href);
          if (safe) { node.href = safe; node.target = '_blank'; node.rel = 'noopener noreferrer'; }
          else node.removeAttribute('href');
        }
      }
      if (node.hasAttribute('src')) node.removeAttribute('src');
      if (node.hasAttribute('srcset')) node.removeAttribute('srcset');
    });
    return document.importNode(parsed.body, true);
  }

  function contentPath(item, id) {
    const value = item?.html || `content/${id}.html`;
    return typeof value === 'string' && /^(?:\.\/)?content\/[a-zA-Z0-9_\-]+\.html$/.test(value) ? value : null;
  }

  async function selectView(view, updateHash = false) {
    if (!Object.hasOwn(viewDescriptions, view)) view = 'research';
    state.view = view;
    const request = ++state.readRequest;
    const panel = $('#reader-panel');
    $$('.reader-tabs button').forEach(button => {
      const selected = button.dataset.view === view;
      button.setAttribute('aria-selected', String(selected));
      button.tabIndex = selected ? 0 : -1;
    });
    panel.setAttribute('aria-labelledby', `tab-${view}`);
    const item = state.contentIndex.find(entry => entry.id === view);
    $('#reader-description').textContent = asText(item?.description) || viewDescriptions[view];
    panel.setAttribute('aria-busy', 'true');
    panel.replaceChildren(element('p', 'loading', '正在载入正文…'));
    if (updateHash) history.replaceState(null, '', `#read-${view}`);
    try {
      const path = contentPath(item, view);
      if (!path) throw new Error('Invalid content path');
      let html = state.contentCache.get(path);
      if (html === undefined) { html = await fetchFile(path, 'text'); state.contentCache.set(path, html); }
      if (request !== state.readRequest) return;
      const body = sanitizeFragment(html);
      panel.replaceChildren(...body.childNodes);
    } catch {
      if (request !== state.readRequest) return;
      showError(panel, '这一篇正文暂时未能载入。请重试，或通过页首 GitHub 仓库查看完整文档。', () => selectView(view));
    } finally { if (request === state.readRequest) panel.setAttribute('aria-busy', 'false'); }
  }

  async function loadReading() {
    try {
      const index = await fetchFile('content/index.json');
      state.contentIndex = Array.isArray(index) ? index : Array.isArray(index.documents) ? index.documents : [];
    } catch { /* Standard id-based content paths are still attempted. */ }
    const fromHash = location.hash.match(/^#read-([a-z-]+)$/)?.[1];
    await selectView(fromHash || state.view);
    if (fromHash) $('#reading').scrollIntoView();
  }

  function buildSourceRow(record, index) {
    const row = element('article', 'source-row');
    row.append(element('div', 'source-number', String(index + 1).padStart(3, '0')));
    const main = element('div', 'source-main');
    const heading = element('h3', 'source-title');
    heading.append(externalLink(asText(record.title) || '未提供标题', record.canonical_url || record.url));
    main.append(heading);
    const meta = element('div', 'source-meta');
    const platform = platformNames[record.platform] || asText(record.platform) || '未知平台';
    const metaValues = [platform, asText(record.author) || '作者未知', validDate(record.published_at) ? record.published_at : '发布日期未知', asText(record.domain)];
    metaValues.filter(Boolean).forEach(value => meta.append(element('span', '', value)));
    if (record.commercial === true || record.commercial === 'true') meta.append(element('span', 'commercial', '含商业 / 推广因素'));
    main.append(meta);
    main.append(element('p', 'source-claim', asText(record.curator_claim) || asText(record.findings) || '该项未形成可引用的正文结论。'));
    const limitation = asText(record.review_limitations) || asText(record.limitations) || asText(record.curator_note);
    if (limitation) {
      const details = element('details', 'source-details');
      details.append(element('summary', '', '证据边界与限制'), element('p', '', limitation));
      main.append(details);
    }
    row.append(main);
    const tags = element('div', 'source-tags');
    tags.append(element('span', `badge ${Object.hasOwn(statusNames, record.curator_status) ? record.curator_status : ''} ${record.evidence_grade === 'weak' ? 'weak' : ''}`, statusNames[record.curator_status] || '未分类'));
    if (gradeNames[record.evidence_grade]) tags.append(element('span', 'grade-label', gradeNames[record.evidence_grade]));
    row.append(tags);
    return row;
  }

  function filterCatalogue(reset = true) {
    if (reset) state.limit = 30;
    const query = $('#search-input').value.trim().toLocaleLowerCase();
    const platform = $('#platform-filter').value;
    const evidence = $('#evidence-filter').value;
    const date = $('#date-filter').value;
    state.filtered = state.catalogue.filter(record => {
      if (platform !== 'all' && record.platform !== platform) return false;
      if (evidence === 'decision' && !(record.curator_status === 'verified' && ['strong', 'medium'].includes(record.evidence_grade))) return false;
      if (!['all', 'decision'].includes(evidence) && record.curator_status !== evidence) return false;
      if (date === 'known' && !validDate(record.published_at)) return false;
      if (date === 'unknown' && validDate(record.published_at)) return false;
      if (query && ![record.title, record.author, record.curator_claim, record.findings, record.domain, record.review_limitations].map(asText).join(' ').toLocaleLowerCase().includes(query)) return false;
      return true;
    });
    renderCatalogue();
  }

  function renderCatalogue() {
    const list = $('#source-list');
    const fragment = document.createDocumentFragment();
    state.filtered.slice(0, state.limit).forEach((record, index) => fragment.append(buildSourceRow(record, index)));
    if (!state.filtered.length) fragment.append(element('p', 'empty-state', '没有匹配的记录。试试缩短关键词，或清除筛选条件。'));
    list.replaceChildren(fragment);
    const showing = Math.min(state.limit, state.filtered.length);
    $('#result-count').textContent = `${state.filtered.length} 条匹配 / 共 ${state.catalogue.length} 条 · 已显示 ${showing} 条`;
    const more = $('#load-more');
    more.hidden = showing >= state.filtered.length;
    more.textContent = `继续显示 ${Math.min(30, state.filtered.length - showing)} 条 ↓`;
  }

  async function loadCatalogue() {
    try {
      const data = await fetchFile('data/catalogue.json');
      state.catalogue = Array.isArray(data) ? data.filter(item => item && typeof item === 'object') : [];
      if (!Array.isArray(data)) throw new Error('Invalid catalogue');
      const counts = new Map();
      state.catalogue.forEach(record => {
        const platform = asText(record.platform);
        if (platform) counts.set(platform, (counts.get(platform) || 0) + 1);
      });
      const select = $('#platform-filter');
      select.replaceChildren(element('option', '', '全部平台'));
      select.firstChild.value = 'all';
      [...counts].sort((a, b) => b[1] - a[1]).forEach(([platform, count]) => {
        const option = element('option', '', `${platformNames[platform] || platform} (${count})`);
        option.value = platform;
        select.append(option);
      });
      filterCatalogue();
    } catch {
      $('#result-count').textContent = '来源目录暂时不可用';
      showError($('#source-list'), '目录文件未能载入。正文与预算仍可独立阅读。', loadCatalogue);
    }
  }

  const currency = value => new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(value);
  const validAmount = value => Number.isFinite(Number(value)) && Number(value) >= 0;
  const budgetLineLabels = { state_formation: '州成立费', formation_service: '注册代办', registered_agent: '注册代理', ein_government: 'EIN 官费', ein_service: 'EIN 代办', annual_report_online: '州年报（含在线支付费）', tax_filing_service_sample: '联邦税表服务样例', mercury_base_required_fees: 'Mercury 必需基础费用', boi_government_filing: 'BOI 官费（当前豁免）' };

  function renderBudget() {
    if (!state.budget) return;
    const first = state.route === 'assisted' ? state.budget.first_period_assisted_ein : state.budget.first_period_self_ein;
    const second = state.budget.second_period;
    if (!first || !second || !validAmount(first.subtotal) || !validAmount(second.subtotal)) return;
    const rows = document.createDocumentFragment();
    Object.entries(budgetLineLabels).forEach(([key, label]) => {
      if (!validAmount(first[key]) || !validAmount(second[key])) return;
      const row = element('tr');
      row.append(element('th', '', label), element('td', '', currency(Number(first[key]))), element('td', '', currency(Number(second[key]))));
      row.firstChild.scope = 'row';
      rows.append(row);
    });
    $('#budget-lines').replaceChildren(rows);
    const base = Number(first.subtotal) + Number(second.subtotal);
    $('#base-first').textContent = currency(Number(first.subtotal));
    $('#base-second').textContent = currency(Number(second.subtotal));
    $('#two-year-base').textContent = currency(base);
    let extra = 0;
    let filled = 0;
    const values = {};
    $$('#extra-costs input').forEach(input => {
      if (input.value.trim() !== '' && validAmount(input.value)) { extra += Number(input.value); filled += 1; values[input.dataset.code] = input.value; }
      else values[input.dataset.code] = '';
    });
    $('#estimated-total').textContent = currency(base + extra);
    $('#budget-completeness').textContent = filled === extraFields.length ? '已加入全部填写项目；仍须核对适用税款与服务范围。' : `额外费用 ${filled} / ${extraFields.length} 项已填写；${extraFields.length - filled} 项未知，此数不是完整总成本。`;
    saveLocal(budgetKey, { route: state.route, extras: values });
  }

  function initExtras() {
    const stored = readLocal(budgetKey, {});
    if (['self', 'assisted'].includes(stored.route)) {
      state.route = stored.route;
      $(`input[name="ein-route"][value="${stored.route}"]`).checked = true;
    }
    const fragment = document.createDocumentFragment();
    extraFields.forEach(([code, label]) => {
      const wrapper = element('label');
      const caption = element('span');
      caption.append(element('b', '', code), document.createTextNode(label));
      const input = element('input');
      input.type = 'number'; input.min = '0'; input.step = '0.01'; input.placeholder = '待估算'; input.inputMode = 'decimal'; input.dataset.code = code;
      input.setAttribute('aria-label', `${label}，两年合计美元`);
      const previous = stored.extras?.[code];
      if (previous !== '' && previous !== undefined && validAmount(previous)) input.value = previous;
      input.addEventListener('input', () => {
        if (input.value !== '' && (!validAmount(input.value) || Number(input.value) < 0)) input.value = '';
        renderBudget();
      });
      wrapper.append(caption, input); fragment.append(wrapper);
    });
    $('#extra-costs').replaceChildren(fragment);
    $$('input[name="ein-route"]').forEach(input => input.addEventListener('change', () => { state.route = input.value; renderBudget(); }));
  }

  async function loadBudget() {
    try {
      const data = await fetchFile('data/budget.json');
      if (!data.first_period_self_ein || !data.second_period) throw new Error('Invalid budget');
      state.budget = data;
      renderBudget();
      const note = $('#budget-source-note');
      note.append(document.createTextNode('预算报价来源：'));
      const labels = { wyoming_formation: '州注册', wyoming_annual: '州年报', provider_formation: '成立服务样例', provider_ein: 'EIN 服务样例', tax_scope: '税表服务范围', bank_pricing: 'Mercury 费用', boi: 'BOI 规则' };
      Object.entries(data.sources || {}).forEach(([key, url]) => { if (safeURL(url)) note.append(externalLink(labels[key] || key, url)); });
    } catch {
      const row = element('tr');
      const cell = element('td'); cell.colSpan = 3;
      showError(cell, '预算明细暂时无法载入。上方数字为本次发布的基础快照；费用计算暂不可用。', loadBudget);
      row.append(cell); $('#budget-lines').replaceChildren(row);
      $('#budget-completeness').textContent = '计算器尚未就绪；请稍后重试明细。';
    }
  }

  function initChecklist() {
    const saved = readLocal(taskKey, []);
    const done = new Set(Array.isArray(saved) ? saved.filter(value => taskDefinitions.some(([id]) => id === value)) : []);
    const root = $('#task-list');
    function update() {
      $('#checklist-progress').textContent = `${done.size} / ${taskDefinitions.length}`;
      $('#progress-fill').style.width = `${done.size / taskDefinitions.length * 100}%`;
      saveLocal(taskKey, [...done]);
    }
    taskDefinitions.forEach(([id, title, description]) => {
      const label = element('label', 'task');
      const checkbox = element('input'); checkbox.type = 'checkbox'; checkbox.value = id; checkbox.checked = done.has(id);
      label.classList.toggle('done', checkbox.checked);
      const text = element('span'); text.append(element('span', 'task-title', title), element('span', 'task-description', description));
      label.append(checkbox, text); root.append(label);
      checkbox.addEventListener('change', () => { if (checkbox.checked) done.add(id); else done.delete(id); label.classList.toggle('done', checkbox.checked); update(); });
    });
    $('#reset-checklist').addEventListener('click', () => { done.clear(); $$('.task input').forEach(input => { input.checked = false; input.closest('.task').classList.remove('done'); }); update(); });
    update();
  }

  async function loadTemplate() {
    const target = $('#business-template');
    target.textContent = defaultTemplate;
    try {
      const value = await fetchFile('content/business-template.txt', 'text');
      if (value.trim()) {
        const start = value.indexOf('[FULL LEGAL COMPANY NAME');
        target.textContent = start >= 0 ? value.slice(start).trim() : value.trim();
      }
    } catch { /* Embedded published template remains usable. */ }
  }

  async function copyTemplate() {
    const text = $('#business-template').textContent;
    const status = $('#copy-status');
    try {
      if (!navigator.clipboard?.writeText) throw new Error('Clipboard unavailable');
      await navigator.clipboard.writeText(text);
      status.textContent = '已复制。提交前替换全部占位符，并删除不适用内容。';
    } catch {
      const selection = window.getSelection();
      const range = document.createRange(); range.selectNodeContents($('#business-template')); selection.removeAllRanges(); selection.addRange(range);
      status.textContent = '浏览器未允许自动复制，已选中模板；请使用系统复制快捷键。';
      $('#business-template').focus();
    }
  }

  function initSources() {
    const fragment = document.createDocumentFragment();
    officialSources.forEach(([group, title, description, url]) => {
      const link = externalLink('', url, 'official-card');
      link.append(element('span', '', group), element('i', '', '↗'), element('strong', '', title), element('small', '', description));
      fragment.append(link);
    });
    $('#official-links').append(fragment);
  }

  function routeHash() {
    const match = location.hash.match(/^#read-([a-z-]+)$/);
    if (match && Object.hasOwn(viewDescriptions, match[1])) { selectView(match[1]); $('#reading').scrollIntoView(); }
  }

  function initNavigation() {
    $$('.reader-tabs button').forEach((button, index, buttons) => {
      button.addEventListener('click', () => selectView(button.dataset.view, true));
      button.addEventListener('keydown', event => {
        let next;
        if (event.key === 'ArrowRight') next = (index + 1) % buttons.length;
        if (event.key === 'ArrowLeft') next = (index + buttons.length - 1) % buttons.length;
        if (event.key === 'Home') next = 0;
        if (event.key === 'End') next = buttons.length - 1;
        if (next !== undefined) { event.preventDefault(); buttons[next].focus(); selectView(buttons[next].dataset.view, true); }
      });
    });
    document.addEventListener('click', event => {
      const link = event.target.closest('a');
      if (!link) return;
      const view = link.dataset.readView;
      const hashView = link.getAttribute('href')?.match(/^#read-([a-z-]+)$/)?.[1];
      if (view || hashView) {
        event.preventDefault(); selectView(view || hashView, true); $('#reading').scrollIntoView();
      }
    });
    window.addEventListener('hashchange', routeHash);
    if ('IntersectionObserver' in window) {
      const observer = new IntersectionObserver(entries => {
        const entry = entries.filter(item => item.isIntersecting).sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top)[0];
        if (entry) $$('.chapter-nav a').forEach(link => link.classList.toggle('active', link.getAttribute('href') === `#${entry.target.id}`));
      }, { rootMargin: '-10% 0px -65% 0px', threshold: 0 });
      $$('.observed-section').forEach(section => observer.observe(section));
    }
  }

  $('#filter-form').addEventListener('submit', event => event.preventDefault());
  $('#filter-form').addEventListener('reset', () => { requestAnimationFrame(() => filterCatalogue()); });
  $('#search-input').addEventListener('input', () => filterCatalogue());
  ['platform-filter', 'evidence-filter', 'date-filter'].forEach(id => $(`#${id}`).addEventListener('change', () => filterCatalogue()));
  $('#load-more').addEventListener('click', () => { state.limit += 30; renderCatalogue(); });
  $('#print-button').addEventListener('click', () => window.print());
  $('#copy-template').addEventListener('click', copyTemplate);
  initExtras(); initChecklist(); initSources(); initNavigation();
  Promise.allSettled([loadSummary(), loadPublications(), loadReading(), loadCatalogue(), loadBudget(), loadTemplate()]);
})();

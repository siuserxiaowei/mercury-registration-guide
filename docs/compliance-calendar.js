(() => {
  'use strict';

  const annualURL = 'https://wyobiz.wyo.gov/Business/AnnualReport.aspx';
  const taxURL = 'https://www.irs.gov/instructions/i5472';
  const day = 86_400_000;
  const utc = (y, m, d) => new Date(Date.UTC(y, m, d));
  const iso = date => date.toISOString().slice(0, 10);
  const moveDays = (date, days) => new Date(+date + days * day);
  const isWeekend = date => [0, 6].includes(date.getUTCDay());
  const clampedDate = (year, month, date) => utc(year, month, Math.min(date, utc(year, month + 1, 0).getUTCDate()));

  function parseDate(value) {
    if (typeof value !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(value) || value < '1900-01-01') return null;
    const [year, month, date] = value.split('-').map(Number);
    const result = utc(year, month - 1, date);
    return iso(result) === value ? result : null;
  }

  function wyomingToday(now = new Date()) {
    const formatter = new Intl.DateTimeFormat('en-US', { timeZone: 'America/Denver', year: 'numeric', month: '2-digit', day: '2-digit' });
    const parts = Object.fromEntries(formatter.formatToParts(now).map(part => [part.type, part.value]));
    return `${parts.year}-${parts.month}-${parts.day}`;
  }

  function federalDueDate(year) {
    const emancipation = utc(year, 3, 16);
    const observed = moveDays(emancipation, emancipation.getUTCDay() === 6 ? -1 : emancipation.getUTCDay() === 0 ? 1 : 0);
    let due = utc(year, 3, 15);
    while (isWeekend(due) || +due === +observed) due = moveDays(due, 1);
    return due;
  }

  function plan({ formation, taxStatus = 'review', agentRenewal = '', today = wyomingToday() }) {
    const formed = parseDate(formation);
    const start = parseDate(today);
    const renewal = parseDate(agentRenewal);
    if (!formed || !start || formed > start || start.getUTCFullYear() > 9997) throw new RangeError('请填写有效的 LLC 成立日期（不能晚于今天）。');
    if (agentRenewal && (!renewal || renewal < start)) throw new RangeError('代理下次续费日期不能早于今天。已过账单请直接向代理核对。');
    if (!['review', 'due', 'none'].includes(taxStatus)) throw new RangeError('请选择 Form 5472 状态。');

    const end = clampedDate(start.getUTCFullYear() + 2, start.getUTCMonth(), start.getUTCDate());
    const events = [];
    const add = (id, date, title, description) => {
      if (date >= start && date < end) events.push({ id, date: iso(date), title, description });
    };
    const firstYear = formed.getUTCFullYear();
    // One extra candidate year covers 30-day checks for early January anniversaries.
    for (let year = Math.max(firstYear + 1, start.getUTCFullYear()); year <= end.getUTCFullYear() + 1; year++) {
      add(`wy-annual-${year}`, utc(year, formed.getUTCMonth(), 1), '怀俄明州年报截止', `成立次年起，于成立周年月的 1 日到期。请核对州登记档案并提前提交。\n${annualURL}`);

      if (!renewal) {
        const anniversary = clampedDate(year, formed.getUTCMonth(), formed.getUTCDate());
        const check = moveDays(anniversary, -30);
        if (anniversary >= start) add(`agent-check-${year}`, check < start ? start : check, '核对注册代理续费（估算）', '按成立周年前约 30 天安排核对。实际续费日以代理合同或账单为准。');
      }

      const due = federalDueDate(year);
      if (taxStatus === 'due') {
        add(`irs-5472-${year - 1}`, due, `Form 5472 常规截止（${year - 1} 税年）`, `如该税年有应报告交易，将 Form 5472 附于形式 Form 1120。此日期按自然年计算，未应用延期或个别 IRS 救济。\n${taxURL}`);
      } else if (taxStatus === 'review' && due >= start) {
        const check = moveDays(due, -30);
        add(`irs-review-${year - 1}`, check < start ? start : check, `核对是否需报 Form 5472（${year - 1} 税年）`, `这是一条核对提醒。若适用，常规截止日为 ${iso(due)}。成立相关款项、股东出资、代垫、分配等也应核对。\n${taxURL}`);
      }
    }

    if (renewal) add('agent-renewal', renewal, '注册代理续费（账单日期）', '这是你填写的下一次续费日期。后续续费请按新账单更新。');
    events.sort((a, b) => a.date.localeCompare(b.date) || a.id.localeCompare(b.id));
    return { events, start: today, end: iso(moveDays(end, -1)), renewalBeyondRange: Boolean(renewal && renewal >= end) };
  }

  function init() {
    const container = document.getElementById('compliance-calendar');
    if (!container || !globalThis.MercuryCalendarICS) return;
    const form = container.querySelector('.calendar-form');
    const formation = container.querySelector('#calendar-formation');
    const tax = container.querySelector('#calendar-tax');
    const agent = container.querySelector('#calendar-agent');
    const status = container.querySelector('.calendar-status');
    const output = container.querySelector('.calendar-output');
    const list = container.querySelector('.calendar-events');
    const download = container.querySelector('.calendar-download');
    let events = [];

    function updateLimits() {
      const today = wyomingToday();
      formation.max = today;
      agent.min = today;
      return today;
    }

    function renderEvent(event) {
      const row = document.createElement('li');
      row.className = 'calendar-event';
      const time = document.createElement('time');
      time.dateTime = event.date;
      time.textContent = event.date;
      const body = document.createElement('div');
      const title = document.createElement('strong');
      title.textContent = event.title;
      const description = document.createElement('p');
      description.textContent = event.description.split('\n')[0];
      body.append(title, description);
      row.append(time, body);
      return row;
    }

    form.addEventListener('submit', event => {
      event.preventDefault();
      try {
        const result = plan({ formation: formation.value, taxStatus: tax.value, agentRenewal: agent.value, today: updateLimits() });
        events = result.events;
        list.replaceChildren(...events.map(renderEvent));
        output.hidden = !events.length;
        status.textContent = `${result.start} 至 ${result.end}：${events.length} 项。${result.renewalBeyondRange ? '所填的代理续费日期超出范围，未加入日历。' : ''}`;
      } catch (error) {
        events = [];
        output.hidden = true;
        status.textContent = error.message;
      }
    });
    form.addEventListener('input', () => {
      if (events.length) status.textContent = '选项已修改，请重新生成日历。';
      events = [];
      output.hidden = true;
    });
    download.addEventListener('click', () => {
      if (!events.length) return;
      const file = new Blob([globalThis.MercuryCalendarICS.serialize(events)], { type: 'text/calendar;charset=utf-8' });
      const url = URL.createObjectURL(file);
      const link = document.createElement('a');
      link.href = url;
      link.download = 'wyoming-llc-compliance.ics';
      document.body.append(link);
      link.click();
      link.remove();
      setTimeout(() => URL.revokeObjectURL(url), 30_000);
    });
    updateLimits();
    form.hidden = false;
  }

  if (typeof module === 'object' && module.exports) module.exports = { plan, federalDueDate, wyomingToday };
  if (typeof document !== 'undefined') init();
})();

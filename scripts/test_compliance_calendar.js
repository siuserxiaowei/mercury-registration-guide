const assert = require('node:assert/strict');
const { test } = require('node:test');
const { plan, federalDueDate, wyomingToday } = require('../dist/compliance-calendar.js');
const { serialize } = require('../dist/calendar-ics.js');

test('state report starts the next year and keeps the official Sunday date', () => {
  // Wyoming Secretary of State's "What's Next?" example.
  const { events } = plan({ formation: '2025-02-16', today: '2025-02-16', taxStatus: 'none' });
  assert.deepEqual(events.filter(e => e.id.startsWith('wy-')).map(e => e.date), ['2026-02-01', '2027-02-01']);
  assert.ok(!events.some(e => e.id.startsWith('irs-')));
});

test('federal dates account for weekends and observed DC Emancipation Day', () => {
  assert.deepEqual([2022, 2026, 2027, 2028, 2029].map(y => federalDueDate(y).toISOString().slice(0, 10)),
    ['2022-04-18', '2026-04-15', '2027-04-15', '2028-04-18', '2029-04-17']);
});

test('the first calendar tax year and state anniversary use different dates', () => {
  const { events, start, end } = plan({ formation: '2026-11-10', today: '2026-11-10', taxStatus: 'due' });
  assert.deepEqual([start, end], ['2026-11-10', '2028-11-09']);
  assert.deepEqual(events.filter(e => e.id.startsWith('irs-')).map(e => [e.id, e.date]),
    [['irs-5472-2026', '2027-04-15'], ['irs-5472-2027', '2028-04-18']]);
  assert.equal(events.find(e => e.id === 'wy-annual-2027').date, '2027-11-01');
});

test('unconfirmed tax status generates a check, and billing date replaces the proxy', () => {
  const { events } = plan({ formation: '2026-10-21', today: '2027-04-10', agentRenewal: '2027-07-03' });
  assert.equal(events.find(e => e.id === 'irs-review-2026').date, '2027-04-10');
  assert.ok(events.find(e => e.id === 'irs-review-2026').description.includes('2027-04-15'));
  assert.ok(!events.some(e => e.id.startsWith('irs-5472') || e.id.startsWith('agent-check')));
  assert.equal(events.find(e => e.id === 'agent-renewal').date, '2027-07-03');
  assert.equal(plan({ formation: '2026-10-21', today: '2027-04-10', agentRenewal: '2029-04-10' }).renewalBeyondRange, true);
});

test('leap-day anniversary estimate stays in February and invalid dates are rejected', () => {
  const { events } = plan({ formation: '2028-02-29', today: '2028-02-29', taxStatus: 'none' });
  assert.equal(events.find(e => e.id === 'agent-check-2029').date, '2029-01-29');
  assert.throws(() => plan({ formation: '2026-02-29', today: '2026-11-10' }), RangeError);
  assert.throws(() => plan({ formation: '2026-11-11', today: '2026-11-10' }), RangeError);
  assert.throws(() => plan({ formation: '2026-10-21', today: '2026-11-10', agentRenewal: '2026-11-01' }), RangeError);
  assert.equal(wyomingToday(new Date('2026-11-10T02:30:00Z')), '2026-11-09');
});

test('the generated .ics contains the visible dates as all-day entries', () => {
  const { events } = plan({ formation: '2026-11-10', today: '2026-11-10', taxStatus: 'due' });
  const file = serialize(events, new Date('2026-11-10T12:00:00Z'));
  assert.ok(file.startsWith('BEGIN:VCALENDAR\r\n'));
  assert.ok(file.endsWith('END:VCALENDAR\r\n'));
  assert.ok(file.split('\r\n').every(line => Buffer.byteLength(line) <= 75));
  assert.deepEqual([...file.matchAll(/DTSTART;VALUE=DATE:(\d{8})/g)].map(m => m[1]), events.map(e => e.date.replaceAll('-', '')));
});

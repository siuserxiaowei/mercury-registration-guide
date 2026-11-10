(() => {
  'use strict';

  const CRLF = '\r\n';
  const encoder = new TextEncoder();

  function escapeText(value) {
    return value.replace(/[\\;,]/g, '\\$&')
      .replace(/\r\n|\r|\n/g, '\\n')
      .replace(/[\u0000-\u0008\u000b-\u001f\u007f]/g, '');
  }

  function foldLine(line) {
    let folded = '';
    let octets = 0;
    for (const character of line) {
      const size = encoder.encode(character).length;
      if (octets + size > 75) {
        folded += CRLF + ' ';
        octets = 1;
      }
      folded += character;
      octets += size;
    }
    return folded;
  }

  function compactDate(date) {
    if (!/^(?!0000)\d{4}-\d{2}-\d{2}$/.test(date)) throw new RangeError('Expected an ISO calendar date');
    const parsed = new Date(`${date}T00:00:00Z`);
    if (Number.isNaN(parsed.valueOf()) || parsed.toISOString().slice(0, 10) !== date) {
      throw new RangeError('Invalid calendar date');
    }
    return date.replace(/-/g, '');
  }

  function serialize(events, now = new Date()) {
    if (events.length === 0) throw new RangeError('A calendar needs at least one event');
    const stamp = now.toISOString().slice(0, 19).replace(/[-:]/g, '') + 'Z';
    const lines = ['BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//Mercury Handbook//Compliance Calendar//ZH-CN'];
    for (const event of events) {
      if (!/^[a-zA-Z0-9._-]+$/.test(event.id)) throw new TypeError('Invalid calendar event identifier');
      const day = compactDate(event.date);
      // A DATE-valued event without DTEND spans one day under RFC 5545.
      lines.push('BEGIN:VEVENT',
        `UID:mercury-handbook-${event.id}-${day}@siuserxiaowei.github.io`,
        `DTSTAMP:${stamp}`,
        `DTSTART;VALUE=DATE:${day}`,
        `SUMMARY:${escapeText(event.title)}`,
        `DESCRIPTION:${escapeText(event.description)}`,
        'TRANSP:TRANSPARENT',
        'END:VEVENT');
    }
    lines.push('END:VCALENDAR');
    return lines.map(foldLine).join(CRLF) + CRLF;
  }

  const calendar = {serialize};
  if (typeof module === 'object' && module.exports) module.exports = calendar;
  else globalThis.MercuryCalendarICS = calendar;
})();

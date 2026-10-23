#!/usr/bin/env python3
"""Build the static handbook using only Python's standard library."""
from pathlib import Path
from html import escape
from urllib.parse import urlsplit, quote
import csv
import io
import json
import re
import shutil

ROOT = Path(__file__).resolve().parents[1]


def safe_url(value):
    if any(ord(c) < 32 for c in value) or "\\" in value:
        return None
    parsed = urlsplit(value)
    if parsed.scheme in ("http", "https") and parsed.netloc and not parsed.username and not parsed.password:
        return value
    if not parsed.scheme and not parsed.netloc:
        if value.startswith("#"):
            return value
        doc_stem = Path(parsed.path).stem
        if parsed.path.endswith('.md') and doc_stem in {'research', 'conclusions', 'full-process', 'checklist'}:
            return '#read-' + doc_stem
        value = re.sub(r"^(?:\.\./)+", "./", value)
        if value.startswith(("./", "content/", "data/")):
            return value
    return None


def inline(value):
    tokens = []

    def hold(markup):
        tokens.append(markup)
        return "\x00TOKEN" + str(len(tokens) - 1) + "\x00"

    value = re.sub(r"`([^`]+)`", lambda m: hold("<code>" + escape(m[1]) + "</code>"), value)

    def link(m):
        url = safe_url(m[2].strip("<>"))
        if url is None:
            return m[1]
        external = url.startswith(("http://", "https://"))
        attrs = ' target="_blank" rel="noopener noreferrer"' if external else ""
        return hold('<a href="' + escape(url, quote=True) + '"' + attrs + ">" + escape(m[1]) + "</a>")

    value = re.sub(r"\[([^\]\n]+)\]\(([^\s)]+)\)", link, value)
    value = escape(value)
    value = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", value)
    value = re.sub(r"\\([\\`*_\[\]$~<#>+|])", r"\1", value)
    return re.sub(r"\x00TOKEN(\d+)\x00", lambda m: tokens[int(m[1])], value)


def table_cells(line):
    return [c.strip().replace("\\|", "|") for c in re.split(r"(?<!\\)\|", line.strip().strip("|"))]


def render_markdown(text, doc_id):
    lines = text.splitlines()
    out, paragraph = [], []
    list_type = None
    counter = 0

    def flush():
        if paragraph:
            out.append("<p>" + inline(" ".join(paragraph)) + "</p>")
            paragraph.clear()

    def close_list():
        nonlocal list_type
        if list_type:
            out.append("</" + list_type + ">")
            list_type = None

    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("```"):
            flush(); close_list()
            code = []
            i += 1
            while i < len(lines) and not lines[i].startswith("```"):
                code.append(lines[i]); i += 1
            out.append("<pre><code>" + escape("\n".join(code)) + "</code></pre>")
        elif not line.strip():
            flush(); close_list()
        elif re.match(r"^#{1,6}\s", line):
            flush(); close_list()
            h = len(line) - len(line.lstrip("#"))
            out.append(f'<h{h}>' + inline(line[h:].strip()) + f'</h{h}>')
        elif i + 1 < len(lines) and "|" in line and re.match(r"^\s*\|?\s*:?-{3,}", lines[i + 1]):
            flush(); close_list()
            headers = table_cells(line)
            out.append('<div class="table-scroll"><table><thead><tr>' + ''.join('<th>' + inline(c) + '</th>' for c in headers) + '</tr></thead><tbody>')
            i += 2
            while i < len(lines) and '|' in lines[i] and lines[i].strip():
                out.append('<tr>' + ''.join('<td>' + inline(c) + '</td>' for c in table_cells(lines[i])) + '</tr>')
                i += 1
            out.append('</tbody></table></div>')
            continue
        elif re.match(r"^\s*(?:[-*]|\d+\.)\s+", line):
            flush()
            ordered = bool(re.match(r"^\s*\d+\.", line))
            kind = 'ol' if ordered else 'ul'
            if list_type != kind:
                close_list(); out.append('<' + kind + '>'); list_type = kind
            value = re.sub(r"^\s*(?:[-*]|\d+\.)\s+", '', line)
            task = re.match(r"^\[([ xX])\]\s+(.*)", value)
            if task:
                counter += 1
                checked = ' checked' if task[1].lower() == 'x' else ''
                out.append(f'<li class="doc-task"><label><input type="checkbox" data-doc-task="{doc_id}-{counter}"{checked}><span>' + inline(task[2]) + '</span></label></li>')
            else:
                out.append('<li>' + inline(value) + '</li>')
        elif line.startswith('>'):
            flush(); close_list(); out.append('<blockquote>' + inline(line.lstrip('> ').strip()) + '</blockquote>')
        elif re.match(r"^\s*[-*_]{3,}\s*$", line):
            flush(); close_list(); out.append('<hr>')
        else:
            close_list(); paragraph.append(line.strip())
        i += 1
    flush(); close_list()
    return '\n'.join(out)


def main():
    dist = ROOT / 'dist'
    (dist / 'content').mkdir(parents=True, exist_ok=True)
    (dist / 'data').mkdir(exist_ok=True)
    index = json.loads((ROOT / 'content/index.json').read_text())
    for doc in index:
        source = ROOT / 'content' / doc['file']
        html_name = doc['id'] + '.html'
        doc['html'] = 'content/' + html_name
        (dist / 'content' / html_name).write_text(render_markdown(source.read_text(), doc['id']))
        shutil.copyfile(source, dist / 'content' / source.name)
    (dist / 'content/index.json').write_text(json.dumps(index, ensure_ascii=False, indent=2))
    shutil.copyfile(ROOT / 'content/business-template.txt', dist / 'content/business-template.txt')
    for source in (ROOT / 'data').glob('*.json'):
        shutil.copyfile(source, dist / 'data' / source.name)
    records = json.loads((ROOT / 'data/catalogue.json').read_text())
    fields = ['id', 'title', 'url', 'platform', 'author', 'published_at', 'curator_status', 'evidence_grade', 'commercial', 'curator_claim', 'review_limitations']
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fields, delimiter='\t', extrasaction='ignore')
    writer.writeheader(); writer.writerows(records)
    (ROOT / 'data/catalogue.tsv').write_text(buf.getvalue())
    shutil.copyfile(ROOT / 'data/catalogue.tsv', dist / 'data/catalogue.tsv')
    (dist / '.nojekyll').write_text('')
    if not (dist / 'index.html').is_file():
        raise RuntimeError('Frontend index.html is not yet available')
    docs = ROOT / 'docs'
    docs.mkdir(exist_ok=True)
    shutil.copytree(dist, docs, dirs_exist_ok=True)
    print(json.dumps({'documents': len(index), 'records': len(records), 'pages_directory': 'docs', 'build_output': 'dist'}))


if __name__ == '__main__':
    main()

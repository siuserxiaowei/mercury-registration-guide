#!/usr/bin/env python3
"""Build the static handbook using only Python's standard library."""
from pathlib import Path
from html import escape
from urllib.parse import urlsplit, quote
import csv
import hashlib
import io
import json
import re
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
STAGE_TITLE = '我现在卡在哪一步？'


def stage_guide_data():
    return json.loads((ROOT / 'data/stages.json').read_text())


def stage_link(label, url, web=False):
    attrs = ' target="_blank" rel="noopener noreferrer"' if web else ''
    return f'<a href="{escape(url, quote=True)}"{attrs}>{escape(label)}</a>'


def stage_list(items):
    return '<ul>' + ''.join(f'<li>{item}</li>' for item in items) + '</ul>'


def render_stage_guide(guide):
    options, cards = [], []
    for index, stage in enumerate(guide['stages']):
        key = escape(stage['id'], quote=True)
        label = escape(stage['label'])
        checked = ' checked' if index == 0 else ''
        options.append(f'<label class="stage-option"><input type="radio" name="handbook-stage" aria-controls="stage-{key}"{checked}><span>{label}</span></label>')
        materials = stage_list(escape(item) for item in stage['materials'])
        links = stage_list(stage_link(*link, web=True) for link in stage['links'])
        cards.append(f'<article class="stage-result" id="stage-{key}" aria-labelledby="stage-title-{key}">'
                     f'<div class="stage-result-head"><h3 id="stage-title-{key}">{label}</h3>'
                     f'<p><strong>下一步：</strong>{escape(stage["next"])}</p></div>'
                     f'<div class="stage-result-grid"><div class="stage-materials"><h4>还缺哪些材料？</h4>{materials}</div>'
                     f'<div class="stage-links"><h4>官方入口</h4>{links}</div></div>'
                     f'<p class="stage-note">{escape(stage["note"])}</p></article>')
    return '\n'.join([
        '<section id="stage-guide" class="stage-guide observed-section" aria-labelledby="stage-guide-title">',
        f'  <div class="section-heading"><div><span class="section-kicker">01 / 按进度找下一步</span><h2 id="stage-guide-title">{STAGE_TITLE}</h2></div><p>{escape(guide["scope"])}</p></div>',
        '  <div class="stage-guide-shell">',
        '    <fieldset class="stage-picker" id="stage-picker" aria-describedby="stage-guide-note" hidden><legend>选择你的进度</legend>',
        *('      ' + option for option in options),
        '    </fieldset>',
        '    <div class="stage-results" id="stage-results">',
        *('      ' + card for card in cards),
        '    </div>',
        '  </div>',
        '  <p id="stage-status" class="sr-only" role="status"></p>',
        f'  <p class="stage-guide-note" id="stage-guide-note">无需填写个人信息；此处的选择不保存、不上传。入口核对于 {escape(guide["verified_on"])}。<a href="#read-checklist">查看完整操作清单</a></p>',
        '</section>',
    ])


def render_feishu_stage(guide):
    page = json.loads((ROOT / 'data/publication.json').read_text())['page_url']
    blocks = [f'<h2>{STAGE_TITLE}</h2>',
              f'<p>{escape(guide["scope"])} 入口核对于 {escape(guide["verified_on"])}。'
              f'{stage_link("打开在线交互清单", page + "#stage-guide")}（无需填写个人信息；选择不保存、不上传）。</p>']
    for stage in guide['stages']:
        materials = stage_list(escape(item) for item in stage['materials'])
        links = ' · '.join(stage_link(*link) for link in stage['links'])
        blocks.extend([f'<h3>{escape(stage["label"])}</h3>',
                       f'<p><b>下一步：</b>{escape(stage["next"])}</p>',
                       f'<p><b>还缺哪些材料？</b></p>{materials}',
                       f'<p><b>官方入口：</b>{links}</p>',
                       f'<p>{escape(stage["note"])}</p>'])
    return '\n'.join(blocks)


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
    frontend = dist / 'index.html'
    html = frontend.read_text()
    html, count = re.subn(r'(<!-- stage-guide:start -->).*?(<!-- stage-guide:end -->)',
                         lambda m: m[1] + '\n' + render_stage_guide(stage_guide_data()) + '\n      ' + m[2], html, flags=re.S)
    if count != 1:
        raise RuntimeError('Expected one stage guide placeholder')
    for attr, asset in [('src', 'app.js'), ('href', 'styles.css')]:
        version = hashlib.sha256((dist / asset).read_bytes()).hexdigest()[:12]
        html = re.sub(rf'{attr}="{re.escape(asset)}(?:\?[^"]*)?"', f'{attr}="{asset}?v={version}"', html)
    frontend.write_text(html)
    docs = ROOT / 'docs'
    docs.mkdir(exist_ok=True)
    shutil.copytree(dist, docs, dirs_exist_ok=True)
    print(json.dumps({'documents': len(index), 'records': len(records), 'pages_directory': 'docs', 'build_output': 'dist'}))


if __name__ == '__main__':
    if sys.argv[1:] == ['--feishu-stage-xml']:
        print(render_feishu_stage(stage_guide_data()))
    else:
        main()

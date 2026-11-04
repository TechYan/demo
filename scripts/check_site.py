"""Validate the built static site, package completeness, local links and PVKit bytes."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote
import hashlib
import json
import re
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else 'dist').resolve()
repo = Path(__file__).resolve().parents[1]
base = sys.argv[2].rstrip('/') if len(sys.argv) > 2 else ''
assert root.is_dir(), root
projects = json.loads((repo / 'src/data/projects.json').read_text(encoding='utf-8'))
assert {'pvkit', 'bus-protocol-lab', 'pg_gen', 'uvm_wiki', 'svip', 'xpggen', 'xDCT'} <= {p['id'] for p in projects}

class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.ids = set()

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if values.get('id'):
            self.ids.add(values['id'])
        for attr in ('href', 'src'):
            if values.get(attr):
                self.links.append(values[attr])

count = 0
pages = list(root.rglob('*.html'))
for page in pages:
    text = page.read_text(encoding='utf-8')
    assert not re.search(r'[CD]:[\\/]+(?:Users|work)|/mnt/d/work/', text), page
    parser = Links()
    parser.feed(text)
    for link in parser.links:
        url = urlsplit(link)
        if url.scheme or url.netloc or not url.path:
            continue
        name = unquote(url.path)
        if name.startswith('/'):
            assert not base or name == base or name.startswith(base + '/'), (page, link, 'missing deployment base')
            target = root / (name[len(base):] if base else name).lstrip('/')
        else:
            target = page.parent / name
        target = target.resolve()
        assert target.is_relative_to(root), (page, link, 'outside build')
        assert target.exists(), (page.relative_to(root), link)
        if target.is_dir():
            assert (target / 'index.html').is_file(), (page, link)
        count += 1

for project in projects:
    assert (root / 'projects' / project['id'] / 'index.html').is_file(), project['id']
    assert (root / project['primary']).is_file(), project['primary']
    for action in project['actions']:
        assert (root / action['path']).is_file(), action['path']

checksums = (root / 'pvkit/SHA256SUMS').read_text().splitlines()
for line in checksums:
    sha, name = line.split('  ', 1)
    assert hashlib.sha256((root / 'pvkit' / name).read_bytes()).hexdigest() == sha, name
manifest = json.loads((root / 'pvkit/manifest.json').read_text(encoding='utf-8'))
assert len(manifest['scenarios']) == 15
assert {s['protocol'] for s in manifest['scenarios']} == {'axi4', 'cxl_native'}

for path in root.rglob('*'):
    if path.is_file():
        assert path.stat().st_size < 25 * 1024 * 1024, ('Cloudflare asset limit', path)
        assert not any(part in {'node_modules', '.git', '.wrangler', 'incoming', 'raw'} for part in path.parts), path
        assert path.suffix not in {'.pyz', '.pyd', '.whl', '.fsdb', '.kdb'}, path
        assert path.name not in {'pcie_hub_reg_rdf.json', 'pcie_private_reg_rdf.json', 'phu_reg_rdf.json'}, path

print(f'PASS: {len(pages)} HTML pages, {count} local links, {len(projects)} project routes, {len(checksums)} preserved PVKit hashes; deployment base {base or "/"}.')

#!/usr/bin/env python3
"""Build and validate the portable UVM Wiki and scoped SVIP documentation demos."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import posixpath
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
GUIDES = [
    ("axi/doc/user-guide.html", "AXI4 · User guide"),
    ("axi/doc/architecture.html", "AXI4 · Architecture"),
    ("axi/doc/protocol-checks.html", "AXI4 · Protocol checks"),
    ("apb/doc/user-guide.html", "APB · User guide"),
    ("apb/doc/architecture.html", "APB · Architecture"),
    ("apb/doc/usage-cookbook.html", "APB · Usage cookbook"),
    ("jtag/doc/user-guide.html", "JTAG · User guide"),
    ("jtag/doc/architecture.html", "JTAG · Architecture"),
    ("spi/doc/user-guide.html", "SPI · User guide"),
    ("spi/doc/architecture.html", "SPI · Architecture"),
    ("control/doc/user-guide.html", "Control · User guide"),
    ("control/doc/architecture.html", "Control · Architecture"),
    ("control/doc/recipes.html", "Control · Recipes"),
]
EXAMPLES = [
    "axi/testsuite/examples/svip_axi_callbacks_example.svh",
    "axi/testsuite/examples/svip_axi_controls_example.svh",
    "axi/testsuite/examples/svip_axi_observation_example.svh",
    "axi/testsuite/examples/svip_axi_patterns_example.svh",
    "axi/testsuite/examples/svip_axi_reset_example.svh",
    "axi/testsuite/examples/svip_axi_slave_model_example.svh",
    "axi/testsuite/examples/svip_axi_timing_example.svh",
    "apb/testsuite/examples/svip_apb_control_examples.svh",
    "apb/testsuite/examples/svip_apb_examples.svh",
    "jtag/testsuite/examples/svip_jtag_examples.svh",
    "spi/testsuite/examples/svip_spi_examples.svh",
    "control/clock/examples/svip_clock_example.sv",
    "control/reset/examples/svip_reset_example.sv",
    "control/signal/examples/svip_signal_example.sv",
    "control/coordinator/examples/svip_clock_signal_example.sv",
    "control/testsuite/examples/svip_control_examples.svh",
    "control/testbench/svip_control_quickstart.sv",
]

STYLE = """
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:#f4f6fa;color:#172033;font:16px/1.7 system-ui,-apple-system,'Segoe UI',sans-serif}main{max-width:1120px;margin:auto;padding:45px 28px 80px}a{color:#3159cc;text-underline-offset:4px}nav{display:flex;gap:20px;flex-wrap:wrap;font-size:14px}h1{font-size:clamp(36px,5vw,62px);letter-spacing:-2px;line-height:1.1;margin:34px 0 22px}h2{font-size:26px;letter-spacing:-.5px;margin:44px 0 18px}h3{margin:0 0 8px;font-size:20px}.eyebrow{color:#607089;font-size:12px;font-weight:700;letter-spacing:2px;text-transform:uppercase;margin-top:40px}.lead{max-width:800px;font-size:20px;color:#536078}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(245px,1fr));gap:18px;margin:28px 0}.card{padding:24px;background:#fff;border:1px solid #dce2ec;border-radius:12px}.card p{color:#536078;margin-bottom:0}.card .number{font-size:34px;font-weight:700;color:#172033}.actions{display:flex;gap:12px;flex-wrap:wrap;margin:28px 0}.button{display:inline-block;padding:12px 20px;background:#3159cc;color:#fff;border-radius:7px;text-decoration:none;font-weight:600}.button.secondary{background:#fff;color:#3159cc;border:1px solid #dce2ec}.note{padding:18px 22px;background:#eaf0ff;border-left:3px solid #5279e1;border-radius:0 8px 8px 0;color:#394c76}.muted{color:#607089;font-size:14px}code,pre{font-family:Consolas,'Courier New',monospace}code{font-size:.9em;overflow-wrap:anywhere}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#101b30;color:#dce8fc;padding:22px;border-radius:8px;font-size:13px;line-height:1.65}.source-section{scroll-margin-top:24px;border-top:1px solid #dce2ec;margin-top:32px;padding-top:20px}.source-section h2{font-size:20px;overflow-wrap:anywhere}table{width:100%;border-collapse:collapse;background:#fff;font-size:14px}td,th{text-align:left;border:1px solid #dce2ec;padding:12px}ul{padding-left:22px}li{margin:6px 0}.tag{display:inline-block;font-size:11px;font-weight:700;letter-spacing:1px;padding:4px 8px;border-radius:4px;background:#e9efff;color:#3159cc}footer{margin-top:50px;padding-top:22px;border-top:1px solid #dce2ec;color:#607089;font-size:13px}@media(max-width:600px){main{padding:24px 18px 55px}h1{letter-spacing:-1px}table{font-size:12px}td,th{padding:8px}.card{padding:19px}}
"""


def write(path: Path, value: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8", newline="\n")


def page(title: str, body: str, nav: str = '<a href="index.html">← Package index</a>') -> str:
    return f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(title)}</title><style>{STYLE}</style></head><body><main><nav>{nav}</nav>{body}<footer>TechYan / Demo · Portable documentation and source examples · <a href="provenance.json">Source provenance</a></footer></main></body></html>\n'


def revision(repo: Path) -> str:
    return subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()


def file_record(path: Path, relative: str) -> dict:
    return {"path": relative, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "bytes": path.stat().st_size}


def anchor(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def source_page(package: Path, files: list[Path], title: str, intro: str):
    toc = "".join(f'<li><a href="#{anchor(p.relative_to(package).as_posix())}">{html.escape(p.relative_to(package).as_posix())}</a></li>' for p in files)
    sections = "".join(f'<section class="source-section" id="{anchor(p.relative_to(package).as_posix())}"><h2>{html.escape(p.relative_to(package).as_posix())}</h2><p><a href="{p.relative_to(package).as_posix()}" download>Download original source</a> · {len(p.read_text(encoding="utf-8").splitlines())} lines</p><pre><code>{html.escape(p.read_text(encoding="utf-8"))}</code></pre></section>' for p in files)
    write(package / "sources.html", page(title, f'<p class="eyebrow">Source browser</p><h1>{title}</h1><p class="lead">{intro}</p><ul>{toc}</ul>{sections}'))


def build_uvm(repo: Path):
    package = ROOT / "uvm_wiki"
    fixture = package / "examples/demo_uvm"
    shutil.copytree(repo / "examples/demo_uvm", fixture, dirs_exist_ok=True)
    sys.path.insert(0, str(repo / "uvm-wiki/scripts"))
    from uvm_wiki_core import build_index, build_snippets
    from uvm_wiki_filelist import expand_project_includes, parse_filelists, require_sources_within_root
    from uvm_wiki_web import render_html

    spec = parse_filelists([fixture / "filelist.f"])
    require_sources_within_root(spec, fixture)
    expand_project_includes(spec, fixture)
    # The upstream generator caches outside the published artifact tree.
    cache = repo.parent / "uvm-wiki-demo-cache.json"
    data = build_index(fixture, "auto", cache, source_context=120, rebuild=True,
                       source_paths=spec.sources, include_dirs=spec.include_dirs,
                       defines=spec.defines, input_metadata=spec.metadata(fixture))
    data["snippets"].update(build_snippets(fixture, [{"file": item["path"], "line": 1} for item in data["files"]], 120))
    data["metadata"]["source_root"] = "examples/demo_uvm"
    data["metadata"]["cache"].pop("cache_path", None)
    data["metadata"]["demo"] = {
        "source_revision": revision(repo),
        "portable": True,
        "simulation_run": False,
        "limits": ["Static per-file syntax index, not simulator elaboration.",
                   "UVM library definitions and uvm_macros.svh are external and are not bundled.",
                   "Factory overrides, dynamic instances, and exact runtime binding are unresolved.",
                   "Portable HTML uses embedded source; full-text source search requires upstream serve mode."],
    }
    # Publish relative paths only, including any diagnostic strings from the parser.
    payload = json.dumps(data, ensure_ascii=False, indent=2)
    for local in (str(fixture.resolve()), str(repo.resolve()), str(cache.resolve())):
        payload = payload.replace(json.dumps(local)[1:-1], "examples/demo_uvm")
    data = json.loads(payload)
    write(package / "uvm_wiki_ai.json", payload + "\n")
    rendered = render_html(data)
    server_mode = 'server:location.protocol==="http:"||location.protocol==="https:"'
    assert rendered.count(server_mode) == 1, "Upstream server-mode initialization changed"
    rendered = rendered.replace(server_mode, "server:false", 1)
    rendered = rendered.replace('wikiMode:"extends"', 'wikiMode:"all"', 1)
    rendered = rendered.replace('<button class="active" data-graph-mode="extends">Inheritance</button><button data-graph-mode="all">All relations</button>', '<button data-graph-mode="extends" title="Only local class-to-class inheritance; UVM bases are shown in Class Hierarchy">Inheritance</button><button class="active" data-graph-mode="all">All relations</button>', 1)
    rendered = rendered.replace('<div class="toolbar wiki-toolbar">', '<div class="toolbar wiki-toolbar"><span class="hint" title="This fixture extends external UVM bases. Use Class Hierarchy for those inheritance links.">Local class relations</span>', 1)
    rendered = rendered.replace('<header><div class="brand">', '<header><div class="brand"><a href="index.html" style="color:#3159cc;text-decoration:none;margin-right:12px;font-size:12px">← Demo</a>', 1)
    write(package / "uvm_wiki.html", rendered)
    shutil.copy2(repo / "uvm-wiki/assets/vendor/D3-LICENSE.txt", package / "D3-LICENSE.txt")
    files = sorted(p for p in fixture.rglob("*") if p.is_file())
    source_page(package, files, "The complete UVM fixture", "A sanitized ready/valid environment: test, environment, agent, sequence, scoreboard, coverage, interface, and a small DUT. These are the exact source files used to generate the interactive wiki.")
    stats = data["stats"]
    input_info = data["metadata"]["input"]
    diagnostic_count = sum(item.get("diagnostics", 0) for item in data["files"])
    cards = "".join(f'<div class="card"><div class="number">{stats[key]}</div><p>{label}</p></div>' for key, label in [("files", "HDL source files"), ("classes", "UVM classes"), ("relations", "Static relations"), ("connections", "TLM connections")])
    views = [("Architecture", "Follow test → env → agent and inspect the virtual-interface boundary."), ("Topology", "Expand factory-created instances and jump to their source evidence."), ("Class Hierarchy", "Explore inherited UVM component, object, and sequence types."), ("TLM Connections", "Inspect item ports, exports, implementations, and connect calls."), ("Phase Map", "Compare declared and inherited UVM phase implementations."), ("Wiki Graph", "Explore local class relationships. Class Hierarchy also shows external UVM inheritance bases."), ("Code Explorer", "Browse indexed definitions and the embedded source preview.")]
    view_cards = "".join(f'<div class="card"><h3>{name}</h3><p>{description}</p></div>' for name, description in views)
    body = f'''<p class="eyebrow">UVM Wiki · Interactive source atlas</p><h1>One environment.<br>Seven ways to understand it.</h1><p class="lead">Explore a real generated SystemVerilog / UVM index. Every graph, connection, and phase is derived from the bundled sanitized source fixture.</p><div class="actions"><a class="button" href="uvm_wiki.html">Open interactive wiki ↗</a><a class="button secondary" href="sources.html">Browse complete source</a><a class="button secondary" href="uvm_wiki_ai.json" download>Download AI index</a></div><div class="grid">{cards}</div><div class="note">Generated with <strong>{html.escape(data['metadata']['parser_effective'])}</strong> in filelist mode. The application embeds its data and D3; it opens as a standalone HTML file and requires no CDN or service.</div><h2>Start with architecture, then follow the evidence</h2><p>Select <code>demo_smoke_test</code>, enter <code>env</code>, and expand the agent. The monitor publishes items to both the scoreboard and coverage. The driver uses the sequencer's item export. Click a wire or a class to see the relevant source.</p><div class="grid">{view_cards}</div><h2 id="limits">What this demo establishes</h2><p>This is a static, per-file source index. It is not simulator elaboration or a passing simulation result. Runtime factory overrides, dynamic instances, and exact DUT/BFM binding need runtime evidence. UVM library definitions and <code>uvm_macros.svh</code> are external to the fixture; the filelist intentionally treats the UVM macro include as an external library include. The parser reports {diagnostic_count} per-file syntax diagnostics; this index is not compilation evidence.</p><p>The portable wiki embeds source context for graph and definition browsing. Full-text source search is an upstream serve-mode feature; the <a href="sources.html">complete static source browser</a> is available here for every bundled file.</p><p class="muted">Source revision: <code>{revision(repo)}</code> · {len(input_info.get('unresolved_includes', []))} unresolved project includes · <a href="README.md">Build and provenance notes</a> · <a href="D3-LICENSE.txt">D3 license</a></p>'''
    write(package / "index.html", page("UVM Wiki · Interactive demo", body, '<a href="../index.html">← All projects</a><a href="https://github.com/TechYan/uvm_wiki">Source repository ↗</a>'))
    provenance = {
        "project": "uvm_wiki", "repository": "https://github.com/TechYan/uvm_wiki", "source_revision": revision(repo),
        "generated_at": data["metadata"]["generated_at"], "generator": "uvm-wiki/scripts/uvm_wiki_core.py + uvm_wiki_filelist.py + uvm_wiki_web.py",
        "parser": data["metadata"]["parser_effective"], "parser_fallback_files": data["metadata"]["parser_fallback_files"],
        "per_file_syntax_diagnostics": diagnostic_count,
        "publication_changes": ["Relative metadata paths and no cache path", "Link back to package index", "Ensure embedded line-one source preview for every HDL file", "Force embedded-source mode on static HTTP hosting", "Default Wiki Graph to All relations; external UVM inheritance remains in Class Hierarchy"],
        "stats": stats, "simulation_run": False,
        "published_source_files": [file_record(p, p.relative_to(package).as_posix()) for p in files],
    }
    write(package / "provenance.json", json.dumps(provenance, indent=2, ensure_ascii=False) + "\n")
    write(package / "README.md", f'''# UVM Wiki portable demo

Open [the package index](index.html) or [the unified interactive wiki](uvm_wiki.html).

The genuine generated application includes Architecture, Topology, Class Hierarchy, TLM Connections, Phase Map, Wiki Graph, and Code Explorer. Its JSON data and D3 are embedded; it requires no server or CDN. [The full fixture](sources.html) is also bundled as readable and downloadable source.

## Source and generation

- Source: https://github.com/TechYan/uvm_wiki
- Revision: `{revision(repo)}`
- Fixture: upstream `examples/demo_uvm`, copied without source changes.
- Generator: upstream `uvm-wiki/scripts/uvm_wiki_core.py`, `uvm_wiki_filelist.py`, and `uvm_wiki_web.py`.
- Effective parser: `{data['metadata']['parser_effective']}`; {data['metadata']['parser_fallback_files']} fallback files.
- Input: `examples/demo_uvm/filelist.f`, including nested RTL filelist and local include closure.
- Result: {stats['files']} HDL files, {stats['classes']} classes, {stats['relations']} relations, {stats['ports']} TLM ports, {stats['connections']} connections.
- Publication changes: relative metadata paths, no cache path, one link back to this package, a static source browser, provenance hashes, forced embedded-source mode on static HTTP hosting, and Wiki Graph initially set to All relations.

Use `python scripts/build_uvm_svip.py --uvm-source <local-uvm-wiki-checkout> --svip-source <local-svip-checkout>` from the demo checkout to reproduce this package. It uses the upstream generator directly; no wheels or parser runtime are copied into the published demo. Use `--check` to verify the generated package.

## Exact limits

This is a static per-file syntax index, not simulator elaboration. Runtime factory overrides, dynamic instances, and exact DUT/BFM binding are unresolved. The UVM library and its `uvm_macros.svh` are not bundled; the generator intentionally excludes that standard external library include from unresolved project include warnings. There are {len(input_info.get('unresolved_includes', []))} unresolved project includes and {diagnostic_count} per-file syntax diagnostics. The index is not a compilation report and absent library macros can affect per-file syntax diagnostics.

Source previews use embedded context (120 lines before and after a location, sufficient for each small fixture file). This publication forces embedded-source mode even when hosted over HTTP/HTTPS, because a static host has no upstream source API. Full-text source search requires generating/using upstream serve-mode output. Every complete fixture source is available separately in `sources.html` and `examples/demo_uvm/`.

Wiki Graph opens on All relations (11 local class nodes and 20 edges). Its Inheritance projection includes only source-backed class-to-class edges; this fixture's classes all extend external UVM bases, so that projection is empty. Class Hierarchy explicitly includes the external UVM inheritance bases and is the appropriate view for them.

No simulation, coverage run, or passing DUT result was produced for this static publication. [provenance.json](provenance.json) records the input revision and SHA-256 for each copied source. D3 attribution and its license are retained in the embedded library and [D3-LICENSE.txt](D3-LICENSE.txt).
''')
    return provenance


def build_svip(repo: Path):
    package = ROOT / "svip"
    package.mkdir(parents=True, exist_ok=True)
    examples = [repo / name for name in EXAMPLES]
    published = []
    for original in examples:
        target = package / original.relative_to(repo)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(original, target)
        published.append(target)
    source_page(package, published, "Reusable SVIP examples", "Original SystemVerilog examples for AXI4, APB, JTAG, SPI, and Clock / Reset / Signal. They demonstrate the documented APIs. Running them requires the full SVIP runtime and VCS/UVM 1.2; the static snapshot contains their source, not simulation results.")
    selected = {name for name, _ in GUIDES}
    sample_paths = {p.relative_to(repo).as_posix() for p in examples}

    def relative_link(origin: str, target: str) -> str:
        location, _, fragment = target.partition("#")
        return posixpath.relpath(location, posixpath.dirname(origin)) + ("#" + fragment if fragment else "")

    def rewrite_link(origin: str, value: str) -> str:
        url = urlsplit(html.unescape(value))
        if url.scheme or url.netloc or value.startswith("#"):
            return value
        resolved = posixpath.normpath(posixpath.join(posixpath.dirname(origin), url.path))
        html_equivalent = resolved[:-3] + ".html" if resolved.endswith(".md") else resolved
        if html_equivalent in selected:
            return relative_link(origin, html_equivalent) + ("#" + url.fragment if url.fragment else "")
        if resolved in sample_paths:
            return relative_link(origin, "sources.html#" + anchor(resolved))
        if resolved.endswith("README.md") and (resolved == "README.md" or resolved == "control/README.md"):
            return relative_link(origin, "index.html")
        if "verification" in resolved:
            return relative_link(origin, "scope.html#verification")
        if "checker" in resolved:
            return relative_link(origin, "scope.html#checkers")
        if "testsuite" in resolved:
            protocol = origin.split("/")[0]
            return relative_link(origin, f"examples.html#{protocol}")
        return relative_link(origin, "scope.html#runtime")

    for name, _ in GUIDES:
        content = (repo / name).read_text(encoding="utf-8")
        content = re.sub(r'(href|src)=("|\')([^"\']+)\2', lambda m: f'{m[1]}={m[2]}{rewrite_link(name, m[3])}{m[2]}', content)
        content = content.replace("本页Markdown", "本页文档").replace(">Markdown<", ">文档页<")
        home = relative_link(name, "index.html")
        scope = relative_link(name, "scope.html")
        banner = f'<div style="padding:10px 18px;background:#eaf0ff;color:#283f74;font:13px/1.6 system-ui;border-bottom:1px solid #bdccef"><a style="color:#244ab3" href="{home}">← SVIP demo</a> · 文档与示例快照 · 运行库、历史验收记录及仿真日志未打包 · <a style="color:#244ab3" href="{scope}">阅读范围说明</a></div>'
        # Some upstream control documents omit an explicit body start tag.
        if re.search(r"<body\b[^>]*>", content, flags=re.I):
            content = re.sub(r"(<body\b[^>]*>)", lambda m: m[1] + banner, content, count=1, flags=re.I)
        else:
            content = content.replace("</style>", "</style>" + banner, 1)
        write(package / name, content)

    protocol_text = {
        "axi": ("AXI4", "Manager / subordinate / passive; independent read/write IDs, outstanding traffic, timing policies, and response ownership."),
        "apb": ("APB3 / APB4", "Requester and passive use; byte strobes, wait states, response checking, RAL, and practical control recipes."),
        "jtag": ("JTAG", "Master / passive / optional TAP device; segmented scans, TDO masks, clock pause, and multi-TAP chain helpers."),
        "spi": ("SPI", "Standard four-wire master / slave / passive; modes 0–3, command-driven responses, timing, and validity masks."),
        "control": ("Clock · Reset · Signal", "Reusable pin control; clock start/stop, reset epochs, signal capture, profiles, tieoff, fuse/strap, and IRQ."),
    }
    cards = []
    example_sections = []
    for protocol, (title, description) in protocol_text.items():
        links = "".join(f'<li><a href="{name}">{label.split(" · ", 1)[1]}</a></li>' for name, label in GUIDES if name.startswith(protocol + "/"))
        cards.append(f'<section class="card"><span class="tag">{protocol.upper()}</span><h2 style="margin-top:14px">{title}</h2><p>{description}</p><ul>{links}</ul><a href="examples.html#{protocol}">Browse source examples →</a></section>')
        sources = [p for p in published if p.relative_to(package).parts[0] == protocol]
        sample_links = "".join(f'<li><a href="sources.html#{anchor(p.relative_to(package).as_posix())}">{html.escape(p.name)}</a> <span class="muted">· {len(p.read_text(encoding="utf-8").splitlines())} lines</span></li>' for p in sources)
        example_sections.append(f'<section id="{protocol}"><h2>{title}</h2><p>{description}</p><ul>{sample_links}</ul><p><a href="{protocol}/doc/user-guide.html">Read the user guide →</a></p></section>')
    body = f'''<p class="eyebrow">SVIP · Documentation + examples</p><h1>Five verification domains.<br>A practical guide for each.</h1><p class="lead">Browse complete user guides and architecture notes for AXI4, APB, JTAG, SPI, and Clock / Reset / Signal, with source examples for the documented APIs.</p><div class="grid"><div class="card"><div class="number">5</div><p>Protocol / control domains</p></div><div class="card"><div class="number">13</div><p>Complete offline HTML guides</p></div><div class="card"><div class="number">{len(published)}</div><p>Original source examples</p></div></div><div class="note">This public snapshot contains documentation and reusable examples. The full SVIP runtime, commercial checker source, internal fixtures, and historical acceptance evidence are outside this package. <a href="scope.html">Read the scope and support notes →</a></div><div class="grid">{''.join(cards)}</div><h2>Choose an entry</h2><p>Start with a user guide for initial integration and API contracts. Architecture pages explain ownership, timing, observations, and reset behavior. The APB cookbook and Control recipes organize practical tasks; AXI4 protocol checks list the monitor's explicit rules.</p><div class="actions"><a class="button" href="examples.html">Explore reusable examples</a><a class="button secondary" href="scope.html">Scope + runtime requirements</a></div><p class="muted">Author: syan · VCS / UVM 1.2 documentation snapshot · Revision <code>{revision(repo)}</code></p>'''
    write(package / "index.html", page("SVIP · Guides and examples", body, '<a href="../index.html">← All projects</a><a href="examples.html">Source examples</a><a href="scope.html">Scope + support</a>'))
    write(package / "examples.html", page("SVIP source examples", f'<p class="eyebrow">API recipes · Original source</p><h1>Read the code behind the guides.</h1><p class="lead">{len(published)} source examples copied from the source revision. These are reusable sequences and small example tops, with original SPDX and author comments retained.</p><div class="note">The standalone Control tops use a small example receiver. Protocol sequences may refer to base sequences or independent peer fixtures from the full test suite. Those supporting runtime classes are not included. No example was simulated for this static publication. See <a href="scope.html#runtime">runtime requirements</a>.</div>{''.join(example_sections)}'))
    scope = '''<p class="eyebrow">Publication scope</p><h1>What is in this snapshot.</h1><p class="lead">Complete guides, architecture notes, and reusable example source for reading and adaptation. A static demo of the documentation and APIs.</p><h2 id="included">Included material</h2><p>The package has all five user guides, all five architecture guides, AXI4 protocol checks, the APB usage cookbook, and Control recipes. It also contains the original public-API examples and small standalone Control example tops. Author and SPDX notices remain intact.</p><h2 id="runtime">Runtime and source requirements</h2><p>Commands and compile filelists shown in the original guides are instructions for the full SVIP workspace. Running them requires its runtime packages, UVM 1.2, VCS, and an appropriate simulator environment. This demo does not bundle the protocol implementation, control backends, build scripts, complete filelists, compliance tests, or independent peer fixtures. Example sequences can reference those runtime base classes; their complete source is presented for learning rather than claimed as a standalone simulator distribution.</p><p>The small Control example tops model a clock/reset/configuration interface and, where needed, a simple receiving register. They are reusable demonstrations, not internal DUT source. Product-specific DUTs, site configuration, credentials, and internal integration instructions are not published.</p><h2 id="verification">Verification and historical records</h2><p>No VCS/UVM simulation, coverage run, tracker capture, or DUT acceptance run was performed to build this static snapshot. Upstream guides discuss supported profiles and refer to acceptance records; those statements remain source documentation. Historical round-by-round verification pages, logs, waveforms, hashes of private test runs, and compliance catalogs are not included here.</p><p>A guide link that originally targeted such a record leads to this section so its evidence boundary is explicit. Use the guide's declared API and protocol limits as documentation; this site does not supply a new passing simulation claim or formal protocol certification.</p><h2 id="checkers">Protocol checking</h2><p><strong>AXI4:</strong> the <a href="axi/doc/protocol-checks.html">protocol-checks guide</a> describes SVIP monitor rules, raw four-state checks, dependency tracking, active byte lanes, and reset behavior. Arm BP063 / Axi4PC is a separately installed independent checker; its implementation and adapter are not bundled in this demo.</p><p><strong>APB:</strong> the <a href="apb/doc/user-guide.html">user guide</a> and <a href="apb/doc/architecture.html">architecture</a> describe selected ACCESS windows, wait-state stability, active byte lanes, X responses, reset abort, and RAL observations. PREADY matters in selected ACCESS; PSLVERR matters at completion. A successful bus command does not automatically prove a DUT side effect.</p><p><strong>SPI / JTAG:</strong> the <a href="spi/doc/architecture.html">SPI architecture</a> and <a href="jtag/doc/architecture.html">JTAG architecture</a> describe the supported profiles, ownership, sample windows, timing, reset, and frame/scan reconstruction. Numerical timing windows must match the connected device.</p><h2 id="links">How navigation is packaged</h2><p>Links among the 13 selected guides point to their bundled HTML version. Example links open the local source browser. Full-runtime, checker integration, compliance, and historical verification references lead to these scope notes or the curated examples index. No private repository URL is required to browse the package.</p><p><a href="index.html">Return to the 13-guide index →</a> · <a href="sources.html">Open all reusable source →</a></p>'''
    write(package / "scope.html", page("SVIP · Scope and support notes", scope))
    provenance = {
        "project": "svip", "source_repository": "TechYan/svip", "source_repository_visibility": "private (unchanged)",
        "source_revision": revision(repo), "published_at": datetime.now(timezone.utc).isoformat(),
        "publication_scope": "Owner-authorized documentation and reusable own examples only",
        "simulation_run": False, "guide_count": len(GUIDES), "example_count": len(published),
        "guide_modifications": ["Local relative links", "Documentation snapshot banner", "Markdown navigation labels updated to HTML"],
        "source_guides": [file_record(repo / name, name) for name, _ in GUIDES],
        "published_examples": [file_record(p, p.relative_to(package).as_posix()) for p in published],
        "excluded": ["Full VIP runtime", "Commercial checker implementation", "Internal DUT/integration source", "Historical verification records", "Credentials/site configuration", "Compliance tests/private-run catalogs"],
    }
    write(package / "provenance.json", json.dumps(provenance, indent=2, ensure_ascii=False) + "\n")
    write(package / "README.md", f'''# SVIP documentation and source example demo

Open [the complete guide index](index.html), [reusable examples](examples.html), or [the source browser](sources.html).

## Source and scope

- Source repository: `TechYan/svip`; its visibility remains private.
- Source revision: `{revision(repo)}`.
- Author: syan.
- Owner-authorized public scope: complete user-facing documentation and reusable own source examples.
- Included: all 5 user guides, all 5 architecture pages, AXI4 protocol checks, APB usage cookbook, Control recipes; {len(published)} original SystemVerilog example files.
- Excluded: full VIP runtime, commercial checker source, internal DUT or site integration source, credentials, historical round-verification pages/logs, and compliance/private-run catalogs.

Guide contents are preserved from the source revision. Publication edits add a scope banner, rewrite local navigation, and replace Markdown navigation labels with HTML labels. All 13 guides are self-contained HTML. Selected-document Markdown references resolve to their HTML page; reusable examples resolve to the local source browser. References to unbundled runtime, verification records, or checker integration resolve to [explicit scope notes](scope.html), not private URLs.

Original example source and SPDX/author comments are preserved. Some protocol sequences use base classes and peer fixtures from the full runtime; only the reusable examples are bundled. The Control quickstart is a small example receiver, not an internal DUT. The [source browser](sources.html) describes these execution dependencies.

## Rebuild and verification

With local source checkouts, run `python scripts/build_uvm_svip.py --uvm-source <uvm-wiki-checkout> --svip-source <svip-checkout>` from the demo checkout. Then run `python scripts/build_uvm_svip.py --check` to validate the static package links and UVM artifact invariants.

[provenance.json](provenance.json) records the exact revision and SHA-256 for each original guide and copied example. The published guide files differ only by the documented link/banner changes. No credentials are used or stored by the builder; fetch source checkouts separately through an authorized Git client.

No simulator, coverage run, tracker capture, or DUT acceptance run was executed for this publication. Source documentation's support and acceptance statements are not new simulation evidence. No synthetic passing tracker or coverage output is provided.
''')
    return provenance


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.ids = set()

    def handle_starttag(self, tag, attrs):
        for name, value in attrs:
            if name in ("href", "src") and value:
                self.links.append(value)
            if name == "id":
                self.ids.add(value)


def check():
    for package in ("uvm_wiki", "svip"):
        assert (ROOT / package / "index.html").is_file(), f"Missing {package}/index.html"
        assert (ROOT / package / "README.md").is_file(), f"Missing {package}/README.md"
        assert (ROOT / package / "provenance.json").is_file(), f"Missing {package}/provenance.json"
    wiki = json.loads((ROOT / "uvm_wiki/uvm_wiki_ai.json").read_text(encoding="utf-8"))
    assert wiki["stats"]["files"] == 15, wiki["stats"]
    assert wiki["stats"]["classes"] == 11, wiki["stats"]
    assert wiki["stats"]["connections"] >= 3, wiki["stats"]
    assert wiki["metadata"]["source_root"] == "examples/demo_uvm"
    wiki_html = (ROOT / "uvm_wiki/uvm_wiki.html").read_text(encoding="utf-8")
    assert "server:location.protocol" not in wiki_html, "Portable static host must use embedded source"
    assert all(f"{item['path']}:1" in wiki["snippets"] for item in wiki["files"]), "A source-file preview is missing"
    for name, _ in GUIDES:
        assert (ROOT / "svip" / name).is_file(), f"Missing guide: {name}"
    assert len(list((ROOT / "svip").rglob("*.sv"))) + len(list((ROOT / "svip").rglob("*.svh"))) == len(EXAMPLES)
    for name in EXAMPLES:
        assert (ROOT / "svip" / name).is_file(), f"Missing source example: {name}"
    parser_cache = {}
    checked_links = 0
    for package in ("uvm_wiki", "svip"):
        for path in (ROOT / package).rglob("*.html"):
            content = path.read_text(encoding="utf-8")
            assert not re.search(r"[A-Za-z]:[\\/](?:Users|work)[\\/]", content), path
            parser = Links()
            parser.feed(content)
            parser_cache[path.resolve()] = parser
    for path, parser in list(parser_cache.items()):
        for link in parser.links:
            url = urlsplit(link)
            if url.scheme or url.netloc or link.startswith("/"):
                continue
            target = (path.parent / unquote(url.path)).resolve() if url.path else path
            if not target.suffix:
                target /= "index.html"
            # Astro owns the hub; check_site.py verifies its emitted URL in dist.
            if target == ROOT / "index.html" and not target.exists():
                target = ROOT / "src/pages/index.astro"
            assert target.is_file(), f"Broken link: {path.relative_to(ROOT)} -> {link}"
            if url.fragment and target.suffix == ".html":
                if target not in parser_cache:
                    target_parser = Links()
                    target_parser.feed(target.read_text(encoding="utf-8"))
                    parser_cache[target] = target_parser
                assert unquote(url.fragment) in parser_cache[target].ids, f"Broken anchor: {path.relative_to(ROOT)} -> {link}"
            checked_links += 1
    print(f"Verified: 15 UVM source files, 11 UVM classes, {len(GUIDES)} SVIP guides, {len(EXAMPLES)} SVIP examples, {checked_links} local HTML links.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="validate the existing package")
    parser.add_argument("--uvm-source", type=Path, help="local checkout of TechYan/uvm_wiki")
    parser.add_argument("--svip-source", type=Path, help="authorized local checkout of TechYan/svip")
    args = parser.parse_args()
    if not args.check:
        if not args.uvm_source or not args.svip_source:
            parser.error("provide --uvm-source and --svip-source, or use --check")
        uvm = build_uvm(args.uvm_source.resolve())
        svip = build_svip(args.svip_source.resolve())
        print(json.dumps({"uvm_wiki": uvm["stats"], "svip_guides": svip["guide_count"], "svip_examples": svip["example_count"]}, ensure_ascii=False))
    check()

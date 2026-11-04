# UVM Wiki portable demo

Open [the package index](index.html) or [the unified interactive wiki](uvm_wiki.html).

The genuine generated application includes Architecture, Topology, Class Hierarchy, TLM Connections, Phase Map, Wiki Graph, and Code Explorer. Its JSON data and D3 are embedded; it requires no server or CDN. [The full fixture](sources.html) is also bundled as readable and downloadable source.

## Source and generation

- Source: https://github.com/TechYan/uvm_wiki
- Revision: `82134333fab2a7a493cd5b13eac5709824c35202`
- Fixture: upstream `examples/demo_uvm`, copied without source changes.
- Generator: upstream `uvm-wiki/scripts/uvm_wiki_core.py`, `uvm_wiki_filelist.py`, and `uvm_wiki_web.py`.
- Effective parser: `pyslang`; 0 fallback files.
- Input: `examples/demo_uvm/filelist.f`, including nested RTL filelist and local include closure.
- Result: 15 HDL files, 11 classes, 56 relations, 2 TLM ports, 3 connections.
- Publication changes: relative metadata paths, no cache path, one link back to this package, a static source browser, provenance hashes, forced embedded-source mode on static HTTP hosting, and Wiki Graph initially set to All relations.

Use `python scripts/build_uvm_svip.py --uvm-source <local-uvm-wiki-checkout> --svip-source <local-svip-checkout>` from the demo checkout to reproduce this package. It uses the upstream generator directly; no wheels or parser runtime are copied into the published demo. Use `--check` to verify the generated package.

## Exact limits

This is a static per-file syntax index, not simulator elaboration. Runtime factory overrides, dynamic instances, and exact DUT/BFM binding are unresolved. The UVM library and its `uvm_macros.svh` are not bundled; the generator intentionally excludes that standard external library include from unresolved project include warnings. There are 0 unresolved project includes and 49 per-file syntax diagnostics. The index is not a compilation report and absent library macros can affect per-file syntax diagnostics.

Source previews use embedded context (120 lines before and after a location, sufficient for each small fixture file). This publication forces embedded-source mode even when hosted over HTTP/HTTPS, because a static host has no upstream source API. Full-text source search requires generating/using upstream serve-mode output. Every complete fixture source is available separately in `sources.html` and `examples/demo_uvm/`.

Wiki Graph opens on All relations (11 local class nodes and 20 edges). Its Inheritance projection includes only source-backed class-to-class edges; this fixture's classes all extend external UVM bases, so that projection is empty. Class Hierarchy explicitly includes the external UVM inheritance bases and is the appropriate view for them.

No simulation, coverage run, or passing DUT result was produced for this static publication. [provenance.json](provenance.json) records the input revision and SHA-256 for each copied source. D3 attribution and its license are retained in the embedded library and [D3-LICENSE.txt](D3-LICENSE.txt).

# SVIP documentation and source example demo

Open [the complete guide index](index.html), [reusable examples](examples.html), or [the source browser](sources.html).

## Source and scope

- Source repository: `TechYan/svip`; its visibility remains private.
- Source revision: `b3347d005d05ef3dd88b8c45f1588540062e9f40`.
- Author: syan.
- Owner-authorized public scope: complete user-facing documentation and reusable own source examples.
- Included: all 5 user guides, all 5 architecture pages, AXI4 protocol checks, APB usage cookbook, Control recipes; 17 original SystemVerilog example files.
- Excluded: full VIP runtime, commercial checker source, internal DUT or site integration source, credentials, historical round-verification pages/logs, and compliance/private-run catalogs.

Guide contents are preserved from the source revision. Publication edits add a scope banner, rewrite local navigation, and replace Markdown navigation labels with HTML labels. All 13 guides are self-contained HTML. Selected-document Markdown references resolve to their HTML page; reusable examples resolve to the local source browser. References to unbundled runtime, verification records, or checker integration resolve to [explicit scope notes](scope.html), not private URLs.

Original example source and SPDX/author comments are preserved. Some protocol sequences use base classes and peer fixtures from the full runtime; only the reusable examples are bundled. The Control quickstart is a small example receiver, not an internal DUT. The [source browser](sources.html) describes these execution dependencies.

## Rebuild and verification

With local source checkouts, run `python scripts/build_uvm_svip.py --uvm-source <uvm-wiki-checkout> --svip-source <svip-checkout>` from the demo checkout. Then run `python scripts/build_uvm_svip.py --check` to validate the static package links and UVM artifact invariants.

[provenance.json](provenance.json) records the exact revision and SHA-256 for each original guide and copied example. The published guide files differ only by the documented link/banner changes. No credentials are used or stored by the builder; fetch source checkouts separately through an authorized Git client.

No simulator, coverage run, tracker capture, or DUT acceptance run was executed for this publication. Source documentation's support and acceptance statements are not new simulation evidence. No synthetic passing tracker or coverage output is provided.

# Programming Guide Generator demo package

[Open the generator](index.html) · [Project overview](../projects/pg_gen/) · [Project hub](../)

Click **Load Sample** for a complete, fictional controller/sensor example: two register blocks, four registers, nine fields, two block windows, and one bus window. The sample flow contains **read**, **write**, **rmw**, and **poll** steps. Names, paths, addresses, and values were authored for this public demonstration and do not describe a product.

1. Click **Load Sample**, select a register, and edit a field or step.
2. Inspect the address formula: bus-window offset + block-window offset + local register offset. The example uses `0x40001000` and `0x40002000` as its fictional block bases.
3. Compare **Guide**, **PG JSON**, **YAML**, **CSV**, and **SV** previews; choose **Download** to export.
4. Use **Save Config** to keep editable inputs and steps; reload that file with **Load Config**.

| File | Purpose |
| --- | --- |
| [samples/demo_control_rdf.json](samples/demo_control_rdf.json) | Load with **Add RDF Blocks**. |
| [samples/demo_sensor_rdf.json](samples/demo_sensor_rdf.json) | Load with **Add RDF Blocks**. |
| [samples/demo_addr_map.json](samples/demo_addr_map.json) | Load with **Add Addr Maps**. |
| [samples/demo_bus_map.json](samples/demo_bus_map.json) | Load with **Add RNOC Maps**. |
| [samples/demo_inputs.json](samples/demo_inputs.json) | Combined reference bundle matching the built-in sample; use individual files for import. |
| [examples/demo_init.config.json](examples/demo_init.config.json) | Editable four-step example, including only the fictional inputs; open with **Load Config**. |
| [examples/demo_init.pg.json](examples/demo_init.pg.json) | Generated PG JSON with register addresses and source metadata. |
| [examples/demo_init.csv](examples/demo_init.csv) | Generated table with one row per step. |
| [examples/demo_init.sv](examples/demo_init.sv) | Generated SystemVerilog read/write/poll snippet. |

Open `index.html` directly in a modern browser, or host the folder as static files. It includes its JavaScript and CSS and makes no network requests. Import and generation operate in browser memory. Downloads use the browser save dialog when available and the normal download mechanism otherwise.

This is an editor and code-generation aid. The SV output is a snippet: the integrating testbench must define its register macros, `regval`, and `read_reg`/`write_reg` access tasks. No simulator run or hardware execution is included.

The standalone HTML was adapted from the user-authorized private `TechYan/pg_gen` repository at the commit recorded in [provenance.json](provenance.json). The public package contains the sanitized page and newly authored fictional data only. Project-specific mapping preferences, original register/address datasets, and obsolete external JS/CSS were excluded. The `company_rdf_json` schema label is retained for export compatibility; it does not imply the included data is a company register map.

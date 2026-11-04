"""Build the xpggen/xDCT public demo evidence from pinned source checkouts.

No parser or Python runtime is shipped to the browser. Run --check without sources.
"""
from __future__ import annotations

import argparse
import asyncio
import csv
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import runpy
import shutil
import subprocess
import sys
from html.parser import HTMLParser
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
PINS = {
    "xpggen": "42417d36867bdbc05992e09a72e5f500540291a4",
    "xDCT": "c19ed688797dabf46e8794bd63ae4385981b5785",
}
FLOW = "demo.register-bringup"
DESCRIPTION = "Synthetic RNOC example: configure fields, check them, poll ready, then delay."
FRAMES = [
    ("home", "01 · Load", "载入 288 个合成寄存器，选择 Register 或 PGGen。"),
    ("search", "02 · Search", "在真实 Register 视图中查询 PCIE，查看寄存器和字段描述。"),
    ("pg-csv", "03 · Compose", "把六种操作放入真实 PGGen 步骤表，查看 CSV 预览。"),
    ("pg-json", "04 · JSON", "同一份流程的 xpggen.pg.v2 JSON，保留语义字段赋值。"),
    ("pg-sv", "05 · SystemVerilog", "同一份流程的 SystemVerilog 预览，包含掩码比较与轮询。"),
]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def copy_file(source: Path, relative: str, target: Path, destination: str | None = None) -> dict:
    destination = destination or relative
    output = target / destination
    output.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source / relative, output)
    return {"source_path": relative, "public_path": destination, "sha256": sha(output)}


def check_source(path: Path, name: str) -> None:
    actual = subprocess.check_output(["git", "-C", str(path), "rev-parse", "HEAD"], text=True).strip()
    assert actual == PINS[name], f"{name}: expected {PINS[name]}, got {actual}"


def steps_from_source(source: Path):
    sys.path.insert(0, str(source / "src"))
    from xpggen.models import FieldAssignment
    from xpggen.pg import make_step
    from xpggen.rnoc import load_rnoc

    catalog = load_rnoc(source / "examples/rnoc.sample.json")
    registers = {register.name: register for register in catalog.registers}
    control = registers["REG__XPG__PCIE__CTRL_000"]
    config = registers["REG__XPG__PCIE__CFG_004"]
    status = registers["REG__XPG__PCIE__STATUS_001"]
    fields = {field.name: field for field in config.fields}
    assignments = (FieldAssignment(fields["mode"], "0x3"), FieldAssignment(fields["threshold"], "0x20"))
    ready = next(field for field in status.fields if field.name == "ready")
    steps = [
        make_step("read", control, comment="Read the initial control value without comparing."),
        make_step("write", control, value="0x1", comment="Write the complete control register."),
        make_step("rmw", config, assignments=assignments, comment="Set mode and threshold in one read-modify-write."),
        make_step("read_check", config, assignments=assignments, comment="Compare only the two configured fields."),
        make_step("poll", status, field=ready, value="0x1", timeout_us=1000, interval_us=10,
                  comment="Poll ready with a 1000 us timeout and a 10 us interval."),
        make_step("delay", delay_us=25, comment="Wait 25 microseconds."),
    ]
    return catalog, steps


async def capture_tui(source: Path, target: Path, steps) -> None:
    from unittest.mock import patch
    from textual.widgets import Input
    from xpggen.tui import Logo, XpgGenApp

    previous = Path.cwd()
    os.chdir(source)
    try:
        # Select the intended terminal color capability, rather than the harness's NO_COLOR=1.
        with patch.dict(os.environ, {"TERM": "xterm-256color", "COLORTERM": "truecolor"}):
            os.environ.pop("NO_COLOR", None)
            app = XpgGenApp(initial_path="examples/rnoc.sample.json")
            app._discover_json_candidates = lambda: [Path("examples/rnoc.sample.json")]
            # Freeze decoration; retain the real app, widgets, text and layout.
            with patch.object(Logo, "_advance", lambda self: None):
                async with app.run_test(size=(180, 52)) as pilot:
                    app.query_one("HeaderClock").display = False
                    for widget in app.query(Input):
                        widget.cursor_blink = False
                    app.set_focus(None)
                    await pilot.wait_for_scheduled_animations()
                    assert app.catalog and app.catalog.register_count == 288

                    def save(name: str) -> None:
                        content = app.export_screenshot(title="xpggen · synthetic RNOC demo")
                        # Rich IDs hash internal segment metadata; normalize identifiers only.
                        content = re.sub(r"terminal-\d+", f"xpggen-{name}", content)
                        (target / "captures" / f"{name}.svg").write_text(content, encoding="utf-8")

                    (target / "captures").mkdir(exist_ok=True)
                    save("home")
                    await pilot.press("f2")
                    app.query_one("#reg-search", Input).value = "PCIE"
                    await pilot.pause(0.3)
                    await pilot.wait_for_scheduled_animations()
                    save("search")
                    await pilot.press("f3")
                    app.query_one("#flow-id", Input).value = FLOW
                    app.steps = steps
                    app._render_steps()
                    app._render_pg_preview()
                    await pilot.wait_for_scheduled_animations()
                    save("pg-csv")
                    for tab in ("json", "sv"):
                        await pilot.click(f"#tab-{tab}")
                        await pilot.wait_for_scheduled_animations()
                        save(f"pg-{tab}")
    finally:
        os.chdir(previous)


def build_xpggen(source: Path, capture: bool) -> None:
    from importlib.metadata import version
    check_source(source, "xpggen")
    target = ROOT / "xpggen"
    target.mkdir(exist_ok=True)
    evidence = [copy_file(source, relative, target) for relative in [
        "examples/rnoc.sample.json", "scripts/make_demo_rnoc.py", "LICENSE",
        *[f"previews/{path.name}" for path in sorted((source / "previews").glob("*.svg"))],
    ]]
    catalog, steps = steps_from_source(source)
    from xpggen.pg import render_csv_preview, render_markdown_guide, render_pg_json, render_systemverilog_preview
    exports = {
        "json": render_pg_json(FLOW, DESCRIPTION, "examples/rnoc.sample.json", steps) + "\n",
        "csv": render_csv_preview(steps),
        "sv": render_systemverilog_preview(FLOW, steps) + "\n",
        "md": render_markdown_guide(FLOW, DESCRIPTION, "examples/rnoc.sample.json", steps) + "\n",
    }
    (target / "examples").mkdir(exist_ok=True)
    for extension, content in exports.items():
        name = "bringup.pg.json" if extension == "json" else f"bringup.{extension}"
        (target / "examples" / name).write_text(content, encoding="utf-8")
    generated_catalog = runpy.run_path(str(source / "scripts/make_demo_rnoc.py"))["build_registers"]()
    assert generated_catalog == json.loads((target / "examples/rnoc.sample.json").read_text(encoding="utf-8"))
    if capture:
        asyncio.run(capture_tui(source, target, steps))
    data = {
        "source_commit": PINS["xpggen"], "register_count": catalog.register_count,
        "field_count": catalog.field_count, "flow": json.loads(exports["json"]), "exports": exports,
        "frames": [{"id": name, "title": title, "caption": caption, "src": f"captures/{name}.svg"}
                   for name, title, caption in FRAMES],
    }
    (target / "data.js").write_text("window.XPGGEN_DEMO = " + json.dumps(data, ensure_ascii=False) + ";\n", encoding="utf-8")
    provenance = {
        "project": "xpggen", "source_repository": "https://github.com/TechYan/xpggen",
        "source_commit": PINS["xpggen"], "source_visibility": "private at capture time",
        "scope": "Synthetic bundled catalog, original previews, real headless Textual captures and source exporter outputs.",
        "copied_evidence": evidence,
        "exporter_paths": ["src/xpggen/pg.py", "src/xpggen/models.py", "src/xpggen/rnoc.py"],
        "exporter_sha256": {path: sha(source / path) for path in ["src/xpggen/pg.py", "src/xpggen/models.py", "src/xpggen/rnoc.py"]},
        "generation": {"flow_id": FLOW, "format": "xpggen.pg.v2", "source": "examples/rnoc.sample.json",
                       "ops": [step.op for step in steps], "steps": 6,
                       "api": "make_step; render_pg_json; render_csv_preview; render_systemverilog_preview; render_markdown_guide"},
        "capture": {"method": "Actual XpgGenApp.run_test and App.export_screenshot", "terminal_cells": [180, 52],
                    "textual": version("textual"), "rich": version("rich"),
                    "normalization": "Truecolor terminal environment; HeaderClock hidden; input cursor blinking disabled; logo animation held at phase 0; finite animations awaited; nonvisual SVG identifiers normalized. No screenshot text or geometry edited.",
                    "setup": "Load bundled sample; F2 and PCIE search; F3; seed exported six-step model; select real preview tabs.",
                    "frames": [{"path": f"captures/{name}.svg", "sha256": sha(target / f"captures/{name}.svg")} for name, _, _ in FRAMES]},
        "limitations": ["Screenshot gallery, not a live browser TUI or timed terminal recording.",
                        "Sample contains register offsets only; no final hardware addresses or real DUT data.",
                        "SV is the original exporter preview and requires project register macros, regval, read_reg/write_reg and a suitable time unit.",
                        "Original Rich SVGs reference optional CDN fonts; local monospace fallback works offline."],
    }
    write_json(target / "provenance.json", provenance)


def build_xdct(source: Path) -> None:
    check_source(source, "xDCT")
    target = ROOT / "xDCT"
    target.mkdir(exist_ok=True)
    paths = ["examples/top_v1.sv", "examples/top_v2.sv", "demo/baseline_cl123450.json",
             "demo/current_cl123456.json", "demo/diff_cl123450_to_cl123456.json", "demo/report_cl123450_to_cl123456.txt"]
    evidence = [copy_file(source, path, target) for path in paths]
    baseline, current, diff = [json.loads((target / path).read_text(encoding="utf-8")) for path in paths[2:5]]
    report = (target / paths[5]).read_text(encoding="utf-8")
    # Verify the shipped evidence with the real prototype; its pyslang binary stays in the private checkout.
    spec = importlib.util.spec_from_file_location("xdct_topif", source / "topif.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.extract_manifest([source / paths[0]], "chip_top", "123450", [], []) == baseline
    assert module.extract_manifest([source / paths[1]], "chip_top", "123456", [], []) == current
    assert module.compare_manifests(baseline, current) == diff
    assert module.render_report(diff) == report
    data = {"baseline": baseline, "current": current, "diff": diff, "report": report,
            "sources": {"before": (target / paths[0]).read_text(encoding="utf-8"),
                        "after": (target / paths[1]).read_text(encoding="utf-8")}}
    (target / "data.js").write_text("window.XDCT_DEMO = " + json.dumps(data, ensure_ascii=False) + ";\n", encoding="utf-8")
    write_json(target / "provenance.json", {
        "project": "xDCT", "version": "v0.1.0-prototype", "source_repository": "https://github.com/TechYan/xDCT",
        "source_commit": PINS["xDCT"], "source_visibility": "private at capture time", "copied_evidence": evidence,
        "scope": "Browser comparison of the repository's existing synthetic chip_top demo; no SystemVerilog parsing in the browser.",
        "verification": {"implementation": "topif.py", "sha256": sha(source / "topif.py"), "pyslang": module.pyslang.__version__,
                         "result": "Both manifests re-extracted and compared against shipped evidence; diff and report reproduced exactly."},
        "summary": {"old_ports": 9, "new_ports": 9, "changed_names": 10, "breaking": 6, "added": 1, "removed": 1, "modified": 5, "order_only": 3},
        "limitations": ["Prototype scope: ANSI-style top ports and interface/modport ports.",
                        "Classifications and breaking flags are the existing prototype's policy, including nonbreaking ADDED and ORDER_ONLY.",
                        "Production baseline update policy, project configuration and stronger diagnostics are outside this demo.",
                        "No pyslang binary or third-party runtime is published."],
    })


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.urls = []

    def handle_starttag(self, tag, attrs):
        for name, value in attrs:
            if name in {"href", "src"} and value:
                self.urls.append(value)


def self_check() -> None:
    xpg = ROOT / "xpggen"
    xdct = ROOT / "xDCT"
    catalog = json.loads((xpg / "examples/rnoc.sample.json").read_text(encoding="utf-8"))
    assert len(catalog) == 288 and sum(len(r["fields"]) for r in catalog) == 1296
    pg = json.loads((xpg / "examples/bringup.pg.json").read_text(encoding="utf-8"))
    assert pg["format"] == "xpggen.pg.v2" and len(pg["steps"]) == 6
    assert {step["op"] for step in pg["steps"]} == {"read", "read_check", "write", "rmw", "poll", "delay"}
    rmw = next(step for step in pg["steps"] if step["op"] == "rmw")
    assert rmw["resolved"] == {"mask": "0x0000FFF0", "value": "0x00002030"}
    assert len(rmw["assignments"]) == 2 and all(not field["force_access"] for field in rmw["assignments"])
    assert next(step for step in pg["steps"] if step["op"] == "delay")["delay_us"] == 25
    poll = next(step for step in pg["steps"] if step["op"] == "poll")
    assert poll["timeout_us"] == 1000 and poll["interval_us"] == 10
    rows = list(csv.DictReader(io.StringIO((xpg / "examples/bringup.csv").read_text(encoding="utf-8"))))
    assert [row["op"] for row in rows] == [step["op"] for step in pg["steps"]]
    sv = (xpg / "examples/bringup.sv").read_text(encoding="utf-8")
    assert all(token in sv for token in ["regval = (regval & ~32'hFFF0) | 32'h2030;", "!==", "===", "poll_elapsed_us <= 1000", "#(10 * 1us);", "#(25 * 1us);"])
    assert all(f"| {i} | {step['op']} |" in (xpg / "examples/bringup.md").read_text(encoding="utf-8") for i, step in enumerate(pg["steps"], 1))
    def browser_data(path: Path, variable: str) -> dict:
        content = path.read_text(encoding="utf-8")
        prefix = f"window.{variable} = "
        assert content.startswith(prefix) and content.endswith(";\n")
        return json.loads(content[len(prefix):-2])

    xpg_data = browser_data(xpg / "data.js", "XPGGEN_DEMO")
    assert xpg_data["flow"] == pg and xpg_data["register_count"] == 288 and xpg_data["field_count"] == 1296
    for extension, filename in {"json": "bringup.pg.json", "csv": "bringup.csv", "sv": "bringup.sv", "md": "bringup.md"}.items():
        assert xpg_data["exports"][extension] == (xpg / "examples" / filename).read_text(encoding="utf-8")
    assert [frame["id"] for frame in xpg_data["frames"]] == [name for name, _, _ in FRAMES]
    assert all((xpg / frame["src"]).is_file() for frame in xpg_data["frames"])
    for name, _, _ in FRAMES:
        svg = (xpg / f"captures/{name}.svg").read_text(encoding="utf-8")
        assert "<svg" in svg and "Generated with Rich" in svg and "xpggen" in svg
        assert "D:\\work" not in svg and "C:\\Users" not in svg
    baseline = json.loads((xdct / "demo/baseline_cl123450.json").read_text(encoding="utf-8"))
    current = json.loads((xdct / "demo/current_cl123456.json").read_text(encoding="utf-8"))
    diff = json.loads((xdct / "demo/diff_cl123450_to_cl123456.json").read_text(encoding="utf-8"))
    assert len(baseline["ports"]) == len(current["ports"]) == 9
    assert len(diff["changes"]) == 10 and sum(change["breaking"] for change in diff["changes"]) == 6
    assert sum(change["categories"] == ["ORDER_ONLY"] for change in diff["changes"]) == 3
    before = {port["name"]: port for port in baseline["ports"]}
    after = {port["name"]: port for port in current["ports"]}
    for change in diff["changes"]:
        assert change["old"] == before.get(change["name"])
        assert change["new"] == after.get(change["name"])
    xdct_data = browser_data(xdct / "data.js", "XDCT_DEMO")
    assert xdct_data["baseline"] == baseline and xdct_data["current"] == current and xdct_data["diff"] == diff
    assert xdct_data["report"] == (xdct / "demo/report_cl123450_to_cl123456.txt").read_text(encoding="utf-8")
    for key, filename in {"before": "top_v1.sv", "after": "top_v2.sv"}.items():
        assert xdct_data["sources"][key] == (xdct / "examples" / filename).read_text(encoding="utf-8")
    checked_links = 0
    for directory in (xpg, xdct):
        provenance = json.loads((directory / "provenance.json").read_text(encoding="utf-8"))
        assert provenance["source_commit"] == PINS[directory.name]
        for evidence in provenance["copied_evidence"]:
            assert sha(directory / evidence["public_path"]) == evidence["sha256"]
        for capture in provenance.get("capture", {}).get("frames", []):
            assert sha(directory / capture["path"]) == capture["sha256"]
        for page in directory.glob("*.html"):
            parser = Links()
            parser.feed(page.read_text(encoding="utf-8"))
            for url in parser.urls:
                parts = urlsplit(url)
                if not parts.scheme and parts.path:
                    assert not parts.path.startswith("/"), f"Use relative URLs: {url}"
                    target = (page.parent / unquote(parts.path)).resolve()
                    # Astro owns the hub; check_site.py verifies its emitted URL in dist.
                    if target == ROOT / "index.html" and not target.exists():
                        target = ROOT / "src/pages/index.astro"
                    assert target.exists(), f"Broken link: {page}: {url}"
                    checked_links += 1
    print(f"PASS: 288 registers / 1296 fields; 6 PG operations / 4 authentic exports / 5 real captures; 9-to-9 ports / 10 changes / 6 breaking / 3 order-only; browser data equality; evidence SHA-256; {checked_links} HTML links.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--xpggen-source", type=Path, default=ROOT.parent / ".tmp/xpggen-source")
    parser.add_argument("--xdct-source", type=Path, default=ROOT.parent / ".tmp/xdct-source")
    parser.add_argument("--capture", action="store_true", help="Regenerate real Textual screenshots (requires Rich/Textual).")
    parser.add_argument("--check", action="store_true", help="Check committed artifacts without private sources or dependencies.")
    args = parser.parse_args()
    if not args.check:
        build_xpggen(args.xpggen_source.resolve(), args.capture)
        build_xdct(args.xdct_source.resolve())
    self_check()


if __name__ == "__main__":
    main()

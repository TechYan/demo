"""Prepare the curated, synthetic wavedbg native example for static publication.

This copies an existing completed run; it never runs the analyzer or simulator.
Only local path metadata and host file fingerprints are removed. Numerical
results, event records, HTML application code and comparison results are kept.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import zipfile


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-directory", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("wavedbg/performance"))
    args = parser.parse_args()
    destination = args.output / "data"
    destination.mkdir(parents=True, exist_ok=True)
    files = {}
    for subdir, source_dir, names in (
        ("native", "wave-report-02", ["report.html", "report.json", "tracker.log", "analyze.log", "capture.csv", "evidence.json", "mapping.json"]),
        ("probe", "probe-report-02", ["report.html", "report.json", "tracker.log", "analyze.log"]),
    ):
        target = destination / subdir
        target.mkdir(parents=True, exist_ok=True)
        for name in names:
            source = args.run_directory / source_dir / name
            original = source.read_bytes()
            content = original.decode("utf-8")
            # The run belongs entirely to our synthetic fixture. Replace its
            # task-specific path with a clearly synthetic publication path.
            content = re.sub(r"/tmp/wavedbg-axi-20261107-01/wave-report-02/", "./", content)
            content = re.sub(r"/tmp/wavedbg-axi-20261107-01/probe-report-02/", "./", content)
            content = content.replace("/tmp/wavedbg-axi-20261107-01/", "/synthetic/native/")
            changes = ["Local task paths replaced with relative or /synthetic/native/ paths"] if content.encode() != original else []
            if name == "evidence.json":
                data = json.loads(content)
                identity = data["waveform_capture"]["file_identity"]
                size = identity["fingerprint"]["size_bytes"]
                identity.pop("fingerprint")
                identity["published_size_bytes"] = int(size)
                identity["publication_note"] = "Host-specific device/inode/mtime/fingerprint omitted; original evidence retained privately."
                content = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
                changes.append("Host-specific file fingerprint omitted")
            published = content.encode("utf-8")
            (target / name).write_bytes(published)
            files[f"{subdir}/{name}"] = {"source_sha256": digest(original), "published_sha256": digest(published), "bytes": len(published), "changes": changes}

    for source_name, public_name in [("native-verification-02.json", "comparison.json"), ("probe.csv", "probe/capture.csv")]:
        data = (args.run_directory / source_name).read_bytes()
        (destination / public_name).write_bytes(data)
        files[public_name] = {"source_sha256": digest(data), "published_sha256": digest(data), "bytes": len(data), "changes": []}

    provenance = {
        "schema": 1,
        "title": "wavedbg 0.3.0 / synthetic AXI4 native FSDB demonstration",
        "run_date": "2026-11-07",
        "source_kind": "Native FSDB from synthetic AXI stimulus, captured simultaneously by the original xpvkit SV probe",
        "wavedbg_version": "0.3.0",
        "xpvkit_version": "0.5.6",
        "xpvkit_commit": "453527455a9cb23ab24742858196d13ea21baf2d",
        "sample_count": 600,
        "capture_window_ps": [100, 60100],
        "protocol_pass": None,
        "notes": [
            "Existing completed run, not re-executed for this publication.",
            "Metrics, event records and analyzer HTML/JavaScript are unchanged.",
            "Capture-local seq starts at 1 for waveform capture and 2 for the original probe; comparison uses relative sequence.",
            "Raw CSV byte/absolute-seq equality is not claimed.",
            "FSDB, raw sample/query streams, original execution manifest, SDK, license and build logs are not included in this public subset.",
            "The published files have their own hashes. The original run manifest does not apply to sanitized copies.",
        ],
        "files": files,
    }
    (destination / "publication.json").write_text(json.dumps(provenance, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (destination / "README.txt").write_text(
        "wavedbg 0.3.0 / AXI4 native synthetic example\n\n"
        "Open native/report.html for the wavedbg-derived xpvkit report.\n"
        "Open probe/report.html for the simultaneous original SV probe reference.\n"
        "comparison.json records the existing 13 semantic comparisons.\n"
        "publication.json records source/published hashes and path-only sanitization.\n"
        "This is a synthetic demonstration, not a DUT performance benchmark or protocol signoff.\n"
        "Auto data window: [300,500) ps, 50 GB/s. Full capture: [100,60100) ps, 0.1666667 GB/s.\n",
        encoding="utf-8",
    )
    members = sorted(p for p in destination.rglob("*") if p.is_file() and p.name != "SHA256SUMS")
    (destination / "SHA256SUMS").write_text("".join(f"{digest(p.read_bytes())}  {p.relative_to(destination).as_posix()}\n" for p in members), encoding="utf-8")
    archive = args.output / "wavedbg-axi-native-demo.zip"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
        for path in sorted(destination.rglob("*")):
            if path.is_file():
                item = zipfile.ZipInfo(path.relative_to(destination).as_posix(), (2026, 11, 7, 0, 0, 0))
                item.compress_type = zipfile.ZIP_DEFLATED
                bundle.writestr(item, path.read_bytes())
    print(json.dumps({"files": len(files), "archive_bytes": archive.stat().st_size, "output": str(args.output)}))


if __name__ == "__main__":
    main()

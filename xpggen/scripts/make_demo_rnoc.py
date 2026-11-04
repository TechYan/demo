from __future__ import annotations

import json
from pathlib import Path


BLOCKS = [
    ("pcie", 0x20100000, "PCIe controller configuration"),
    ("phub", 0x20200000, "Protocol hub routing"),
    ("dma", 0x20300000, "DMA channel control"),
    ("msi", 0x20400000, "MSI interrupt delivery"),
    ("atu", 0x20500000, "Address translation unit"),
    ("debug", 0x20600000, "Debug and observability"),
]

REG_KINDS = [
    ("CTRL", "RW", "Control knobs for enabling datapath features"),
    ("STATUS", "RO", "Live status bits sampled from hardware"),
    ("MASK", "RW", "Interrupt and event mask settings"),
    ("COUNT", "RO", "Saturating event counter value"),
    ("CFG", "RW", "Programmable configuration fields"),
    ("ERR", "RW1C", "Sticky error indications cleared by writing one"),
    ("TIMEOUT", "RW", "Timeout threshold used by local watchdog logic"),
    ("CAP", "RO", "Capability and feature discovery register"),
]

FIELD_LIBRARY = [
    ("enable", 0, 0, 1, "0", "Enables this feature when set"),
    ("ready", 1, 1, 1, "0", "Indicates that the block completed initialization"),
    ("busy", 2, 2, 1, "0", "Shows that an internal transaction is active"),
    ("error", 3, 3, 1, "0", "Sticky error summary bit"),
    ("mode", 4, 7, 4, "0", "Selects the operating mode"),
    ("threshold", 8, 15, 8, "32", "Programmable threshold value"),
    ("target_id", 16, 23, 8, "0", "Destination or requester identifier"),
    ("version", 24, 31, 8, "1", "Encoded hardware revision"),
]


def build_registers() -> list[dict]:
    registers: list[dict] = []
    for block_index, (block, base, block_desc) in enumerate(BLOCKS):
        for index in range(48):
            kind, access, kind_desc = REG_KINDS[(index + block_index) % len(REG_KINDS)]
            offset = index * 4
            name = f"{block.upper()}_{kind}_{index:03d}"
            field_count = 3 + ((index + block_index) % 4)
            fields = {}
            for field_index in range(field_count):
                fname, low, high, width, reset, fdesc = FIELD_LIBRARY[(index + field_index + block_index) % len(FIELD_LIBRARY)]
                field_name = f"{fname}_{field_index}" if fname in fields else fname
                fields[field_name] = {
                    "bit_range": {
                        "low": low,
                        "high": high,
                        "shift": low,
                        "width": width,
                        "mask": ((1 << width) - 1) << low,
                    },
                    "reset": int(reset, 0),
                    "access": access,
                    "doc": [
                        f"{fdesc}; used by {block} register {index:03d}.",
                        f"This field is generated in the flat RNOC demo format for field-description display testing.",
                    ],
                }
            registers.append(
                {
                    "name": f"REG__XPG__{block.upper()}__{kind}_{index:03d}",
                    "offset": f"0x{offset:04X}",
                    "doc": f"{block_desc}: {kind_desc} ({index:03d}). Base demo address would be 0x{base + offset:08X}.",
                    "fields": fields,
                }
            )
    return registers


def main() -> None:
    output = Path(__file__).resolve().parents[1] / "examples" / "rnoc.sample.json"
    data = build_registers()
    output.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {len(data)} registers to {output}")


if __name__ == "__main__":
    main()

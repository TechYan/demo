#!/usr/bin/env python3
"""Build or check the public, synthetic wavedbg guided replay (stdlib only).

Check the shipped data: python scripts/build_wavedbg_examples.py --check
Rebuild with the pinned source: python scripts/build_wavedbg_examples.py --source PATH
No native engine, simulator, SDK, FSDB or KDB is opened by this script.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

SITE = Path(__file__).resolve().parents[1]
OUT = SITE / "wavedbg"
REVISION = "9bf7b333dce94c73f64877bd7e676524b35b033e"
REPOSITORY = "TechYan/wavedbg"
SOURCE = {"repository": REPOSITORY, "revision": REVISION, "version": "0.2.1"}
FIXTURE = "src/wavedbg/engines/wave/_native/tests/fixtures/sv/progressive_wave.sv"
FAKE = "src/wavedbg/engines/wave/fake_backend.py"
SKILL_ROOT = "src/wavedbg/skills"
SKILLS = ["wavedbg", "wavedbg-axi", "wavedbg-apb", "wavedbg-ahb", "wavedbg-clock-reset", "wavedbg-fifo", "wavedbg-credit"]
SOURCE_PATHS = [
    "README.md", "pyproject.toml", "docs/architecture.md", "docs/compatibility.md",
    "docs/skills-review.md", "docs/pdf/build_documents.py", "docs/pdf/evidence/synthetic-results.json", FAKE, FIXTURE,
    "src/wavedbg/skill_catalog.py", "src/wavedbg/engines/wave/wave_overview.py",
    "src/wavedbg/engines/wave/overview_summary.py", "src/wavedbg/engines/wave/semantic.py",
    "src/wavedbg/engines/wave/discovery_index.py",
    *[f"{SKILL_ROOT}/{name}/SKILL.md" for name in SKILLS],
    *[f"{SKILL_ROOT}/wavedbg/references/{name}.md" for name in ["xwave", "xtrace", "sampling", "joint-debug", "x-propagation", "tool-reference", "session-management"]],
]


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ref(path, description):
    return {"path": path, "description": description}


def signal(name, label, width, role, events):
    return {"id": name, "label": label, "width": width, "role": role, "events": events}


def step(title, summary, evidence, window, signals):
    return {"title": title, "summary": summary, "evidence": evidence, "window": window, "signals": signals}


def bits(value):
    width = value["width"]
    data, x, z = [int(value[key], 16) for key in ("data_hex", "x_mask_hex", "z_mask_hex")]
    return "".join("x" if x & (1 << n) else "z" if z & (1 << n) else str((data >> n) & 1) for n in reversed(range(width)))


def capture_fake(source):
    """Call the original Python FakeBackend; preserve result payloads unchanged."""
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(source / "src"))
    OUT.mkdir(parents=True, exist_ok=True)
    # Keep cache paths short on Windows and inside the permitted output tree.
    with tempfile.TemporaryDirectory(prefix=".query-", dir=OUT) as scratch:
        assert Path(scratch).resolve().is_relative_to(OUT.resolve())
        old_cache = os.environ.get("XWAVE_CACHE_HOME")
        os.environ["XWAVE_CACHE_HOME"] = str(Path(scratch) / "cache")
        module = importlib.import_module("wavedbg.engines.wave.fake_backend")
        original_root = module.fake_semantic_cache_root
        module.fake_semantic_cache_root = lambda: Path(scratch) / "semantic"
        try:
            backend = module.FakeBackend()
            records = []

            def query(label, action, params):
                result = copy.deepcopy(dict(backend.invoke(action, params)))
                records.append({"id": label, "action": action, "params": params, "result": result})
                return result

            opened = query("open", "session.open", {"fsdb_path": "/fixtures/xwave/basic.fsdb"})
            sid = opened["session_id"]
            query("info", "fsdb.info", {"session_id": sid})
            paths = ["tb.clk", "tb.rst_n", "tb.dut.valid", "tb.dut.ready", "tb.dut.data"]
            for path in paths:
                query("raw:" + path, "signal.changes", {"session_id": sid, "signal": {"path": path}, "begin": {"tick": "0"}, "end": {"tick": "40"}, "event_view": "raw", "limit": 100})
            query("points", "value.at", {"session_id": sid, "signals": [{"alias": path.rsplit(".", 1)[-1], "ref": {"path": path}} for path in paths], "times": [{"tick": str(t)} for t in [12, 14, 15, 19, 20, 24, 25, 30, 35]]})
            tracks = [{"name": name, "signal": {"path": "tb.dut." + name}} for name in ["valid", "ready", "data"]]
            overview = {"session_id": sid, "begin": {"tick": "0"}, "end": {"tick": "40"}, "tracks": tracks, "bucket_counts": [8], "focus_limit": 6}
            query("overview", "wave.overview", overview)
            query("overview-repeat", "wave.overview", overview)
            query("overview-focus", "wave.overview", {**overview, "begin": {"tick": "15"}, "end": {"tick": "25"}})
            query("close", "session.close", {"session_id": sid})
        finally:
            module.fake_semantic_cache_root = original_root
            if old_cache is None:
                os.environ.pop("XWAVE_CACHE_HOME", None)
            else:
                os.environ["XWAVE_CACHE_HOME"] = old_cache
    return {"schema_version": 1, "source": SOURCE, "kind": "original-python-fake-backend-query-export", "native_execution": False, "note": "Original FakeBackend.invoke responses, not MCP/native results. The /fixtures path is the built-in synthetic identity; no waveform file is read. Tick = 1 ps. IDs and completeness are preserved.", "records": records}


def fake_signals(export):
    labels = {"clk": ("clk", "时钟"), "rst_n": ("rst_n", "低有效复位"), "valid": ("valid", "发送意愿"), "ready": ("ready", "接收能力"), "data": ("data[7:0]", "数据，保留 X/Z")}
    result = []
    for record in export["records"]:
        if not record["id"].startswith("raw:"):
            continue
        response = record["result"]
        name = response["signal"]["name"]
        label, role = labels[name]
        events = [[int(row["time"]["tick"]) / 1000, bits(row["value"])] for row in response["changes"]]
        result.append(signal(name, label, response["signal"]["width"], role, events))
    return result


def progressive_signals(text):
    """Evaluate the fixture's simple explicit #delay/assignment schedules only.

    This is a stimulus reconstruction, not a simulator or an FSDB reader.
    Same-tick glitch and dump-off coverage signals are deliberately excluded.
    """
    assert "`timescale 1ps/1ps" in text
    assert "bus = 64'h8000_0000_0000_0000" in text
    histories = {"clk": [[0, "0"]], "valid": [[0, "0"]], "ready": [[0, "1"]], "narrow": [[0, "0"]], "initial_x": [[0, "x"]], "bus": [[0, "00000000"]]}
    fork = re.search(r"\bfork\s+(.*?)\bjoin\b", text, re.S).group(1)
    token = re.compile(r"#(?P<delay>\d+)|\b(?P<scalar>clk|valid|ready|narrow|initial_x)\s*=\s*(?P<value>1'b[xz]|[01])\s*;|bus\[(?P<bit>\d+)\]\s*=\s*(?P<bitvalue>1'b[xz]|[01])\s*;")
    for branch in re.findall(r"\bbegin\b(.*?)\bend\b", fork, re.S):
        time_ps = 0
        bus = list(histories["bus"][0][1])
        for match in token.finditer(branch):
            if match["delay"] is not None:
                time_ps += int(match["delay"])
            elif match["scalar"]:
                histories[match["scalar"]].append([time_ps / 1000, match["value"].removeprefix("1'b")])
            else:
                bit = int(match["bit"])
                assert bit < 8
                bus[7 - bit] = match["bitvalue"].removeprefix("1'b")
                value = "".join(bus)
                if histories["bus"][-1][0] == time_ps / 1000:
                    histories["bus"][-1][1] = value
                else:
                    histories["bus"].append([time_ps / 1000, value])
    labels = {"clk": ("clk", "激励时钟"), "valid": ("valid", "请求脉冲"), "ready": ("ready", "持续允许"), "narrow": ("narrow", "1 ps 窄脉冲"), "initial_x": ("initial_x", "初始未知值"), "bus": ("bus[7:0]", "原 64 位总线的低 8 位")}
    return [signal(name, labels[name][0], 8 if name == "bus" else 1, labels[name][1], events) for name, events in histories.items()]


def credit_example():
    edges = [15, 25, 35, 45, 55, 65, 75, 85]
    offered = [1, 1, 0, 1, 1, 1, 1, 1]
    sends = [1, 1, 0, 1, 1, 0, 0, 1]
    frees = [0, 1, 1, 0, 0, 0, 1, 0]

    def input_events(values):
        events = [[0, "0"]]
        for edge, value in zip(edges, values):
            if str(value) != events[-1][1]:
                events.append([edge - 5, str(value)])
        return events

    credits, counter_events, rows = 2, [[0, "010"]], []
    for edge, offered_value, sent, returned in zip(edges, offered, sends, frees):
        before = credits
        assert sent <= before
        credits += returned - sent
        assert 0 <= credits <= 4
        if f"{credits:03b}" != counter_events[-1][1]:
            counter_events.append([edge + 0.2, f"{credits:03b}"])
        rows.append({"edge_ns": edge, "offered": offered_value, "send": sent, "free": returned, "credit_before": before, "credit_after": credits})
    contract = {"kind": "educational-synthesis", "based_on": f"{SKILL_ROOT}/wavedbg-credit/SKILL.md", "clock": "rising, period 10 ns", "observe": "inputs before edge; counter observed 0.2 ns after edge", "reset": "active low, known initial credit 2; released at 8 ns", "capacity": 4, "initial_credit": 2, "virtual_channels": 1, "send_free_encoding": "one asserted sample consumes/returns one unit", "returned_credit_usable": "next cycle", "accounting": "C_next = C_before + free - send", "native_execution": False, "rows": rows}
    traces = [signal("clk", "clk", 1, "10 ns 周期", [[t, str((t // 5) % 2)] for t in range(0, 91, 5)]), signal("rst_n", "rst_n", 1, "低有效复位", [[0, "0"], [8, "1"]]), signal("offered", "offered", 1, "上游有数据想发", input_events(offered)), signal("send", "send", 1, "本周期真正发出一份", input_events(sends)), signal("free", "free", 1, "本周期归还一份", input_events(frees)), signal("credit", "credit[2:0]", 3, "沿后更新的可用额度", counter_events)]
    return traces, contract


def build_cases(fake, progressive, credit):
    fake_ref = [ref("examples/fake-query-export.json", "本版本原始 Python FakeBackend 查询响应；1 ps/tick"), ref(FAKE, "五条内建合成信号的确定时间线")]
    return {"schema_version": 1, "mode": "guided-synthetic-replay", "source": SOURCE, "cases": [
        {"id": "ready-valid", "title": "VALID 已拉高，为什么还在等？", "protocol": "Ready / Valid", "question": "是没有发送请求，还是接收端暂时接不住？", "prompt": "请用 wavedbg 查看这段 ready/valid：先确认请求何时出现，再检查等待期间的 READY 和 DATA，给出时间证据，并说明是否足以确认一次时钟握手。", "summary": "把“没有数据可发”和“有数据但对方没准备好”分开，再用局部证据核对。", "span": [0, 0.04], "focus": [0.012, 0.027], "detail": [0.014, 0.021], "signals": fake, "evidence_kind": "original-fake-backend", "origin_label": "内建假后端的原始查询回放 · 时间单位 1 ps", "steps": [
            step("先看全貌", "先选时钟、复位和一条通道，观察请求出现的位置。", ["复位在 12 ps 释放。", "VALID 在 15 ps 变为 1，READY 此时仍为 0。"], [0, 0.04], ["clk", "rst_n", "valid", "ready"]),
            step("聚焦等待区间", "将视野收窄到请求附近，分辨等待与重叠。", ["15–20 ps：VALID=1 且 READY=0，等待持续 5 ps。", "20–25 ps：VALID 与 READY 的稳定值同时为 1。"], [0.012, 0.027], ["valid", "ready", "data"]),
            step("核对精确变化", "读原始变化和数据，防止把电平重叠直接当成协议通过。", ["DATA 在 15 ps 是 00010010，在 20 ps 变成 xxxx0010。", "VALID 在 15 ps 与时钟上升沿同一 tick 变化；25 ps 又与上升沿同 tick 拉低。", "这些记录没有仿真调度区域，不能据此给出无歧义的接受拍数。"], [0.014, 0.021], ["clk", "valid", "ready", "data"])
        ], "conclusion": "可以确认：发送意愿已出现，READY 低电平造成了 15–20 ps 的等待。20 ps 之后两者电平重叠，但 DATA 含 X，且边沿采样有同 tick 歧义；还不能宣布一次干净的协议传输。", "limitations": ["这是内建合成假后端，不是真实 DUT、FSDB 或 native 运行。", "展示电平与变化事实；接受拍数还需要时钟、复位、沿前/沿后及同 tick 采样契约。", "数据中保留 X/Z；这里只观察现象，没有证明 READY 或 X 的设计原因。"], "references": fake_ref + [ref(f"{SKILL_ROOT}/wavedbg-axi/SKILL.md", "单通道背压、接受条件与采样边界")]},
        {"id": "clock-stop", "title": "活动还在，时钟为什么停了？", "protocol": "Clock / Reset", "question": "先确认接收端真的没有沿，再讨论门控或复位。", "prompt": "请用 wavedbg 先查看 clk 的活动概览，再找最后一次上升/下降沿。指出能确认的时钟事实，以及还需哪些门控、复位或设计连接证据。", "summary": "从全局活动缩到最后几条边沿，把“没有观察到时钟”变成可核对的时间点。", "span": [0, 40], "focus": [19, 34], "detail": [23, 28], "signals": progressive, "evidence_kind": "source-fixture-reconstruction", "origin_label": "现有合成激励的时间线重建 · 未运行仿真或 native 查询", "steps": [
            step("先找活动范围", "少量轨道便能看到时钟活动集中在前半段。", ["这个教学激励声明了 5、15、24 ns 三次上升沿。", "VALID 在相应沿附近短暂拉高，READY 保持为 1。"], [0, 40], ["clk", "valid", "ready"]),
            step("收窄到最后一组沿", "概览只负责指路，精确时间由变化记录核对。", ["相邻上升沿间隔是 10 ns、9 ns。", "高电平宽度分别为 3 ns、4 ns、2 ns；不能先假定它是固定周期时钟。"], [19, 34], ["clk", "valid"]),
            step("保留能确认的边界", "最后一次下降沿在 26 ns；下一步应查真实接收时钟的驱动。", ["24 ns 上升，26 ns 下降；该合成激励之后不再产生时钟。", "源文件另有 28–32 ns dump-off 区间；真实数据分析须单独确认记录覆盖。", "门控 enable、reset 和 driver 不在此示例中，不能替它们编造根因。"], [23, 28], ["clk", "valid", "ready"])
        ], "conclusion": "这个教学激励在 26 ns 的下降沿后主动停止产生时钟。wavedbg 的实用路径是先定位活动边界，再取精确边沿，随后结合真实接收端的门控、复位和连接解释原因。", "limitations": ["轨道从随库 SystemVerilog 合成激励的显式延时与赋值重建，未生成或读取 FSDB。", "仅展示 clk、valid、ready、narrow、initial_x 和原 64 位 bus 的低 8 位。", "未重建同 tick 的 glitch 轨道；真实 dump-off 区间不能用“扫描完成”证明没有事件。", "数字时间线不能用于模拟抖动、setup/hold 或 CDC 签核。"], "references": [ref("examples/progressive_wave.sv", "随库小型合成激励的原样副本"), ref(FIXTURE, "固定版本的原始夹具路径"), ref(f"{SKILL_ROOT}/wavedbg-clock-reset/SKILL.md", "先查接收端边沿，再查门控/复位的证据流程")]},
        {"id": "credit-return", "title": "有数据想发，credit 却不够了？", "protocol": "Send / Free", "question": "归还的额度能否在同一拍使用，会改变结论。", "prompt": "请分析这段 send/free：初始 credit=2，容量=4，单 VC，每个 SEND/FREE 表示一份，归还的 credit 下一拍才能用。先重建额度，再解释 65 ns、75 ns 为什么没有发送。", "summary": "先说清规则，再逐拍核账；把没有请求、额度耗尽和额度尚未生效分开。", "span": [0, 90], "focus": [45, 88], "detail": [60, 88], "signals": credit, "evidence_kind": "educational-synthesis", "origin_label": "依据 credit skill 构造的教学时序 · 独立核账检查通过", "steps": [
            step("先固定接口约定", "这个示例只有一个 VC，额度初值和使用时机都已知。", ["复位 8 ns 释放；上升沿取沿前输入，counter 在沿后 0.2 ns 更新。", "初始 credit=2，容量=4；SEND/FREE 各代表一份，归还额度下一拍可用。"], [0, 90], ["clk", "rst_n", "send", "free", "credit"]),
            step("按已接受事件核账", "每拍应用 C_next=C_before+FREE−SEND，不能只看 SEND 高了多久。", ["15、25、35 ns 的 send/free 分别是 (1,0)、(1,1)、(0,1)：额度 2→1→1→2。", "45、55 ns 再各发一份，55.2 ns 的 counter 已归零。"], [45, 88], ["clk", "offered", "send", "free", "credit"]),
            step("解释等待与恢复", "把上游意愿、实际发出和归还生效时机并排看。", ["65 ns：offered=1、credit_before=0、FREE=0，因此没有 SEND。", "75 ns：虽有 FREE=1，credit_before 仍为 0；按此契约本拍不能使用归还额度。", "75.2 ns counter=1；到 85 ns 才发出下一份。"], [60, 88], ["clk", "offered", "send", "free", "credit"])
        ], "conclusion": "这个教学例子里，65 ns 没有发送是额度耗尽；75 ns 收到归还但按约定下一拍才可用，85 ns 恢复发送。所有已展示周期的额度都保持在 0–4，结论依赖这里明确给出的初始状态和接口契约。", "limitations": ["这是手工构造并由脚本逐拍核账的教学时序，不是 wavedbg 引擎响应或真实 NoC 波形。", "send/free 没有统一通用协议；不能把本例的逐拍单份编码和下一拍可用规则套到未知接口。", "真实多 VC、数量编码、归还延迟、跨窗口状态和丢失记录都需要额外约定与证据。", "这里解释已给定的控制关系；没有 KDB/RTL 证据来证明真实实现的 gating 根因。"], "references": [ref("examples/credit-contract.json", "明确的教学契约与独立逐拍核账表"), ref(f"{SKILL_ROOT}/wavedbg-credit/SKILL.md", "额度更新公式、未知初值和同拍归还使用的边界")]},
        {"id": "first-x", "title": "DATA 变成 X，从哪一刻开始查？", "protocol": "Four-state / X", "question": "先定位首个已记录的 X，再沿设计连接追原因。", "prompt": "请用 wavedbg 找到 DATA 第一次出现 X 的记录，保留受影响位和相邻控制值。不要仅凭时间相近就认定某个信号导致 X；说明下一步需要的设计证据。", "summary": "把长波形中的异常缩成一个时间、几条信号和一个待验证的假设。", "span": [0, 0.04], "focus": [0.014, 0.036], "detail": [0.019, 0.022], "signals": fake, "evidence_kind": "original-fake-backend", "origin_label": "内建假后端的原始查询回放 · 保留原始四态值", "steps": [
            step("从概览找异常区域", "先看 DATA 的活动和 X/Z 分布，再挑一小段取证。", ["DATA 初值是 00000000；15 ps 变为 00010010。", "概览可指出含 X/Z 的区间，但不能代替逐条变化证据。"], [0, 0.04], ["data", "valid", "ready"]),
            step("定位首个 X", "保留值和位掩码，不把未知数据填成零。", ["20 ps：DATA=xxxx0010，X mask=0xF0，受影响的是高 4 位。", "同一时刻 READY 变高，只能说明时间相近，不能证明因果。", "30 ps 变为 1010zzzz，Z mask=0x0F；35 ps 恢复为 01011010。"], [0.014, 0.036], ["data", "valid", "ready"]),
            step("把追因问题变具体", "接下来需要匹配的设计数据，沿实际 driver 逐段验证。", ["下一步：核对 FSDB/KDB 身份与路径映射，再查 DATA 的 driver 和相关赋值。", "检查输入、选择条件、使能、复位在异常前后的值；不能从名称猜连接。", "本回放没有 KDB/源码证据，因此结论停在已记录的 X 现象。"], [0.019, 0.022], ["clk", "rst_n", "data", "valid", "ready"])
        ], "conclusion": "首个已记录 X 在 20 ps：DATA 高 4 位未知、低 4 位是 0010。已定位到值得追查的时间和位；X 的真实来源仍需设计连接、相关代码及上游局部波形共同验证。", "limitations": ["这是 Python FakeBackend 的五信号合成模型，没有 native FSDB/KDB 执行。", "没有设计 driver 或源代码关联，不能把 READY 的同时变化当成 X 来源。", "假后端记录范围内的首个 X 不代表任意真实仿真的最早 X；真实分析仍须确认 dump 覆盖和窗口历史。", "未知值、缺记录和不支持的数据是不同状态，不能相互替代。"], "references": fake_ref + [ref(f"{SKILL_ROOT}/wavedbg/references/x-propagation.md", "沿连接、控制与局部波形逐段验证 X 的工作流")]}
    ]}


def capabilities():
    catalog = [
        ("wavedbg", "主调试流程", "从问题和时间范围出发，选择波形、设计连接与源码证据，保留尚未证实的部分。", ["信号何时变化", "谁驱动这个信号", "X 从哪段开始追"]),
        ("wavedbg-axi", "AXI / AXI-Lite / AXI-Stream", "按实际接口映射分析握手、背压、burst、ID 和包边界。", ["一条通道为什么停顿", "最后一拍是否真的被接受"]),
        ("wavedbg-apb", "APB", "区分 setup、access 和 wait，按完成时刻核对寄存器数据与错误。", ["等待了几拍", "PSLVERR 是否发生在完成访问时"]),
        ("wavedbg-ahb", "AHB-Lite", "保留地址/数据流水关系，避免把同刻的地址和返回数据错配。", ["HREADY 低时哪笔事务仍在等待", "返回数据属于哪个地址"]),
        ("wavedbg-clock-reset", "时钟 / 复位", "核对接收端边沿、复位顺序、门控和沿前/沿后观察规则。", ["时钟何时停止", "复位后为什么还是 X"]),
        ("wavedbg-fifo", "FIFO", "依据已接受读写、深度、指针和读出规则核对占用量、顺序与标志。", ["请求是否真的被接受", "指针相等是空还是满"]),
        ("wavedbg-credit", "Send / Free / Credit", "先明确额度、编码、VC 和归还时机，再逐拍核账并解释等待。", ["额度是否耗尽", "归还额度何时可用"]),
    ]
    return {"schema_version": 1, "source": SOURCE, "title": "让 AI 围绕证据调试波形", "description": "wavedbg 是接给 AI Agent 的本地查询服务：xwave 读取 FSDB 的时间、值和事件，xtrace 查询 KDB 的层次、连接和源码位置。", "positioning": "它提供查询能力和调试工作流；本页的波形回放用于说明如何逐步收窄问题。", "entry_flow": [
        {"title": "给出问题", "description": "告诉 Agent 要看哪份数据、哪条信号、大致哪段时间，以及你观察到了什么。"},
        {"title": "定位相关证据", "description": "先确认数据身份、时间单位和真实信号路径；需要追因时再查连接与相关代码。"},
        {"title": "收窄并验证", "description": "从少量信号的概览进入局部变化和时钟采样，逐条核对假设。"},
        {"title": "给出可复查结论", "description": "列出信号、时间、值、采样规则和证据缺口，让人能继续验证。"}
    ], "benefits": [
        {"title": "少搬运无关数据", "description": "按信号和时间窗口查询，无需为局部问题先把整个 FSDB 导出成文本。"},
        {"title": "从现象走向原因", "description": "把波形异常、实际 driver/load 和相关赋值放进同一条可检查的证据链。"},
        {"title": "按场景带上经验", "description": "随包 skills 提醒 Agent 先问清协议和采样约定，再判断握手、FIFO 或额度。"}
    ], "zoom": {"title": "越看越窄，证据越具体", "summary": "先用少量轨道和时间桶寻找活动或异常区域，再缩小时间范围，最后读取精确事件或对齐采样。", "stages": [
        {"id": "overview", "title": "全局概览", "description": "少量信号 + 有界时间桶，知道哪里值得继续看。", "tools": ["wave_overview"]},
        {"id": "focus", "title": "聚焦区间", "description": "只保留与问题相关的路径、窗口和必要历史。", "tools": ["wave_find", "wave_overview", "wave_edge"]},
        {"id": "evidence", "title": "精确证据", "description": "核对变化、定点值或时钟采样，保留 X/Z 和完整性。", "tools": ["wave_values", "wave_changes", "wave_analyze", "wave_count"]}
    ], "demo_note": "本页“全局 → 聚焦 → 细节”是合成数据上的导览可视化，不是产品自带的 GUI 波形查看器；也没有在浏览器启动 native 引擎。", "source_note": "底层 wave.overview 支持时间桶、focus_windows 与持久摘要块；公开 MCP 将其封装为 wave_overview。"}, "efficiency": {"title": "效率来自更有针对性的查询", "items": [
        {"title": "限定范围", "description": "减少信号数、时间跨度和返回行数；先查局部故障，必要时再补历史。"},
        {"title": "复用已打开的数据", "description": "兼容客户端可以共享本机资源会话，各自保留租约；避免反复打开同一份数据。"},
        {"title": "复用索引和摘要", "description": "发现索引和持久概览摘要可用于后续查询；底层结果会报告复用摘要块。"},
        {"title": "检查预算与完整性", "description": "按工具支持使用计数 checkpoint、设计查询 continuation，或缩窄/划分窗口。部分结果不能当成全量事实。"}
    ], "limits": ["首次打开、索引和大范围扫描仍有成本。", "本页没有速度倍数、吞吐或真实大文件性能基准。", "公开 wave_changes 不提供通用 cursor 参数；被截断时应缩窄或划分窗口。计数、设计查询和底层引擎各有继续规则。", "Registry 历史和磁盘摘要不等于 native 句柄永远有效；关闭后的实时查询引用不会被历史恢复。"]}, "skills": [{"id": name, "title": title, "description": description, "examples": examples, "source_path": f"{SKILL_ROOT}/{name}/SKILL.md"} for name, title, description, examples in catalog], "skills_note": "v0.2.1 随包包含主 skill 加六个专用 skill，共七个；它们是在查询原语之上组织证据的工作流。", "extension": {"title": "把自己的接口经验写成 skill", "description": "已有私有总线、项目握手或额外协议时，可在客户端的 skills 目录添加自己的工作流，继续调用 wavedbg 的通用查询能力。", "steps": ["写清触发场景、真实信号映射和时钟/复位。", "说明接受条件、采样时机、数量单位、延迟和跨窗口状态。", "安排“发现路径 → 局部采样 → 核账/配对 → 查连接和代码”的顺序。", "用小型已知结果案例核对结论，说明 X/Z、截断和缺记录如何处理。"], "example": {"name": "wavedbg-my-link", "scenario": "项目自定义链路的 send/free 核账", "contract": ["每个 VC 的初始额度和容量", "send/free 是脉冲、数量还是电平", "归还延迟以及能否同拍使用", "复位和未完成事务如何清理"]}, "boundary": "自定义 skill 是用户扩展，不会自动新增引擎或协议解码器。PCIe、CXL 等可以作为扩展示例讨论，不属于本版本随包七个 skills。"}, "boundaries": ["原生数据查询面向现场有授权的 Verdi SDK/runtime 环境；本页只展示合成回放。", "skills 不是完整内建协议解码器，也不是自动证明动态因果的系统。", "设计结构兼容不等于相同编译/运行；配对后仍须核对身份和动态时序。", "扫描完成不自动证明 dump 覆盖完整；观察不到事件不必然表示仿真中没有事件。"], "references": [ref("README.md", "定位、开始调试与七个 skills"), ref("docs/architecture.md", "本机共享会话、查询工具与有限采样边界"), ref("src/wavedbg/engines/wave/wave_overview.py", "时间桶、focus windows、持久摘要与复用计数"), ref("src/wavedbg/engines/wave/discovery_index.py", "信号发现索引"), ref(f"{SKILL_ROOT}/wavedbg/references/xwave.md", "缩小窗口、复用会话、预算与工具继续规则"), ref("src/wavedbg/skill_catalog.py", "随包 skills 目录及安装器"), ref("examples/fake-query-export.json", "实际 Python 假后端概览、复用与定点查询输出")]}


def value_at(case, name, time, before=False):
    events = next(item["events"] for item in case["signals"] if item["id"] == name)
    candidates = [value for tick, value in events if tick < time or (tick == time and not before)]
    assert candidates, (case["id"], name, time)
    return candidates[-1]


def verify(cases, caps, export, contract, fixture_text):
    assert cases["source"] == SOURCE and export["source"] == SOURCE and caps["source"] == SOURCE
    assert cases["schema_version"] == 1 and cases["mode"] == "guided-synthetic-replay"
    assert len(cases["cases"]) == 4
    required = {"id", "title", "protocol", "question", "prompt", "summary", "span", "focus", "detail", "signals", "steps", "conclusion", "limitations", "references"}
    for case in cases["cases"]:
        assert required <= case.keys(), case["id"]
        begin, end = case["span"]
        assert begin < end
        assert begin <= case["focus"][0] < case["focus"][1] <= end
        assert case["focus"][0] <= case["detail"][0] < case["detail"][1] <= case["focus"][1]
        ids = [item["id"] for item in case["signals"]]
        assert 5 <= len(ids) <= 7 and len(ids) == len(set(ids))
        for item in case["signals"]:
            assert item["events"][0][0] == begin
            times = [event[0] for event in item["events"]]
            assert times == sorted(set(times))
            assert all(begin <= tick <= end and len(value) == item["width"] and set(value) <= set("01xz") for tick, value in item["events"])
        for row in case["steps"]:
            assert begin <= row["window"][0] < row["window"][1] <= end
            assert set(row["signals"]) <= set(ids) and row["evidence"]
        assert case["limitations"] and case["references"] and case["conclusion"]
    indexed = {case["id"]: case for case in cases["cases"]}
    exact = fake_signals(export)
    assert indexed["ready-valid"]["signals"] == exact == indexed["first-x"]["signals"]
    rv = indexed["ready-valid"]
    assert all(value_at(rv, "valid", t / 1000) == "1" and value_at(rv, "ready", t / 1000) == "0" for t in range(15, 20))
    assert all(value_at(rv, "valid", t / 1000) == "1" and value_at(rv, "ready", t / 1000) == "1" for t in range(20, 25))
    assert value_at(rv, "data", 0.015) == "00010010" and value_at(rv, "data", 0.020) == "xxxx0010"
    assert value_at(rv, "data", 0.030) == "1010zzzz" and value_at(rv, "data", 0.035) == "01011010"
    assert next(t for t, val in exact[-1]["events"] if "x" in val) == 0.020
    assert indexed["clock-stop"]["signals"] == progressive_signals(fixture_text)
    clocks = next(item["events"] for item in indexed["clock-stop"]["signals"] if item["id"] == "clk")
    assert clocks == [[0, "0"], [5, "1"], [8, "0"], [15, "1"], [19, "0"], [24, "1"], [26, "0"]]
    assert [clocks[n+1][0] - clocks[n][0] for n in [1, 3, 5]] == [3, 4, 2]
    assert "#28000;" in fixture_text and "$fsdbDumpoff" in fixture_text and "#1000 $fsdbDumpon" in fixture_text
    credit = indexed["credit-return"]
    previous = contract["initial_credit"]
    for row in contract["rows"]:
        edge = row["edge_ns"]
        sampled = {name: int(value_at(credit, name, edge, before=True), 2) for name in ["offered", "send", "free", "credit"]}
        assert sampled["credit"] == row["credit_before"] == previous
        assert sampled["send"] == row["send"] and sampled["free"] == row["free"] and sampled["offered"] == row["offered"]
        assert sampled["send"] <= previous and sampled["send"] <= sampled["offered"]
        assert sampled["send"] == int(bool(sampled["offered"] and previous > 0))
        previous += sampled["free"] - sampled["send"]
        assert 0 <= previous <= contract["capacity"]
        assert int(value_at(credit, "credit", edge + 0.2), 2) == previous == row["credit_after"]
    assert [row["credit_after"] for row in contract["rows"][:3]] == [1, 1, 2]
    assert [row["edge_ns"] for row in contract["rows"] if row["offered"] and not row["send"]] == [65, 75]
    assert [item["id"] for item in caps["skills"]] == SKILLS
    records = {record["id"]: record["result"] for record in export["records"]}
    for row in records["points"]["rows"]:
        time_ns = int(row["time"]["resolved"]["tick"]) / 1000
        for sample in row["values"]:
            assert sample["status"] == "ok"
            assert value_at(rv, sample["alias"], time_ns) == bits(sample["value"])
    assert records["info"]["timebase"]["tick_unit_fs"] == "1000"
    assert records["info"]["timebase"]["native_timescale"] == "1ps"
    for name in ["overview", "overview-repeat", "overview-focus"]:
        assert records[name]["completeness"]["scan_complete"]
        assert records[name]["overview"]["persistent"]
        assert records[name]["quality"]["recording_coverage"] == "unknown"
    assert records["overview-repeat"]["progress"]["reused_summary_blocks"] > 0
    return {"cases": 4, "tracks": sum(len(case["signals"]) for case in cases["cases"]), "query_records": len(export["records"]), "credit_cycles": len(contract["rows"]), "skills": len(caps["skills"]), "native_execution": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, help="Read-only checkout at the exact pinned source revision; regenerate artifacts")
    parser.add_argument("--check", action="store_true", help="Validate shipped artifacts without source access")
    args = parser.parse_args()
    if args.source:
        source = args.source.resolve(strict=True)
        actual = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=source, text=True).strip()
        assert actual == REVISION, f"Wrong source revision: {actual}"
        assert all((source / path).is_file() for path in SOURCE_PATHS)
        subprocess.run(["git", "diff", "--exit-code", "--no-ext-diff", "HEAD", "--", *SOURCE_PATHS], cwd=source, check=True)
        export = capture_fake(source)
        fixture = (source / FIXTURE).read_text(encoding="utf-8")
        traces, contract = credit_example()
        cases = build_cases(fake_signals(export), progressive_signals(fixture), traces)
        caps = capabilities()
        result = verify(cases, caps, export, contract, fixture)
        write_json(OUT / "cases.json", cases)
        write_json(OUT / "capabilities.json", caps)
        write_json(OUT / "examples/fake-query-export.json", export)
        write_json(OUT / "examples/credit-contract.json", contract)
        (OUT / "examples/progressive_wave.sv").write_bytes((source / FIXTURE).read_bytes())
        manifest = {"schema_version": 1, "source": SOURCE, "policy": "Only synthetic fixture/query evidence and original public-demo content. Source hashes identify inspected private-repository files; source runtime, SDK, native binaries, FSDB, KDB, DUT and licenses are excluded.", "source_files": [{"path": path, "sha256": sha256(source / path)} for path in SOURCE_PATHS], "artifacts": [{"path": str(path.relative_to(OUT)).replace("\\", "/"), "sha256": sha256(path)} for path in [OUT / "cases.json", OUT / "capabilities.json", OUT / "examples/fake-query-export.json", OUT / "examples/credit-contract.json", OUT / "examples/progressive_wave.sv"]]}
        write_json(OUT / "provenance.json", manifest)
    else:
        cases = read_json(OUT / "cases.json")
        caps = read_json(OUT / "capabilities.json")
        export = read_json(OUT / "examples/fake-query-export.json")
        contract = read_json(OUT / "examples/credit-contract.json")
        fixture = (OUT / "examples/progressive_wave.sv").read_text(encoding="utf-8")
        result = verify(cases, caps, export, contract, fixture)
        manifest = read_json(OUT / "provenance.json")
        assert manifest["source"] == SOURCE
        for artifact in manifest["artifacts"]:
            path = (OUT / artifact["path"]).resolve(strict=True)
            assert path.is_relative_to(OUT.resolve())
            assert sha256(path) == artifact["sha256"], artifact["path"]
        assert sha256(OUT / "examples/progressive_wave.sv") == next(row["sha256"] for row in manifest["source_files"] if row["path"] == FIXTURE)
    print(json.dumps({"status": "pass", **result}, ensure_ascii=False))


if __name__ == "__main__":
    main()

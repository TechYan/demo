# PVKit demo

**[打开在线示例目录](https://techyan.github.io/demo/pvkit/)** · [返回 demo 仓库](../README.md)

收录 xpvkit **0.5.5** release 中的 **15 个合成场景**：7 个 AXI4、8 个 CXL Native。
每个场景均提供交互 HTML、实际 TUI 打印、分析日志、完整 tracker 和原始 CSV。
无需安装 Python 或下载工具即可通过下表直接浏览。数据不代表真实 DUT 性能。

## 在线浏览

### AXI4

| 场景 | 观察重点 | HTML | TUI 打印 | 分析日志 | Tracker | CSV |
|---|---|---|---|---|---|---|
| 只读流量 | 观察 AR/R 关联、读带宽与请求到响应延迟。 | [打开](https://techyan.github.io/demo/pvkit/examples/axi4/read_only/traffic.pv.html) | [打开](https://techyan.github.io/demo/pvkit/examples/axi4/read_only/tui.html) | [查看](https://techyan.github.io/demo/pvkit/examples/axi4/read_only/traffic.analyze.log) | [查看](https://techyan.github.io/demo/pvkit/examples/axi4/read_only/traffic.tracker.log) | [下载](https://techyan.github.io/demo/pvkit/examples/axi4/read_only/traffic.csv) |
| 只写流量 | 观察 AW/W/B 关联、写带宽与写响应。 | [打开](https://techyan.github.io/demo/pvkit/examples/axi4/write_only/traffic.pv.html) | [打开](https://techyan.github.io/demo/pvkit/examples/axi4/write_only/tui.html) | [查看](https://techyan.github.io/demo/pvkit/examples/axi4/write_only/traffic.analyze.log) | [查看](https://techyan.github.io/demo/pvkit/examples/axi4/write_only/traffic.tracker.log) | [下载](https://techyan.github.io/demo/pvkit/examples/axi4/write_only/traffic.csv) |
| 并发读写 | 在同一时间轴比较读写带宽、outstanding 和通道背压。 | [打开](https://techyan.github.io/demo/pvkit/examples/axi4/concurrent/traffic.pv.html) | [打开](https://techyan.github.io/demo/pvkit/examples/axi4/concurrent/tui.html) | [查看](https://techyan.github.io/demo/pvkit/examples/axi4/concurrent/traffic.analyze.log) | [查看](https://techyan.github.io/demo/pvkit/examples/axi4/concurrent/traffic.tracker.log) | [下载](https://techyan.github.io/demo/pvkit/examples/axi4/concurrent/traffic.csv) |
| 阶梯带宽 | 观察负载分阶段变化及有效数据窗口。 | [打开](https://techyan.github.io/demo/pvkit/examples/axi4/bandwidth_steps/traffic.pv.html) | [打开](https://techyan.github.io/demo/pvkit/examples/axi4/bandwidth_steps/tui.html) | [查看](https://techyan.github.io/demo/pvkit/examples/axi4/bandwidth_steps/traffic.analyze.log) | [查看](https://techyan.github.io/demo/pvkit/examples/axi4/bandwidth_steps/traffic.tracker.log) | [下载](https://techyan.github.io/demo/pvkit/examples/axi4/bandwidth_steps/traffic.csv) |
| 混合指标 | 检查 WSTRB、Partial write、延迟与背压。 | [打开](https://techyan.github.io/demo/pvkit/examples/axi4/mixed_metrics/traffic.pv.html) | [打开](https://techyan.github.io/demo/pvkit/examples/axi4/mixed_metrics/tui.html) | [查看](https://techyan.github.io/demo/pvkit/examples/axi4/mixed_metrics/traffic.analyze.log) | [查看](https://techyan.github.io/demo/pvkit/examples/axi4/mixed_metrics/traffic.tracker.log) | [下载](https://techyan.github.io/demo/pvkit/examples/axi4/mixed_metrics/traffic.csv) |
| 高并发请求 | 观察 1024 outstanding 场景的趋势与事务查询。 | [打开](https://techyan.github.io/demo/pvkit/examples/axi4/high_outstanding/traffic.pv.html) | [打开](https://techyan.github.io/demo/pvkit/examples/axi4/high_outstanding/tui.html) | [查看](https://techyan.github.io/demo/pvkit/examples/axi4/high_outstanding/traffic.analyze.log) | [查看](https://techyan.github.io/demo/pvkit/examples/axi4/high_outstanding/traffic.tracker.log) | [下载](https://techyan.github.io/demo/pvkit/examples/axi4/high_outstanding/traffic.csv) |
| 响应未完成 | 诊断示例：保留缺失响应、未完成事务及已观察证据。 | [打开](https://techyan.github.io/demo/pvkit/examples/axi4/incomplete_response/traffic.pv.html) | [打开](https://techyan.github.io/demo/pvkit/examples/axi4/incomplete_response/tui.html) | [查看](https://techyan.github.io/demo/pvkit/examples/axi4/incomplete_response/traffic.analyze.log) | [查看](https://techyan.github.io/demo/pvkit/examples/axi4/incomplete_response/traffic.tracker.log) | [下载](https://techyan.github.io/demo/pvkit/examples/axi4/incomplete_response/traffic.csv) |

### CXL Native

| 场景 | 观察重点 | HTML | TUI 打印 | 分析日志 | Tracker | CSV |
|---|---|---|---|---|---|---|
| 全双工流量 | 比较 M2S/S2M 消息、双向带宽与事务关联。 | [打开](https://techyan.github.io/demo/pvkit/examples/cxl_native/full_duplex/traffic.pv.html) | [打开](https://techyan.github.io/demo/pvkit/examples/cxl_native/full_duplex/tui.html) | [查看](https://techyan.github.io/demo/pvkit/examples/cxl_native/full_duplex/traffic.analyze.log) | [查看](https://techyan.github.io/demo/pvkit/examples/cxl_native/full_duplex/traffic.tracker.log) | [下载](https://techyan.github.io/demo/pvkit/examples/cxl_native/full_duplex/traffic.csv) |
| 突发与重新初始化 | 观察独立初始化域、突发流量与重新初始化。 | [打开](https://techyan.github.io/demo/pvkit/examples/cxl_native/reinitialize/traffic.pv.html) | [打开](https://techyan.github.io/demo/pvkit/examples/cxl_native/reinitialize/tui.html) | [查看](https://techyan.github.io/demo/pvkit/examples/cxl_native/reinitialize/traffic.analyze.log) | [查看](https://techyan.github.io/demo/pvkit/examples/cxl_native/reinitialize/traffic.tracker.log) | [下载](https://techyan.github.io/demo/pvkit/examples/cxl_native/reinitialize/traffic.csv) |
| 读 credit 限流 | 观察读方向各 channel/slot 记录到的 credit EMPTY 区间。 | [打开](https://techyan.github.io/demo/pvkit/examples/cxl_native/read_credit_throttle/traffic.pv.html) | [打开](https://techyan.github.io/demo/pvkit/examples/cxl_native/read_credit_throttle/tui.html) | [查看](https://techyan.github.io/demo/pvkit/examples/cxl_native/read_credit_throttle/traffic.analyze.log) | [查看](https://techyan.github.io/demo/pvkit/examples/cxl_native/read_credit_throttle/traffic.tracker.log) | [下载](https://techyan.github.io/demo/pvkit/examples/cxl_native/read_credit_throttle/traffic.csv) |
| 写 credit 限流 | 观察写方向 credit EMPTY 与消息发送的时间关系。 | [打开](https://techyan.github.io/demo/pvkit/examples/cxl_native/write_credit_throttle/traffic.pv.html) | [打开](https://techyan.github.io/demo/pvkit/examples/cxl_native/write_credit_throttle/tui.html) | [查看](https://techyan.github.io/demo/pvkit/examples/cxl_native/write_credit_throttle/traffic.analyze.log) | [查看](https://techyan.github.io/demo/pvkit/examples/cxl_native/write_credit_throttle/traffic.tracker.log) | [下载](https://techyan.github.io/demo/pvkit/examples/cxl_native/write_credit_throttle/traffic.csv) |
| 同一 slot 反复 EMPTY | 观察同一个物理 slot 多次耗尽与恢复。 | [打开](https://techyan.github.io/demo/pvkit/examples/cxl_native/repeated_empty/traffic.pv.html) | [打开](https://techyan.github.io/demo/pvkit/examples/cxl_native/repeated_empty/tui.html) | [查看](https://techyan.github.io/demo/pvkit/examples/cxl_native/repeated_empty/traffic.analyze.log) | [查看](https://techyan.github.io/demo/pvkit/examples/cxl_native/repeated_empty/traffic.tracker.log) | [下载](https://techyan.github.io/demo/pvkit/examples/cxl_native/repeated_empty/traffic.csv) |
| 交错与重叠 EMPTY | 展开各 slot，检查交错和重叠耗尽区间。 | [打开](https://techyan.github.io/demo/pvkit/examples/cxl_native/staggered_slots/traffic.pv.html) | [打开](https://techyan.github.io/demo/pvkit/examples/cxl_native/staggered_slots/tui.html) | [查看](https://techyan.github.io/demo/pvkit/examples/cxl_native/staggered_slots/traffic.analyze.log) | [查看](https://techyan.github.io/demo/pvkit/examples/cxl_native/staggered_slots/traffic.tracker.log) | [下载](https://techyan.github.io/demo/pvkit/examples/cxl_native/staggered_slots/traffic.csv) |
| 独立 channel 反复 EMPTY | 检查四条读写 channel 的独立耗尽模式。 | [打开](https://techyan.github.io/demo/pvkit/examples/cxl_native/independent_channels/traffic.pv.html) | [打开](https://techyan.github.io/demo/pvkit/examples/cxl_native/independent_channels/tui.html) | [查看](https://techyan.github.io/demo/pvkit/examples/cxl_native/independent_channels/traffic.analyze.log) | [查看](https://techyan.github.io/demo/pvkit/examples/cxl_native/independent_channels/traffic.tracker.log) | [下载](https://techyan.github.io/demo/pvkit/examples/cxl_native/independent_channels/traffic.csv) |
| 长时间域中的短脉冲 | 缩放长 capture，检查短 credit EMPTY 脉冲。 | [打开](https://techyan.github.io/demo/pvkit/examples/cxl_native/short_pulses/traffic.pv.html) | [打开](https://techyan.github.io/demo/pvkit/examples/cxl_native/short_pulses/tui.html) | [查看](https://techyan.github.io/demo/pvkit/examples/cxl_native/short_pulses/traffic.analyze.log) | [查看](https://techyan.github.io/demo/pvkit/examples/cxl_native/short_pulses/traffic.tracker.log) | [下载](https://techyan.github.io/demo/pvkit/examples/cxl_native/short_pulses/traffic.csv) |

## 如何阅读

- **HTML 报告**：切换 Performance / Debug，缩放或框选时间段，查看事务关联、筛选与查询；报告内嵌脚本和数据，可离线打开。
- **TUI 打印**：同一 CSV 的真实彩色终端输出，支持 `standard / full / compact` 和 `120 / 80 / 60` 列。可复制纯文本或下载 ANSI。终端回放不执行分析，交互查询请使用 HTML。
- **分析日志** `traffic.analyze.log`：`full --trend all` 对应的 UTF-8 文本报告，方便搜索、复制和比较。
- **Tracker** `traffic.tracker.log`：完整 capture 的时序事件和事务关联。AXI 保留 AW/W/B/AR/R；CXL 保留 native channel、物理 slot 和请求引用。`UNKNOWN` 为证据不足，`NOT_CAPTURED` 为未采集。
- 默认 `--window auto` 以接受的数据活动计算带宽；事务、延迟、outstanding、背压与诊断使用完整 capture。手动选窗后 HTML 会按所选范围重算相应指标。
- `incomplete_response` 用于演示缺失响应诊断。CXL `EMPTY` 不等于连续 credit 余额，未记录的区间不能推断为已知有 credit。

## 文件布局与本地浏览

```text
pvkit/
├── index.html                 # 在线/离线场景导航
├── README.md                  # 场景说明与在线链接
├── manifest.json              # release 版本与原始 CSV SHA256
└── examples/
    ├── axi4/<scene>/
    └── cxl_native/<scene>/
        ├── traffic.csv
        ├── traffic.pv.html
        ├── traffic.analyze.log
        ├── traffic.tracker.log
        ├── tui.html
        └── captures/          # 3 种模式 × 3 种列宽的 TXT / ANSI
```

下载仓库 ZIP 并解压后打开根目录 `index.html`；保留 `assets/` 与 `pvkit/` 的相对位置。
已有 xpvkit 0.5.5 工具时，可从仓库根目录重新分析任意 CSV，例如：

```bash
python /path/to/xpv.pyz analyze pvkit/examples/axi4/concurrent/traffic.csv --report-mode full --trend all
```

重建整套页面需要原版 `xpvkit-0.5.5.zip`、Python 3.11+ 和可选终端依赖 Rich：

```bash
python -m pip install rich
python scripts/build_pvkit.py --release /path/to/xpvkit-0.5.5.zip
```

构建脚本校验 release ZIP 与内嵌工具的 SHA256，仅提取 AXI4 / CXL Native 的 CSV，
使用包内原版分析器生成报告与 TUI；不修改原始数据，也不需要仿真环境。
`manifest.json` 记录输入来源，`SHA256SUMS` 校验发布的静态文件。

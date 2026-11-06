# wavedbg AXI Performance / v0.3.0

[打开演示页](https://techyan.github.io/demo/wavedbg/performance/) ·
[实际报告](https://techyan.github.io/demo/wavedbg/performance/data/native/report.html) ·
[在线日志](https://techyan.github.io/demo/wavedbg/performance/#logs)

本目录展示已经生成的真实 FSDB 分析产物，使用自建 AXI4 激励，
不包含用户 DUT 波形。wavedbg 0.3.0 读取 600 个 rising / pre-edge 样本，
按原始 probe 契约生成 CSV，由固定版本 xpvkit 0.5.6 生成原生 HTML 与日志。

## 文件与指标

- `data/native/`：wavedbg 采集后的 HTML、tracker、analysis log、JSON 和 CSV。
- `data/probe/`：同一总线同时接入原始 xpvkit SV probe 的参考产物。
- `data/comparison.json`：已有运行的 13 项语义比较结果。
- `data/publication.json`：来源、发布处理、源文件与公开文件的 SHA-256。
- `data/SHA256SUMS`：公开文件校验列表。
- `assets/`：由实际 HTML 渲染的 Performance / Debug view 截图。
- `wavedbg-axi-native-demo.zip`：可离线打开的精选示例包。

示例有 1 读、1 写，读 4 B / 写 6 B，读延迟 100 ps / 写延迟 300 ps。
auto 数据窗口 `[300,500)` ps 对应 50 GB/s；
full capture `[100,60100)` ps 对应 0.1666667 GB/s。
HTML 使用相对时间，0 ns 对应 capture 的 100 ps。

本地 seq 起点在 wavedbg capture 中为 1、probe 中为 2，
所以原始 CSV 不是字节相同；比较的是事件字段、相对顺序和性能口径。
`protocol_pass` 保持 null，报告不是 DUT 协议签核。

公开副本仅处理本地路径和主机文件指纹，保留原始数值、事件与报告程序。
原始 FSDB、完整样本/查询流、运行 manifest、SDK 和许可证日志不在公开包内。
报告由已有运行产生；发布脚本不会重新执行仿真、采样或分析。

## 维护

页面位于 `src/pages/wavedbg/performance/index.astro`，
样式位于 `src/styles/axi-performance.css`。更新既有运行的公开副本：

```sh
python scripts/publish_wavedbg_performance.py --run-directory PATH_TO_COMPLETED_RUN
npm run build:github
```

生成器预期既有运行目录含 `wave-report-02`、`probe-report-02`、
`probe.csv` 和 `native-verification-02.json`。发布前人工确认目录属于自建演示数据。
它不适用于公开用户工程数据。

旧 `/wavedbg/` 四个教学案例仍固定在 v0.2.1；本目录是独立的 v0.3.0 性能演示。
源码与发行包位于私有 wavedbg 仓库，需要对应访问权限；此演示可独立浏览。

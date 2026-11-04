# wavedbg 合成导览数据

此目录为 `/wavedbg/` 页面提供可核对的教学内容。wavedbg 是供 AI Agent 使用的本地波形与设计查询服务；浏览器中的波形是预制导览回放。页面不启动 native 引擎，也不代表产品自带 GUI 波形查看器。

内容依据 `TechYan/wavedbg` 的 v0.2.1 源码，固定到提交 `9bf7b333dce94c73f64877bd7e676524b35b033e`。`provenance.json` 记录已核对源文件和发布数据的 SHA-256。源仓库可见性与本站独立；本目录不依赖访问源仓库才能播放或检查。

| 文件 | 用途 |
| --- | --- |
| `cases.json` | 四个中文导览案例，含轨道、三级视野、分析步骤、结论、边界和参考路径 |
| `capabilities.json` | 用途、使用流程、渐进查询、效率机制、七个随包 skills 与自定义扩展说明 |
| `examples/fake-query-export.json` | 直接调用固定版本原始 Python `FakeBackend.invoke` 得到的 12 条查询记录，响应正文未改写 |
| `examples/progressive_wave.sv` | 随库小型合成测试激励的原样副本，不包含用户 DUT |
| `examples/credit-contract.json` | 明确标为教学合成的单 VC 契约与八拍额度核账表 |
| `provenance.json` | 固定版本、源文件哈希和数据文件哈希 |

`cases.json` 的 `mode` 为 `guided-synthetic-replay`。所有 `span`、`focus`、`detail`、`steps[].window` 和 `signals[].events[][0]` 均以 **ns** 表示；信号值为保留位宽的 `0/1/x/z` 字符串。小于 1 ns 的图建议用 ps 显示轴标签。所有轨道在展示区间起点具有初始值，时间升序且不重复。

| 案例 ID | 时间跨度 | 证据来源与可以说明的内容 |
| --- | --- | --- |
| `ready-valid` | 0–0.04 ns，即 0–40 ps | 原始假后端五信号。15–20 ps 出现 VALID 高、READY 低；不能据同 tick 电平变化认定无歧义握手 |
| `clock-stop` | 0–40 ns | 从原样合成激励中显式 `#delay` 和赋值重建的预期时序；最后上升沿 24 ns、下降沿 26 ns，未运行仿真或读取 FSDB |
| `credit-return` | 0–90 ns | 依照随包 credit skill 的公式和初始三拍例子扩展的教学合成；独立沿前采样核账解释 65/75 ns 等待和 85 ns 恢复 |
| `first-x` | 0–0.04 ns，即 0–40 ps | 原始假后端五信号；20 ps DATA 高四位成为 X，30 ps 低四位成为 Z，不提供设计因果证明 |

每个案例额外包含 `evidence_kind` 和 `origin_label`，用于在页面清楚显示来源：`original-fake-backend`、`source-fixture-reconstruction`、`educational-synthesis`。后两类不能渲染成引擎返回的诊断结果。导览步骤是编辑整理的解释，原始查询响应单独保存在 exports 文件中。

原始假后端导出保留 `/fixtures/xwave/basic.fsdb` 这一内建合成身份字符串；它不是本机文件路径，查询没有读取该文件。生成器仅把临时索引/摘要缓存重定向到临时目录，不更改查询实现或响应。导出包含打开、元信息、五条 raw timeline、批量取值、概览、重复概览、收窄概览和关闭。重复概览确实返回非零 `reused_summary_blocks`；这只验证小型合成模型上的复用机制，不是性能基准。它是 Python 后端层面的运行证据，不能称为完整 MCP 客户端集成或 native 验收。

`clock-stop` 只重建显式延时刺激，不解释仿真调度区域。它展示 `clk`、`valid`、`ready`、`narrow`、`initial_x` 和原 64 位总线的低 8 位。源文件中的同 tick glitch 轨道没有进入本导览。源文件另有 28–32 ns dump-off；未运行 native 时，不能据重建时间线声明真实 FSDB 在该处记录完整。

七个随包 skills 是 `wavedbg`、`wavedbg-axi`、`wavedbg-apb`、`wavedbg-ahb`、`wavedbg-clock-reset`、`wavedbg-fifo`、`wavedbg-credit`。它们指导 Agent 明确信号、协议和采样契约后组织证据，不是完整协议解码器。用户可在客户端添加自己的 skill；PCIe、CXL 等不在本版本随包列表中。

渐进视野对应“概览指路 → 缩小时间和信号范围 → 精确事件/采样取证”。实际底层 `wave.overview` 有时间桶、候选 focus window、持久摘要块和完整性信息；公开 MCP 的 `wave_overview` 封装该能力。复用会话、信号发现索引、限制范围和预算可减少重复工作，但首次打开、索引和大范围扫描仍有成本。公开 `wave_changes` 没有通用 cursor 参数；计数 checkpoint、设计查询 continuation 和底层引擎分页各有自己的规则。

源仓库的 `docs/pdf/evidence/synthetic-results.json` 另有自身标注的旧上游提交 `0b8c5fff11c9b4bf1e668787322ec41d08dd9d91`，内容是排序与前缀计数的合成实验。生成器记录其源文件哈希以说明曾核对，但未将它当成本页案例证据或 v0.2.1 native 运行结果。

仓库根目录使用标准库即可检查现有发布内容：

```text
python scripts/build_wavedbg_examples.py --check
```

有固定源码 checkout 时，可重新生成数据和哈希：

```text
python -B scripts/build_wavedbg_examples.py --source SOURCE_CHECKOUT
```

脚本首先核对准确的 Git HEAD；它不修改源文件。检查包括 schema 必需字段、起点初值、位宽/四态值、无重复的有序时间、逐级窗口、步骤轨道引用、原始查询与回放逐值一致、源夹具重建一致、X/Z 掩码、时钟边沿、八拍 credit 的沿前/沿后状态、同拍归还规则、七个 skills 列表及发布文件哈希。检查过程不需要 native SDK、许可证、FSDB、KDB 或网络。

此目录只发布教学合成数据、一个合成测试激励、人工编写说明与查询输出，不发布源运行时、native SDK/二进制、真实设计波形、KDB、用户 DUT 或许可证。

# xDCT 接口变化演示

打开 [index.html](index.html)，比较 `chip_top` 从 CL `123450` 到 `123456` 的真实合成示例。页面支持破坏性、非破坏性、仅声明顺序筛选，以及端口名 / 分类搜索；每项保留前后声明、变化属性与原始记录。全部资源使用相对链接，可离线浏览。

来源：`TechYan/xDCT`，版本 `v0.1.0-prototype`，固定提交 `c19ed688797dabf46e8794bd63ae4385981b5785`。仓库制作时为私有。公开包保留源仓库现有示例，不包含解析器、私有工程或 `pyslang` 二进制。原路径、SHA-256 与复核结果见 [provenance.json](provenance.json)。

## 结果与证据

| 指标 | 原始结果 |
|---|---:|
| Baseline / Current 端口数 | 9 → 9 |
| 变化名称数 | 10 |
| 破坏性变化 | 6 |
| 新增 / 移除 / 修改 / 仅声明顺序 | 1 / 1 / 5 / 3 |

6 处破坏性变化由 1 个移除与 5 个修改组成。4 个非破坏性变化由 1 个新增与 3 个仅顺序变化组成。分类可能重叠，例如 `ctrl` 同时有 `MODPORT_CHANGED` 和 `ORDER_CHANGED`。声明顺序使用清单中的零基索引。

| 变化 | 内容 |
|---|---|
| `legacy_mode` | 端口移除；breaking |
| `link_up` | 新增输出；info |
| `rx_data` / `tx_data` | 参数 `DATA_W` 从 16 变为 32，解析后位宽和类型变化；breaking |
| `lanes` | unpacked array 从 2 项变为 4 项，总 bitstream 位宽 16 → 32；breaking |
| `status` | output → input；breaking |
| `ctrl` | `ctrl_if.master` → `ctrl_if.slave`，同时声明顺序变化；breaking |
| `clk` / `rst_n` / `pad` | 只有声明顺序变化；info |

下列文件均逐字节复制原仓库证据：

- [旧版 SystemVerilog](examples/top_v1.sv) 与 [新版 SystemVerilog](examples/top_v2.sv)
- [Baseline manifest](demo/baseline_cl123450.json) 与 [Current manifest](demo/current_cl123456.json)
- [原始 diff JSON](demo/diff_cl123450_to_cl123456.json)
- [原始文本报告](demo/report_cl123450_to_cl123456.txt)

制作展示包时，使用固定提交中的 `topif.py` 和原仓库附带的 `pyslang 11.0.0` 重新提取了两个 SV 的 manifest，并确认与现有文件完全相同；`compare_manifests` 与 `render_report` 也精确重现了现有 diff 和报告。浏览器读取同一份证据，仅负责渲染与筛选，没有重新实现 SystemVerilog 解析或变化判定策略。

## 本地复现原型

在有源仓库权限的环境中：

```powershell
git clone https://github.com/TechYan/xDCT.git
cd xDCT
git checkout c19ed688797dabf46e8794bd63ae4385981b5785
python topif.py extract --source examples/top_v1.sv --top-module chip_top --p4-cl 123450 --output demo/baseline_cl123450.json
python topif.py check --source examples/top_v2.sv --top-module chip_top --p4-cl 123456 --baseline demo/baseline_cl123450.json --current-manifest demo/current_cl123456.json --diff-json demo/diff_cl123450_to_cl123456.json --report demo/report_cl123450_to_cl123456.txt
```

最后一条命令应返回 **2**，表示发现破坏性接口变化；不是解析失败。退出码 `0` 表示没有破坏性变化，`1` 表示解析或配置失败。

源仓库附带的编译扩展适用于 CPython 3.12 / Windows x64；其他环境需按原仓库 `requirements.txt` 安装匹配的 `pyslang`。展示包不发布此扩展。

## 原型范围

支持 ANSI 风格 module ports、普通端口与 interface / modport、参数展开后的位宽及 packed / unpacked 数组类型。它可分类新增、移除、方向、位宽、类型、signedness、interface / modport、storage 与顺序变化。

`ADDED` 和 `ORDER_ONLY` 的非破坏性判定来自当前原型策略。生产环境的项目配置、baseline 更新规则、诊断格式及真实生成顶层回归仍需补齐。此页面展示固定合成示例，没有接受用户 SV 上传或执行 CI 门禁。

## 展示包检查

从 demo 仓库根目录运行 `python scripts/build_register_demos.py --check`，只需 Python 标准库。它核对 9 → 9 端口、10 个变化、6 个 breaking、3 个 order-only、每个变化的 old/new 与原始 manifest 的对应关系、原始证据 SHA-256 和本地 HTML 链接。

用 `--xpggen-source PATH --xdct-source PATH --capture` 可重新生成两个展示包。此步骤需要固定提交的私有源仓库与其运行依赖；具体见 [xpggen 复现说明](../xpggen/README.md)。

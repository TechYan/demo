# xpggen 演示包

打开 [index.html](index.html) 浏览真实 Textual TUI 的五个场景、原仓库四张 SVG，以及由当前 PG 导出器生成的四种输出。文件使用相对链接，可通过 GitHub Pages、Cloudflare 或解压后离线打开。

本页面是**真实 TUI 截图的场景回放与导出结果浏览器**。完整的搜索、字段组合、步骤排序与保存功能运行在本地 Python Textual 应用中。五个场景不是计时终端录像；页面没有把 TUI 功能重新实现成网页。

## 内容与来源

来源仓库：`TechYan/xpggen`，固定提交 `42417d36867bdbc05992e09a72e5f500540291a4`。仓库在制作时为私有，公开包只包含本演示所需的合成样例、SVG 与生成输出。逐文件原路径与 SHA-256 见 [provenance.json](provenance.json)。xpggen 原始素材的 [MIT License](LICENSE) 随包保留。

| 文件 | 内容 |
|---|---|
| [examples/rnoc.sample.json](examples/rnoc.sample.json) | 原仓库内置合成目录：288 个寄存器、1,296 个字段 |
| [scripts/make_demo_rnoc.py](scripts/make_demo_rnoc.py) | 原始合成目录生成脚本；6 个名称分组，每组 48 个寄存器 |
| `previews/*.svg` | 原仓库四个预览，逐字节保留 |
| `captures/*.svg` | 本次使用当前代码真实运行并导出的五张 TUI 截图 |
| [examples/bringup.pg.json](examples/bringup.pg.json) | `xpggen.pg.v2` 流程，保留字段赋值与解析后的 mask/value |
| [examples/bringup.csv](examples/bringup.csv) | 原始 CSV 预览输出 |
| [examples/bringup.sv](examples/bringup.sv) | 原始 SystemVerilog 预览输出 |
| [examples/bringup.md](examples/bringup.md) | 原始 Markdown Guide 预览输出 |

示例中的 `pcie / phub / dma / msi / atu / debug` 来自生成脚本，不代表真实芯片配置。目录保留原始偏移，没有最终硬件地址。不同名称分组可有相同偏移；演示没有为它们虚构完整地址映射。

## 流程与操作语义

六步流程通过源码 `src/xpggen/pg.py` 中的 `make_step` 和 `render_*` 函数生成，没有在网页中重新实现导出器：

1. `read`：读取 `REG__XPG__PCIE__CTRL_000`，不比较结果。
2. `write`：向完整控制寄存器写入 `0x1`。
3. `rmw`：对 `REG__XPG__PCIE__CFG_004` 的 `mode=0x3`、`threshold=0x20` 做一次读改写；聚合掩码 `0x0000FFF0`，聚合值 `0x00002030`。
4. `read_check`：比较上述两个字段，保留其他位不参与比较。
5. `poll`：检查 `REG__XPG__PCIE__STATUS_001.ready=1`，每 10 μs 重试，超时 1,000 μs。
6. `delay`：等待 25 μs，不需要寄存器目标。

JSON 保存语义字段及解析结果；CSV 和 Markdown 是可读预览。SystemVerilog 忠实保留当前导出器的代码形态，包括 `read_reg / write_reg`、字段掩码、四态比较、轮询超时与延时。接入仿真时需要工程定义寄存器宏、`regval`、访问函数以及合适的 time unit。本演示未编译 SV，也未执行寄存器或 DUT 访问。

## 本地运行真实 TUI

在有源仓库访问权限的环境中：

```powershell
git clone https://github.com/TechYan/xpggen.git
cd xpggen
git checkout 42417d36867bdbc05992e09a72e5f500540291a4
python -m pip install -e .
python -m xpggen --demo
```

也可以运行 `python -m xpggen path/to/rnoc.json` 载入自己的上游扁平目录。`F2` 进入 Register，`F3` 进入 PGGen，`Ctrl+S` 保存 PG。

## 重新生成与校验展示包

在 demo 仓库根目录，准备两个固定提交的源仓库，安装 `rich==15.0.0`、`textual==8.2.8`，然后运行：

```powershell
python scripts/build_register_demos.py --xpggen-source PATH_TO_XPGGEN --xdct-source PATH_TO_XDCT --capture
python scripts/build_register_demos.py --check
```

`--capture` 直接调用 `XpgGenApp.run_test(size=(180, 52))` 与 `App.export_screenshot()`。使用 truecolor 终端环境，隐藏时钟、关闭输入光标闪烁，将 Logo 动画固定为 phase 0，并等待有限动画完成。Rich 内部生成的非视觉 SVG 标识符会被规范化；不修改截图中的文本或几何布局。截图中六步流程通过真实步骤模型载入，导出预览页签由测试 API 点击。截图没有宣称逐键操作录像。

不带 `--capture` 的重建会沿用已有截图。`--check` 只用 Python 标准库，验证目录与字段数量、六种操作、聚合掩码、轮询参数、四份输出、SVG、原始证据 SHA-256 和 HTML 本地链接。原始 Rich SVG 含可选 CDN 字体 URL；离线时使用本地等宽字体回退。

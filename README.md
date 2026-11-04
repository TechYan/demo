# Demo

**[打开在线 Demo 首页](https://techyan.github.io/demo/)**

本仓库按项目保存可直接浏览的演示；每个项目有独立目录、说明和网页入口，方便后续加入其他 demo。

| 项目 | 内容 | 在线访问 | 说明与文件 |
|---|---|---|---|
| PVKit | 7 个 AXI4、8 个 CXL Native 场景：交互 HTML、TUI 打印、分析日志、Tracker 和原始 CSV | [打开场景目录](https://techyan.github.io/demo/pvkit/) | [PVKit README](pvkit/README.md) · [示例文件](pvkit/examples/) |

## 快速开始

1. 打开 [PVKit 场景目录](https://techyan.github.io/demo/pvkit/)，选择感兴趣的 AXI4 或 CXL Native 场景。
2. 点 **HTML 报告** 操作图表、时间窗口和事务查询；点 **TUI 打印** 浏览终端输出。
3. 点 **分析日志** 或 **Tracker** 查看、复制文本，或下载原始 CSV 重新分析。

所有展示均为静态文件，浏览者无需安装工具。示例来自 xpvkit v0.5.5 release 的合成数据，
不代表真实 DUT 性能。完整场景表、指标口径和复现方式见 [PVKit README](pvkit/README.md)。

## 仓库结构

```text
index.html        # 所有 demo 的网页入口
README.md         # 所有 demo 的 GitHub 入口
assets/           # 导航与 TUI 回放的静态样式/脚本
pvkit/            # PVKit 场景、报告、日志与说明
scripts/          # 从已有 release 重建演示的脚本
```

后续项目放到新的顶级目录，并在本 README 和 `index.html` 中增加入口。
GitHub Pages 从 `main` 分支根目录发布，`.nojekyll` 保留原始静态文件。
下载仓库 ZIP、解压并打开 `index.html` 也可以离线浏览。

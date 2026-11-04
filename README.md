# TechYan / Engineering Playground

**[打开在线 Demo](https://techyan.github.io/demo/)** · [部署与本地开发](docs/DEPLOYMENT.md)

可直接体验的协议、验证、性能分析与寄存器工具。导航以 [DevPortfolio](https://github.com/RyanFitzgerald/devportfolio) 为基础，使用 **Astro 7 + Tailwind CSS 4** 静态构建；包含分类筛选、中英文搜索、深浅主题、移动布局，以及每个项目的详情与演示入口。字体随站点构建，无运行时字体服务依赖。

## 项目目录

| 项目 | 已收录内容 | 在线入口 | 数据与说明 |
|---|---|---|---|
| **PVKit** | 15 个 AXI4 / CXL Native 场景；HTML、TUI、分析日志、tracker、CSV | [打开](https://techyan.github.io/demo/projects/pvkit/) | [README](pvkit/README.md) |
| **Bus Protocol Lab** | AXI→PCIe Packet Studio、AXI Atomic、PCIe TLP Split 三个独立工具 | [打开](https://techyan.github.io/demo/projects/bus-protocol-lab/) | [README](bus-protocol-lab/README.md) |
| **PG Builder** | 可操作的寄存器 PG 编辑器，2 个虚构 block、4 个寄存器、read/write/rmw/poll 样例及导出 | [打开](https://techyan.github.io/demo/projects/pg_gen/) | [README](pg_gen/README.md) |
| **UVM Wiki** | 从脱敏 demo_uvm 真实生成的 7 种视图、结构化索引和源码浏览 | [打开](https://techyan.github.io/demo/projects/uvm_wiki/) | [README](uvm_wiki/README.md) |
| **SVIP** | AXI4 / APB / JTAG / SPI / Control 的 13 份完整指南与 17 个自有示例 | [打开](https://techyan.github.io/demo/projects/svip/) | [README](svip/README.md) |
| **xpggen** | 5 张真实 TUI 场景、4 张原始预览、288 个合成寄存器和 6 步 PG 的四种导出 | [打开](https://techyan.github.io/demo/projects/xpggen/) | [README](xpggen/README.md) |
| **xDCT** | 两版 top interface 的语义对比、筛选、原始 manifest/diff/report；6 个 breaking change | [打开](https://techyan.github.io/demo/projects/xDCT/) | [README](xDCT/README.md) |

每个项目说明展示方式与证据边界：浏览器工具可直接操作，TUI 页面展示真实截图/打印，指南不在浏览器运行仿真。演示输入为合成或公开脱敏样例，不代表真实 DUT 性能。私有源仓库的可见性没有改变；发布包只收录选定的演示产物和自有示例。

## 本地开发与构建

需要 Node.js 24（或满足 `package.json` 的版本）和 Python 3.11+。Python 用于文件与链接检查。

```bash
npm ci
npm run dev
```

```bash
npm test
npm run build
npm run check:site
npm run preview
```

`npm run build` 输出根路径版本，适用于 Cloudflare Pages；`npm run build:github` 输出 `/demo/` 版本，适用于 GitHub Pages。两种构建都会将独立演示文件复制到 `dist/`，保留原有 PVKit URL 和文件内容。`dist/` 与 `node_modules/` 不提交。

浏览器测试使用系统 Edge：先运行 `npm run preview -- --port 4321`，再运行 `npm run test:browser`。其他平台可在 `playwright.config.mjs` 中改用已安装的 Chromium。

## 目录与后续扩展

```text
src/pages/              Astro 导航与项目详情
src/components/         作品卡片、技术示意、图标
src/data/projects.json  项目、分类、演示入口和展示范围
src/styles/             Tailwind 与站点主题
public/                 favicon / Cloudflare headers
pvkit/                  独立演示包；其余六项各占同名目录
scripts/                站点构建、静态检查、演示重建
tests/                  筛选逻辑与真实浏览器测试
.github/workflows/      GitHub Pages 自动发布
```

增加项目时，在 `src/data/projects.json` 中登记信息，将演示放到独立顶级目录，并加入 `scripts/build-site.mjs` 的复制清单。示例重建脚本只负责对应项目，避免覆盖 Astro 导航与总 README。

各新项目的 `provenance.json` 记录固定源提交、原文件哈希和公开范围；PVKit 的 `manifest.json` 与 `SHA256SUMS` 记录 release 输入和全部静态文件校验。模板、字体与第三方库说明见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。

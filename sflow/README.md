# Sflow 交互组合与开发 tree 使用指南

[打开在线使用指南](https://techyan.github.io/demo/sflow/) · [操作 IP / tile / view / config 组合图](https://techyan.github.io/demo/sflow/#composition) · [完整离线 HTML 手册](https://techyan.github.io/demo/sflow/development-tree-guide.html)

页面沿用 TechYan demo 的 Astro Base、全局导航、项目卡片、深浅主题和部署方式。`src/pages/sflow/index.astro` 组织章节，`src/components/SflowComposition.astro` 提供交互组合图，目录与阶段数据在 `src/data/sflow-guide.mjs`。完整手册位于 `sflow/development-tree-guide.html`，可离线打开和打印。

## 交互组合图

- 从 PCIe、DMA、DNoC、RNoC、ATU、MC 六个样例 IP 中选择组合，查看对应 workspace、imports 与 publication。
- 选择 PCIe variant、增加第二个 PCIe 实例，观察同一 design_variant 的发布复用。
- 编辑兼容 bundle 的 master → slave 连接；未连接端点显式导出为顶层端口。
- 调整实例 tile 归属、增加自定义 tile、合并或按功能重新分区，观察同 tile / 跨 tile 连线与 assembly 更新。
- 切换 flat、partitioned、debug view 对应的 SoC config，查看 fileset、调试宏、构建命令和输出目录。
- 复制或下载 imports、project、两份 assembly 声明，填入真实 Git 来源与 ref 后在本地开发 tree 使用。

实际项目通过 imports 扩展组件库，依据各设计的清单、variant 与接口契约组合。依赖同步获取 checkout，build/publish 解析选中闭包并发布，BIA 根据 assembly 连接 block 和生成 tile 层次，config 通过 target/view 选择结构与 fileset。根平台锁选择整次构建的 runtime。

## 阅读路径

1. 准备本地依赖，创建并运行示例 SoC。
2. 用 Terminal tree 阅读 env / import / src / out。
3. 对比六 IP 直接集成与 io_subsys 集成。
4. 操作组件、连线、tile、view/config 组合，查看对应声明。
5. 区分 repo、design_variant、instance 与 feature 命名空间。
6. 沿 SC 的 publish → BIA → assembly → compile / lint → run 追踪输入输出。
7. 查找构建产物、节点 rerun、升级平台或覆盖本地 IP。

## 来源与边界

行为与手册基线为 TechYan/sflow 的 `829e8fbc24512062689dbbabf5e4576ff0925458`，参考其 README、docs/architecture.md、configuration.py、BIA、demo.py、flow.py、suites.py 和模板。完整 HTML 手册与该提交中的文件逐字节同步，摘要记录在 provenance.json。

浏览器编辑并展示配置，实际构建在本地通过 sflow / SC 执行。目录和输出是说明示例，动态路径按实际运行结果填写。样例 RTL 用于流程启动检查，项目的功能 stimulus、scoreboard 与协议验证按设计目标组织。

交互导出的七个构建场景已用真实 SC/Icarus 执行，debug config 的两个 seed 已通过。六 IP 的 64 种子集已通过当前配置解析及原生 BIA 的 flat / partitioned 两种结构检查。页面检查覆盖实际路由、深浅主题、手机布局和打印展开；原有 11 项站点浏览器回归通过。

公开内容包含使用说明、交互图和通用声明示例。实际运行需有可访问的平台与设计 Git 来源、uv 环境及 Icarus 工具。完整手册包含失败节点调试命令与环境恢复说明。

## 站点验证

```sh
npm ci
npm test
npm run build:github
python scripts/check_site.py dist /demo
```

指南组织参考 [SiliconCompiler User Guide](https://docs.siliconcompiler.com/en/stable/user_guide/index.html) 与 [FuseSoC User Guide](https://fusesoc.readthedocs.io/en/stable/user/index.html) 的入门、概念、任务式结构；图形和文字围绕 sflow 重新制作。

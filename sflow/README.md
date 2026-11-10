# Sflow user guide

[打开在线使用指南](https://techyan.github.io/demo/sflow/)

沿用 TechYan demo 的 Astro Base、全局导航、项目卡片、深浅主题和部署方式。页面由 `src/pages/sflow/index.astro` 生成，目录与阶段数据在 `src/data/sflow-guide.mjs`；交互脚本仅切换说明和复制文本。

## 阅读路径

1. 准备本地依赖，创建并运行示例 SoC。
2. 用 Terminal tree 阅读 env / import / src / out。
3. 对比六 IP 直接集成与 io_subsys 集成。
4. 区分 repo、design_variant、instance 与 feature 命名空间。
5. 沿 SC 的 publish → BIA → assembly → compile / lint → run 追踪输入输出。
6. 查找构建产物、升级平台或覆盖本地 IP。

## 来源与边界

行为基线：TechYan/sflow 的 `0906cbc27d8bbeb3a633b74ff288f787029a654f`，参考其 README、docs/architecture.md、src/sflowkit/demo.py、flow.py、suites.py 和模板。目录为保留真实路径的整理示意，省略辅助文件；命令块不是现场运行日志。本网页不执行仿真，不把启动检查当作 PCIe / DMA 功能验证。

公开页面只包含讲解、示意图和通用示例命令，不复制完整平台源码或本机运行产物。需要实际执行命令时，用户需已拥有 sflow checkout。

## 站点验证

```sh
npm ci
npm test
npm run build:github
python scripts/check_site.py dist /demo
```

指南组织参考 [SiliconCompiler User Guide](https://docs.siliconcompiler.com/en/stable/user_guide/index.html) 与 [FuseSoC User Guide](https://fusesoc.readthedocs.io/en/stable/user/index.html) 的入门、概念、任务式结构；图形和文字围绕 sflow 重新制作。

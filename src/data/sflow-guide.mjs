export const sections = [
  ['start', '快速开始'], ['tree', '读懂 SoC tree'], ['integration', '组合独立仓库'],
  ['composition', '交互 IP / tile / config'], ['variants', 'Variant 与 feature'], ['build', '构建如何发生'], ['bia', 'BIA 与层次连接'],
  ['outputs', '找到构建产物'], ['daily', '日常操作与升级']
];
export const socTree = `soc/                                     # 当前构建根
├── run.py                               # 稳定入口，启动锁定的 sflow
├── env/
│   ├── sync.py                          # 同步平台和设计依赖
│   ├── tree.json                        # 模板来源与入口基线
│   ├── platform.hjson                   # sflow 来源 / ref
│   ├── platform.lock.json               # sflow 的精确 commit
│   ├── imports.hjson                    # 设计依赖声明
│   └── imports.lock.json                # 完整设计闭包的 commit
├── import/                              # sync 后的独立 Git checkout
│   ├── sflow/                           # 本次构建唯一的 flow runtime
│   │   ├── src/sflowkit/
│   │   ├── platform.json
│   │   └── uv.lock
│   ├── pcie/                            # 同一源码可生成多个 variant
│   ├── dma/
│   ├── dnoc/
│   ├── rnoc/
│   ├── atu/
│   ├── mc/
│   ├── io_subsys/                       # pcie + dma + dnoc
│   ├── sharedlib/                       # FIFO、同步器等公共 RTL
│   └── common_info/                     # bundle 格式与公共定义
├── src/                                 # 项目自己维护的内容
│   ├── rtl/
│   ├── verif/
│   └── meta/
│       ├── build.py                     # VARIANTS / 生成器配方
│       ├── manifest/project.hjson       # targets、configs、filesets、suites
│       ├── interface/                   # 模块接口 / bundle sidecar
│       ├── connectivity/
│       │   ├── flat.hjson               # 直接集成六个 IP
│       │   ├── hier.hjson               # 通过 io_subsys 集成
│       │   └── multi_pcie.hjson         # 多 variant / tile 示例
│       ├── register/addresses.hjson     # SoC 分配最终地址
│       ├── assembly/                    # 保留的元数据分类目录
│       ├── feature/                     # 保留的元数据分类目录
│       └── fuse/
└── out/                                 # 构建后产生，不提交到 Git
    └── <os>/                            # 例如 linux / darwin
        ├── latest.json                  # 最新构建结果索引
        └── builds/<id>/                 # 每次构建独立目录
            ├── library/
            ├── connectivity/
            ├── config/
            ├── run/
            └── sc/`;
export const outputTree = `<build>/
├── plan.json                            # 解析后的 config / unit / 任务输入
├── provenance.json                      # 平台、设计 commit、override / dirty
├── features.json / features.svh          # 同一份 feature 快照
├── result.json                          # 阶段、case 与最终状态
├── library/
│   ├── pcie_rc_x16/                     # rc0、rc1 共用
│   │   ├── src/                         # 发布的静态 + 生成源码
│   │   ├── context.json
│   │   └── manifest.json
│   ├── pcie_ep_x16/
│   └── pcie_dm_x8/                      # 其余单元省略
├── addresses/                           # 根地址信息的生成物
├── connectivity/<design_variant>/<view>/
│   └── *.sv                             # BIA 顶层 / tile 连接代码
├── config/<config>/<view>/
│   ├── compile/
│   │   ├── rtl.f / sim.f / compile.f
│   │   ├── slang.f / metadata.json
│   │   └── replay.sh / sc/
│   └── lint/                            # lint 构建的日志 / include 审计
├── run/smoke/<execution>/
│   ├── startup_a/1/                     # case / seed
│   ├── startup_a/2/
│   └── startup_b/7/                     # 各自 command / log / 产物
└── sc/                                  # SC 原生任务与产物目录`;
export const platformTree = `sflow/
├── src/sflowkit/         # build / publish / BIA / assembly / compile / run / lint
│   └── templates/       # tree 骨架 + 按类型提供初始配置
├── references/{ip,soc}/ # 同一模板生成的可运行参考
├── agents/              # 架构约束、决策与维护工作流
└── tests/               # 平台及真实工具验证`;
export const createCommand = `# 在拥有 sflow checkout 的环境中；需要 Git、Python ≥3.11、uv、Icarus / vvp
cd /path/to/sflow
uv sync --locked
# 目标目录必须不存在；生成本地独立 Git 源仓库与开发 checkout
uv run --locked python scripts/create_demo.py /tmp/sflow-tour`;
export const startCommand = `cd /tmp/sflow-tour/workspaces/soc
python env/sync.py
python run.py list
python run.py sim --config multi_pcie
python run.py status`;
export const phases = [
  {id:'snapshot',name:'Snapshot',label:'冻结输入',title:'先确定这一次要构建什么',text:'构建根选择平台和设计闭包，解析 config、target、view、variant 及 typed feature。记录源码摘要与版本状态，后续阶段使用这一份输入。',input:'platform.lock + imports.lock + project.hjson',output:'plan.json · provenance.json · features.json',path:'out/<os>/builds/<id>/',hint:'本地覆盖不会伪装成正式锁定版本：路径、commit 与 dirty 状态都会进入 provenance。'},
  {id:'publish',name:'Publish',label:'按依赖并行',title:'每个 design_variant 发布自己的实现',text:'复制静态输入并执行项目 build.py 配方。Perl、Python、Ruby 等生成器可由配方调用。SC 依据显式 build dependencies 排序，无依赖单元可以并行发布。',input:'src/ + build(context) + 已解析 feature',output:'发布源码 · context.json · manifest.json',path:'library/<design_variant>/',hint:'不同 variant 使用不同目录和模块名。同 variant 的多个实例共享一份发布物。'},
  {id:'connect',name:'BIA',label:'生成连接层次',title:'从 bundle 端点生成顶层 DUT',text:'地址任务读取根的已发布地址定义。BIA 使用已发布接口和 assembly，校验连接并按声明生成 flat 或 tile 层次。父单元的 BIA 依赖子单元的生成结果。',input:'已发布 assembly / sidecar / bundle 定义',output:'顶层 .sv · tile .sv · 地址定义',path:'connectivity/<design_variant>/<view>/',hint:'这里的 assembly 是 BIA 硬件连接描述；下一阶段的 assembly 是编译输入组装，两者职责不同。'},
  {id:'assembly',name:'Assembly',label:'选择编译输入',title:'按 config / view 收集 fileset 和宏',text:'组合发布物、连接 RTL、地址定义与 feature 宏，按 fileset 依赖组织编译顺序。使用明确的文件路径与元数据，不依赖每个 library 对应一个环境变量。',input:'library + connectivity + filesets + features',output:'compile.f · slang.f · metadata.json · replay.sh',path:'config/<config>/<view>/compile/',hint:'工艺库、SRAM 等可通过 external_files / external_include_dirs 声明，不复制，但记录实际输入摘要。'},
  {id:'compile',name:'Compile / lint',label:'实际工具检查',title:'编译与 lint 消费相同的发布契约',text:'build / sim 使用 Icarus 编译；lint 使用 Slang 进行语法、展开和基础诊断。两个前端各自审计实际源码与 include 闭包；lint 错误失败，warning 报告。',input:'组装后的文件列表与工具参数',output:'.vvp image 或 lint 日志 / 审计',path:'config/<config>/<view>/compile/ 或 lint/',hint:'这是两个可选择的分支，lint 不会附带执行仿真。无 top 的公共库默认只进行 snapshot / publish。'},
  {id:'run',name:'Run',label:'按 case 隔离',title:'编译一次，分开运行每个 case / seed',text:'suite 选择 plusargs、seed、超时与成功标志。每次 execution 及其 case / seed 拥有独立目录；非零退出、错误诊断、超时或缺少成功标志都会失败。',input:'已编译 image + suite 运行参数',output:'每个 case 的命令、日志与结果',path:'run/<suite>/<execution>/<case>/<seed>/',hint:'重跑先校验 image 摘要，不重新生成或编译。改变编译配置需要新建 build。'}
];

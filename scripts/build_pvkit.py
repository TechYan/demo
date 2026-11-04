"""Build the static PVKit gallery from the unchanged xpvkit 0.5.5 release ZIP."""
from __future__ import annotations

import argparse
import hashlib
import html
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import zipfile

VERSION = '0.5.5'
RELEASE_SHA256 = 'c3cddb9de23104ad8be9db2f564f2a3c721a42dfdbb575bd336eda093b2533cd'
BASE_URL = 'https://techyan.github.io/demo/'
ROOT = Path(__file__).resolve().parents[1]
SCENARIOS = [
    ('axi4', 'read_only', '只读流量', '观察 AR/R 关联、读带宽与请求到响应延迟。'),
    ('axi4', 'write_only', '只写流量', '观察 AW/W/B 关联、写带宽与写响应。'),
    ('axi4', 'concurrent', '并发读写', '在同一时间轴比较读写带宽、outstanding 和通道背压。'),
    ('axi4', 'bandwidth_steps', '阶梯带宽', '观察负载分阶段变化及有效数据窗口。'),
    ('axi4', 'mixed_metrics', '混合指标', '检查 WSTRB、Partial write、延迟与背压。'),
    ('axi4', 'high_outstanding', '高并发请求', '观察 1024 outstanding 场景的趋势与事务查询。'),
    ('axi4', 'incomplete_response', '响应未完成', '诊断示例：保留缺失响应、未完成事务及已观察证据。'),
    ('cxl_native', 'full_duplex', '全双工流量', '比较 M2S/S2M 消息、双向带宽与事务关联。'),
    ('cxl_native', 'reinitialize', '突发与重新初始化', '观察独立初始化域、突发流量与重新初始化。'),
    ('cxl_native', 'read_credit_throttle', '读 credit 限流', '观察读方向各 channel/slot 记录到的 credit EMPTY 区间。'),
    ('cxl_native', 'write_credit_throttle', '写 credit 限流', '观察写方向 credit EMPTY 与消息发送的时间关系。'),
    ('cxl_native', 'repeated_empty', '同一 slot 反复 EMPTY', '观察同一个物理 slot 多次耗尽与恢复。'),
    ('cxl_native', 'staggered_slots', '交错与重叠 EMPTY', '展开各 slot，检查交错和重叠耗尽区间。'),
    ('cxl_native', 'independent_channels', '独立 channel 反复 EMPTY', '检查四条读写 channel 的独立耗尽模式。'),
    ('cxl_native', 'short_pulses', '长时间域中的短脉冲', '缩放长 capture，检查短 credit EMPTY 脉冲。'),
]


def write(path, content):
    path = ROOT / path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding='utf-8', newline='\n')


def page(title, body, prefix=''):
    return f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title><link rel="stylesheet" href="{prefix}assets/site.css"></head>
<body><main>{body}<footer>PVKit demo · xpvkit {VERSION} · 合成示例数据</footer></main></body></html>'''


class TerminalCapture(io.StringIO):
    encoding = 'utf-8'

    def __init__(self, columns):
        super().__init__()
        self.columns = columns

    def isatty(self):
        return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--release', type=Path, required=True)
    args = parser.parse_args()
    archive_path = args.release.resolve()
    assert hashlib.sha256(archive_path.read_bytes()).hexdigest() == RELEASE_SHA256, 'Release SHA256 mismatch'
    from rich.console import Console
    from rich.text import Text
    from rich.terminal_theme import MONOKAI

    with tempfile.TemporaryDirectory(prefix='.pvkit-build-', dir=ROOT) as temporary:
        tool_path = Path(temporary) / 'xpv.pyz'
        with zipfile.ZipFile(archive_path) as archive:
            tool_path.write_bytes(archive.read('xpv.pyz'))
            assert hashlib.sha256(tool_path.read_bytes()).hexdigest() == 'a67370373fc5cab5b6bf5f8a46227e5dc96d642238bce329b37dfdf95d3b5eef'
            sys.path.insert(0, str(tool_path))
            from xpvlib import __version__
            from xpvlib.analyze import analyze_and_write, format_summary, write_html
            from xpvlib.terminal import print_report
            assert __version__ == VERSION
            os.chdir(ROOT)
            os.environ.pop('NO_COLOR', None)
            os.environ['TERM'] = 'xterm-256color'
            os.environ['FORCE_COLOR'] = '1'
            manifest = {'tool': 'xpvkit', 'version': VERSION, 'release_tag': 'v' + VERSION,
                        'release_sha256': RELEASE_SHA256, 'window': 'auto',
                        'report_mode': 'full', 'trend': 'all',
                        'data': 'synthetic demo, not measured DUT performance', 'scenarios': []}
            for protocol, slug, title, description in SCENARIOS:
                source = f'examples/{protocol}/{slug}/traffic.csv'
                folder = Path('pvkit') / source.removesuffix('/traffic.csv')
                folder.mkdir(parents=True, exist_ok=True)
                raw = archive.read(source)
                csv = folder / 'traffic.csv'
                csv.write_bytes(raw)
                result, report_path = analyze_and_write(csv, window='auto', report_mode='full', trend='all')
                assert result.get('protocol', 'axi4') in {'axi', 'axi4', 'cxl_native'}, result.get('protocol')
                # The release resolves output paths; make published artifacts portable.
                for key, value in result.get('artifacts', {}).items():
                    result['artifacts'][key] = Path(value).resolve().relative_to(ROOT).as_posix()
                result['path'] = csv.as_posix()
                log_path = folder / 'traffic.analyze.log'
                log_text = log_path.read_text(encoding='utf-8')
                log_text = log_text.replace(str(ROOT) + os.sep, '')
                for artifact in result['artifacts'].values():
                    log_text = log_text.replace(artifact.replace('/', os.sep), artifact)
                write(log_path, log_text)
                write_html(result, report_path)
                panels = []
                for width in (120, 80, 60):
                    for mode in ('standard', 'full', 'compact'):
                        stream = TerminalCapture(width)
                        print_report(format_summary(result), result, report_path.as_posix(),
                                     stream=stream, report_mode=mode, trend='all')
                        ansi = stream.getvalue()
                        plain = Text.from_ansi(ansi).plain
                        assert '\x1b' not in plain
                        capture = folder / 'captures' / f'{mode}.{width}'
                        write(str(capture) + '.txt', plain)
                        write(str(capture) + '.ansi', ansi)
                        console = Console(file=io.StringIO(), record=True, width=width, highlight=False)
                        console.print(Text.from_ansi(ansi), end='')
                        colored = console.export_html(inline_styles=True, theme=MONOKAI, code_format='{code}')
                        hidden = '' if (mode, width) == ('standard', 120) else ' hidden'
                        panels.append(f'<div class="panel" data-mode="{mode}" data-width="{width}"{hidden}><pre>{colored}</pre></div>')
                name = ('AXI4' if protocol == 'axi4' else 'CXL Native') + ' · ' + title
                command = f'python xpv.pyz analyze {csv.as_posix()}'
                body = f'''<nav><a href="../../../index.html">← PVKit 场景目录</a></nav>
<h1>{html.escape(name)}</h1><div class="eyebrow">ACTUAL TUI CAPTURE · XPVKIT {VERSION}</div>
<p>{html.escape(description)} 以下内容由同一份 CSV 经 release 工具实际打印，网页仅回放终端输出。</p>
<div class="links"><a href="traffic.pv.html">交互 HTML 报告</a><a href="traffic.analyze.log">分析日志</a><a href="traffic.tracker.log">Tracker 日志</a><a href="traffic.csv" download>原始 CSV</a></div>
<div class="controls"><label>报告模式 <select id="mode"><option value="standard">standard / 概览</option><option value="full">full / 协议详情</option><option value="compact">compact / 摘要</option></select></label>
<label>终端列数 <select id="width"><option>120</option><option>80</option><option>60</option></select></label></div>
<div class="terminal">{''.join(panels)}</div>
<div class="links"><a id="txt" href="captures/standard.120.txt">当前输出纯文本</a><a id="ansi" href="captures/standard.120.ansi" download>下载 ANSI</a></div>
<p>使用已有的 xpvkit {VERSION} 工具，从仓库根目录复现（Rich 为彩色 TUI 的可选依赖）：</p>
<pre class="command" id="command">{html.escape(command)} --report-mode standard --trend all</pre>
<p>默认带宽按实际数据活动窗口计算；事务、延迟与诊断保留完整 capture 范围。TUI 是输出式报告，鼠标选窗与事务查询请打开交互 HTML。</p>'''
                document = page(name + ' · TUI', body, '../../../../')
                document = document.replace('<body>', '<body data-command="' + html.escape(command, quote=True) + '">')
                document = document.replace('</body>', '<script src="../../../../assets/tui.js"></script></body>')
                write(folder / 'tui.html', document)
                manifest['scenarios'].append({'protocol': protocol, 'slug': slug, 'title': title,
                    'description': description, 'source': source,
                    'source_sha256': hashlib.sha256(raw).hexdigest(), 'directory': folder.as_posix()})
                print(f'{protocol}/{slug}: HTML, tracker, analyze log, 9 TUI captures', flush=True)

    write('pvkit/manifest.json', json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    body = '''<nav><a href="../index.html">← Demo 首页</a> · <a href="https://github.com/TechYan/demo/tree/main/pvkit">GitHub 文件目录</a></nav>
<h1>PVKit 示例</h1><div class="eyebrow">AXI4 · CXL NATIVE · XPVKIT 0.5.5</div>
<p>15 个 release 场景：7 个 AXI4、8 个 CXL Native。直接打开 HTML 报告，回放真实 TUI 打印，或查看可复制的分析与 tracker 日志。所有页面和数据均为静态文件，无需安装工具。</p>
<p class="note">数据为合成示例，不代表真实 DUT 性能。响应未完成场景有预期诊断。CXL 的 EMPTY 仅表示记录到的耗尽区间，未记录部分保持 UNKNOWN。</p>
<div class="links"><a href="README.md">使用说明</a><a href="manifest.json">版本与 CSV 来源校验</a></div>'''
    readme = f'''# PVKit demo

**[打开在线示例目录]({BASE_URL}pvkit/)** · [返回 demo 仓库](../README.md)

收录 xpvkit **{VERSION}** release 中的 **15 个合成场景**：7 个 AXI4、8 个 CXL Native。
每个场景均提供交互 HTML、实际 TUI 打印、分析日志、完整 tracker 和原始 CSV。
无需安装 Python 或下载工具即可通过下表直接浏览。数据不代表真实 DUT 性能。

## 在线浏览

'''
    for protocol, label in [('axi4', 'AXI4'), ('cxl_native', 'CXL Native')]:
        body += f'<section id="{protocol}"><h2>{label}</h2><div class="grid">'
        readme += f'### {label}\n\n| 场景 | 观察重点 | HTML | TUI 打印 | 分析日志 | Tracker | CSV |\n|---|---|---|---|---|---|---|\n'
        for rec in manifest['scenarios']:
            if rec['protocol'] != protocol:
                continue
            path = f'examples/{protocol}/{rec["slug"]}/'
            body += f'''<article class="card"><div class="tag">{html.escape(rec['slug'])}</div><h3>{html.escape(rec['title'])}</h3><p>{html.escape(rec['description'])}</p><div class="links"><a href="{path}traffic.pv.html">HTML 报告 →</a><a href="{path}tui.html">TUI 打印 →</a><a href="{path}traffic.analyze.log">分析日志</a><a href="{path}traffic.tracker.log">Tracker</a><a href="{path}traffic.csv" download>CSV</a></div></article>'''
            public = BASE_URL + 'pvkit/' + path
            readme += f'| {rec["title"]} | {rec["description"]} | [打开]({public}traffic.pv.html) | [打开]({public}tui.html) | [查看]({public}traffic.analyze.log) | [查看]({public}traffic.tracker.log) | [下载]({public}traffic.csv) |\n'
        body += '</div></section>'
        readme += '\n'
    readme += '''## 如何阅读

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
'''
    write('pvkit/index.html', page('PVKit · AXI4 / CXL Native 示例', body, '../'))
    write('pvkit/README.md', readme)
    write('index.html', page('TechYan Demo', '''<div class="eyebrow">TECHYAN / DEMO</div><h1>Demo 目录</h1>
<p>按项目浏览可直接打开的演示。每个项目使用独立目录，后续示例从这里进入。</p>
<div class="grid"><article class="card"><div class="tag">PVKIT · XPVKIT 0.5.5</div><h2>总线性能与协议分析</h2><p>15 个 AXI4 / CXL Native 场景，包含交互 HTML、真实 TUI 打印、分析日志与 tracker。</p><div class="links"><a href="pvkit/">打开 PVKit →</a><a href="https://github.com/TechYan/demo/tree/main/pvkit">查看文件</a></div></article></div>'''))
    write('README.md', f'''# Demo

**[打开在线 Demo 首页]({BASE_URL})**

本仓库按项目保存可直接浏览的演示；每个项目有独立目录、说明和网页入口，方便后续加入其他 demo。

| 项目 | 内容 | 在线访问 | 说明与文件 |
|---|---|---|---|
| PVKit | 7 个 AXI4、8 个 CXL Native 场景：交互 HTML、TUI 打印、分析日志、Tracker 和原始 CSV | [打开场景目录]({BASE_URL}pvkit/) | [PVKit README](pvkit/README.md) · [示例文件](pvkit/examples/) |

## 快速开始

1. 打开 [PVKit 场景目录]({BASE_URL}pvkit/)，选择感兴趣的 AXI4 或 CXL Native 场景。
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
''')
    checksums = []
    for path in sorted((ROOT / 'pvkit').rglob('*')):
        if path.is_file() and path.name != 'SHA256SUMS':
            checksums.append(f'{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.relative_to(ROOT / "pvkit").as_posix()}')
    write('pvkit/SHA256SUMS', '\n'.join(checksums) + '\n')
    print(f'Built {len(SCENARIOS)} scenarios; {len(checksums)} static PVKit files verified from release {VERSION}.')


if __name__ == '__main__':
    main()

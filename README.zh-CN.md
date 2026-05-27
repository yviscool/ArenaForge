[English](README.md) | [简体中文](README.zh-CN.md) | [日本語](README.ja.md) | [한국어](README.ko.md) | [Русский](README.ru.md)

# ArenaForge

[![CI](https://github.com/yviscool/ArenaForge/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/yviscool/ArenaForge/actions/workflows/ci.yml)

ArenaForge 是一个给 Sublime Text 使用的竞赛编程一体化工作台。
它把本地运行、样例管理、比赛工作区初始化、格式化、C++ 诊断、对拍和 Codeforces 提交放进同一个包里。

## 快速入口

- [快速上手](docs/QUICKSTART.zh-CN.md)
- [架构说明](docs/ARCHITECTURE.md)
- [Sublime 壳层迁移说明](docs/SUBLIME_SHELL_MIGRATION.md)

## 它能做什么

- 在独立的测试面板里运行当前文件。
- 把测试和会话快照存成靠近源码树的 JSON 文件。
- 对比程序输出与期望答案，并标出第一个不匹配的位置。
- 在运行面板里保留输入历史和类终端编辑操作。
- 从 OJ 链接初始化比赛或单题工作区。
- 初始化比赛前先选择目标语言。
- 在 ArenaForge 内部对支持的语言直接做格式化。
- 通过 `lint_compile_cmd` 显示 C++ 诊断标记。
- 使用 `<task>__Good` 和 `<task>__Generator` 做对拍。
- 通过 `keyring` 保存凭据并直接提交 Codeforces。
- 为当前文件或整个工作区生成 formatter 配置文件。

## 语言支持

### 运行 / 比赛模板

| 语言 | 运行 | 比赛模板 | formatter |
| --- | --- | --- | --- |
| C | 支持 | 支持 | `clang-format` |
| C++ | 支持 | 支持 | `clang-format` |
| Python | 支持 | 支持 | `ruff format` |
| Java | 支持 | 支持 | `google-java-format` |
| Kotlin | 支持 | 支持 | `ktfmt` |
| Go | 支持 | 支持 | `gofmt` |
| Rust | 支持 | 支持 | `rustfmt` |
| JavaScript | 支持 | 支持 | `oxfmt` |

### 仅格式化支持

通过 `oxfmt`，ArenaForge 还支持这些常见文本 / Web 文件的格式化：

- TypeScript / TSX
- JSON / YAML / TOML
- HTML / Vue / Svelte
- CSS / SCSS / Less
- Markdown / MDX
- GraphQL

## Provider 支持

| Provider | 工作区初始化 | 提交 |
| --- | --- | --- |
| Codeforces | 比赛工作区，自动抓取样例 | 支持 |
| AtCoder | 比赛工作区，自动抓取样例 | 暂不支持 |
| Luogu | 单题工作区 | 暂不支持 |
| AcWing | 单题工作区 | 暂不支持 |

Codeforces 提交需要 `requests` 和可用的 `keyring` 后端。
仓库里的 `dependencies.json` 已声明 `requests`。

## 安装

### 普通安装

1. 把这个目录放到 Sublime Text 的 `Packages/` 目录下。
2. 外层包目录名保持为 `ArenaForge`。
3. 重启 Sublime Text，或者执行 `Tools -> Developer -> Reload Plugins`。
4. 打开命令面板，运行 `ArenaForge: Open Settings`。

你仍然需要本地装好要用到的编译器和 formatter，例如 `g++`、`python`、`javac`、`ruff`、`rustfmt`。

### Windows 开发连接

本地开发时，推荐用 junction，而不是手动复制目录到 `Packages/`。
这样 Sublime 会直接指向你的工作树，不会保留过期副本。

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\link_sublime_package.ps1
```

按你当前环境，这会创建：

```text
C:\software\Sublime Text 4\Data\Packages\ArenaForge
-> C:\Users\Administrator\Desktop\manage_svn\sub\arena_forge
```

## 命令

### 运行 / 比赛

- `ArenaForge: Run`
- `ArenaForge: Setup Contest`
- `ArenaForge: Submit`
- `ArenaForge: Configure Credentials`
- `ArenaForge: Doctor`
- `ArenaForge: Run History`

### 格式化

- `ArenaForge: Format`
- `ArenaForge: Format Document`
- `ArenaForge: Format Selection`
- `ArenaForge: Diagnose Formatter`
- `ArenaForge: Formatter Install Guide`
- `ArenaForge: Create Format Config For Current File`
- `ArenaForge: Create Workspace Format Configs`

## 推荐工作流

1. 如果你在本地开发，先用 junction 脚本把包连到 Sublime。
2. 个性化覆盖只写在 `Packages/User/ArenaForge.sublime-settings`。
3. 打开 `A.cpp`、`main.py` 或 `Main.java` 这类源文件。
4. 运行 `ArenaForge: Run`，在右侧面板维护测试。
5. 需要时运行 `ArenaForge: Format`，或者开启 `format_on_save`。
6. 需要建比赛目录时运行 `ArenaForge: Setup Contest`。
7. 在比赛初始化面板里选择目标语言。
8. 调整过编译器或 formatter 路径后，跑一次 `ArenaForge: Doctor`。

具体的 C++ / Python / Java 例子见 [快速上手](docs/QUICKSTART.zh-CN.md)。

## 用户配置

主设置文件是仓库自带的 `ArenaForge.sublime-settings`。
你自己的覆盖配置应该放到：

```text
Packages/User/ArenaForge.sublime-settings
```

最佳实践：

- 用户配置只放“个人路径”和“工作流开关”。
- 风格规则尽量写到项目原生配置文件里，例如 `.clang-format`、`pyproject.toml`、`rustfmt.toml`。
- `formatting.commands` 用来写本机 formatter 路径或完整命令前缀。
- 不要把超长 formatter 风格定义直接塞进编辑器设置。

示例：

```json
{
  "preferred_locale": "zh-Hans",
  "default_contest_language": "cpp",
  "close_sidebar": false,
  "formatting": {
    "format_on_save": true,
    "commands": {
      "clang-format": [
        "C:/Program Files/LLVM/bin/clang-format.exe"
      ]
    }
  }
}
```

### Formatter 补充说明

- Java / Kotlin formatter 也会自动发现项目里的 `tools/google-java-format.jar` 和 `tools/ktfmt.jar`。
- 如果 JAR 放在别的位置，再用 `formatting.commands` 显式写 `["java", "-jar", "..."]`。

## 关键设置项

- `default_contest_language`：`Setup Contest` 时默认高亮的语言
- `run_settings`：运行 / 编译 / 模板行为对应的语言档案
- `formatting.format_on_save`：保存前同步格式化
- `formatting.commands`：本机 formatter 命令前缀
- `formatting.extra_args`：formatter 运行参数
- `submission_language_ids`：不同 provider 的提交语言 ID 映射
- `stress_time_limit_seconds`：对拍超时时间
- `tests_relative_dir`、`session_relative_dir`、`tests_file_suffix`：测试与快照存储布局

## 排错

### 没有 C++ 红框或错误标记

ArenaForge 目前只对 C++ 做内联诊断标记。

先检查：

- `lint_enabled` 是否为 `true`
- 当前文件是不是受支持的 C++ 扩展名，例如 `.cpp`
- C++ 的 `run_settings` 里是否还保留了有效的 `lint_compile_cmd`
- Sublime 当前环境里是否能调用 `g++`
- 改完设置后是否执行了 `Reload Plugins`

必要时运行：

- `ArenaForge: Doctor`
- `Tools -> Developer -> Reload Plugins`

### 格式化命令没有效果

先检查：

- 当前语法是否被某个 formatter adapter 识别
- formatter 是否在 `PATH` 中，或者已经写进 `formatting.commands`，或者对 Java / Kotlin 来说项目里已经有 `tools/google-java-format.jar` / `tools/ktfmt.jar`
- 当前不是某个不支持选区格式化的语言/模式

可以运行 `ArenaForge: Diagnose Formatter` 查看匹配到的 adapter、命令和配置文件搜索结果。

### 比赛工作区生成成了错误的语言

先检查：

- 你在 `ArenaForge: Setup Contest` 里选了什么语言
- 用户配置里的 `default_contest_language` 是什么

## 项目结构

- `arena_forge/core`：类型化领域模型、输出比对、会话用例
- `arena_forge/adapters`：Sublime 集成、provider、存储、runner、i18n、工作区脚手架、凭据存储
- `arena_forge/formatting`：formatter adapter、可执行文件发现、配置生成和格式化运行时
- `arena_forge/templates`：内置比赛模板
- `tests`：覆盖 provider、存储、设置、运行面板行为和格式化的 pytest 测试
- `docs`：架构、迁移说明和快速上手文档

## 开发

- Python：`3.8+`
- 依赖管理：`uv`
- 运行时依赖：`keyring`

本地检查：

```bash
uv sync --group dev
uv run ruff check arena_forge tests
uv run pytest -q
uv run mypy
```

## 致谢

这个项目的思路和工作流来自 [FastOlympicCoding](https://github.com/Jatana/FastOlympicCoding) by Jatana。

当前代码库仍然面向竞赛编程场景，但实现已经重组为类型化核心、可移植 JSON 存储、集成格式化能力，以及更清晰的 Sublime 适配层。

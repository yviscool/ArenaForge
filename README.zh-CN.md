[English](README.md) | [简体中文](README.zh-CN.md) | [日本語](README.ja.md) | [한국어](README.ko.md) | [Русский](README.ru.md)

# ArenaForge

[![CI](https://github.com/yviscool/ArenaForge/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/yviscool/ArenaForge/actions/workflows/ci.yml)

ArenaForge 是一个给 Sublime Text 用的竞赛编程工作台。它把本地运行、样例管理、比赛建站、格式化、C++ 诊断、对拍和 Codeforces 提交放在一个包里。

## 快速入口

- [快速上手](docs/QUICKSTART.zh-CN.md)
- [配置说明](docs/CONFIGURATION.md)
- [PCH 流程](docs/PCH.md)
- [架构说明](docs/ARCHITECTURE.md)
- [Sublime 壳层迁移说明](docs/SUBLIME_SHELL_MIGRATION.md)

## 能做什么

- 在独立的测试面板里运行当前文件。
- 把测试和会话快照存成靠近源代码树的 JSON 文件。
- 对比程序输出和期望答案，并标出第一个不匹配位置。
- 在运行面板里保留输入历史和类终端编辑操作。
- 从支持的 OJ 链接生成比赛或单题工作区。
- 初始化比赛前先选择目标语言。
- 在 ArenaForge 内部对支持的语言直接做格式化。
- 通过 `lint_compile_cmd` 显示 C++ 诊断标记。
- 使用 `<task>__Good` 和 `<task>__Generator` 做对拍。
- 通过 `keyring` 保存凭据，并直接从 Sublime Text 提交 Codeforces。
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

ArenaForge 还通过 `oxfmt` 支持这些常见文本 / Web 格式：

- TypeScript / TSX
- JSON / YAML / TOML
- HTML / Vue / Svelte
- CSS / SCSS / Less
- Markdown / MDX
- GraphQL

## Provider 支持

| Provider | 工作区初始化 | 提交 |
| --- | --- | --- |
| Codeforces | 带样例的比赛工作区 | 支持 |
| AtCoder | 带样例的比赛工作区 | 暂不支持 |
| Luogu | 单题工作区 | 暂不支持 |
| AcWing | 单题工作区 | 暂不支持 |

Codeforces 提交需要 `requests` 和可用的 `keyring` 后端。仓库里已经在 `dependencies.json` 声明了 `requests`。

## 安装

### 常规安装

1. 把这个目录放到 Sublime Text 的 `Packages/` 目录下。
2. 外层包目录名保持为 `ArenaForge`。
3. 重启 Sublime Text，或者执行 `Tools -> Developer -> Reload Plugins`。
4. 打开命令面板，运行 `ArenaForge: Open Settings`。

你仍然需要本地安装要用到的编译器和 formatter，比如 `g++`、`python`、`javac`、`ruff`、`rustfmt`。

### Windows 开发链接

本地开发时，建议用 junction 连接仓库，而不是手动复制到 `Packages/`。

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\link_sublime_package.ps1
```

## 命令

### 运行 / 比赛

- `ArenaForge: Run`
- `ArenaForge: Setup Contest`
- `ArenaForge: Submit`
- `ArenaForge: Configure Credentials`
- `ArenaForge: Doctor`
- `ArenaForge: Run History`

Windows 默认把 `Ctrl+Alt+B` 绑定到 `ArenaForge: Run`。

### 格式化

- `ArenaForge: Format`
- `ArenaForge: Format Document`
- `ArenaForge: Format Selection`
- `ArenaForge: Diagnose Formatter`
- `ArenaForge: Formatter Install Guide`
- `ArenaForge: Create Format Config For Current File`
- `ArenaForge: Create Workspace Format Configs`

## 推荐流程

1. 本地开发时先用 junction 脚本把包连到 Sublime。
2. 个人覆盖只写在 `Packages/User/ArenaForge.sublime-settings`。
3. 打开 `A.cpp`、`main.py` 或 `Main.java` 这类源文件。
4. 运行 `ArenaForge: Run`，在右侧运行面板里维护测试。
5. 需要时运行 `ArenaForge: Format`，或开启 `format_on_save`。
6. 需要新比赛目录时运行 `ArenaForge: Setup Contest`。
7. 在比赛初始化面板里选择目标语言。
8. 调整编译器或 formatter 路径后运行 `ArenaForge: Doctor`。

## 用户设置

主设置文件是仓库自带的 `ArenaForge.sublime-settings`。你的个人覆盖应该放在：

```text
Packages/User/ArenaForge.sublime-settings
```

建议：

- 用户设置只放个人路径和工作流开关。
- 语言特定的风格规则放在 `.clang-format`、`pyproject.toml`、`rustfmt.toml` 等项目文件里。
- `formatting.commands` 用来写本机的 formatter 路径或命令前缀。
- 不要把超长的 formatter 风格配置直接塞进编辑器设置。

示例：

```json
{
  "preferred_locale": "zh-Hans",
  "default_contest_language": "cpp",
  "close_sidebar": false,
  "language_profiles": {
    "profiles": {
      "cpp": {
        "compile_cmd": "g++ \"{source_file}\" -std=c++14 -g -Wall -Winvalid-pch -finput-charset=UTF-8 -fexec-charset=UTF-8 -o \"{source_file_dir}\\\\{file_name}.exe\"",
        "lint_compile_cmd": "g++ -std=c++14 -g -Wall -fsyntax-only -fdiagnostics-color=never -Winvalid-pch -finput-charset=UTF-8 -fexec-charset=UTF-8 \"{source_file}\" -I \"{source_file_dir}\""
      }
    },
    "order": ["c", "cpp", "python", "java", "kotlin", "go", "rust", "javascript"]
  },
  "formatting": {
    "format_on_save": true,
    "commands": {
      "clang-format": ["C:/Program Files/LLVM/bin/clang-format.exe"]
    }
  }
}
```

### Formatter 补充

- Java / Kotlin formatter 会自动查找项目里的 `tools/google-java-format.jar` 和 `tools/ktfmt.jar`。
- 如果 JAR 放在别处，就在 `formatting.commands` 里显式写成 `["java", "-jar", "..."]`。

## 关键设置

- `default_contest_language`：`Setup Contest` 时默认高亮的语言
- `language_profiles`：按顺序排列的语言配置
- `formatting.format_on_save`：保存前同步格式化
- `formatting.commands`：本机 formatter 命令前缀
- `formatting.extra_args`：formatter 额外参数
- `formatting.selector_overrides`：按 scope 覆盖 formatter 选择
- `submission_language_ids`：各 provider 的提交语言 ID 映射
- `stress_time_limit_seconds`：对拍超时时间
- `tests_relative_dir`、`session_relative_dir`、`tests_file_suffix`：测试与会话快照存储位置

## 排错

### 没有 C++ 红框或错误标记

ArenaForge 目前只对 C++ 做内联诊断标记。

先检查：

- `lint_enabled` 是 `true`
- 当前文件是受支持的 C++ 扩展名，比如 `.cpp`
- `language_profiles.profiles.cpp.lint_compile_cmd` 还有效
- 当前 Sublime 环境里能调用 `g++`
- 改完设置后重新加载了插件

如果你使用 `bits/stdc++.h`，请先生成匹配的 `.gch`：

```bash
bash scripts/pch.sh
```

需要时再执行：

- `ArenaForge: Doctor`
- `Tools -> Developer -> Reload Plugins`

### 格式化没有生效

先检查：

- 当前语法是否被某个 formatter adapter 支持
- formatter 是否在 `PATH` 里，或已写入 `formatting.commands`
- Java / Kotlin 是否能找到 `tools/google-java-format.jar` / `tools/ktfmt.jar`
- 当前不是某个不支持的选区格式化模式

可运行 `ArenaForge: Diagnose Formatter` 查看匹配到的 adapter、命令和配置路径。

### 比赛工作区语言不对

先检查：

- 你在 `ArenaForge: Setup Contest` 里选了什么语言
- 用户设置里的 `default_contest_language`

## 项目结构

- `arena_forge/core`：类型化领域模型、输出对比、会话用例
- `arena_forge/adapters`：Sublime 集成、provider、存储、runner、i18n、工作区脚手架、凭据存储
- `arena_forge/formatting`：formatter adapter、可执行文件发现、配置生成和格式化运行时
- `arena_forge/templates`：内置比赛模板
- `tests`：provider、存储、设置、运行面板行为和格式化的 pytest 测试
- `docs`：架构、迁移说明和快速上手文档

## 开发

- Python: `3.8+`
- 依赖管理: `uv`
- 运行时依赖: `keyring`

本地检查：

```bash
uv sync --group dev
uv run ruff check arena_forge tests
uv run pytest -q
uv run mypy
```

## 致谢

这个项目的思路和工作流来自 [FastOlympicCoding](https://github.com/Jatana/FastOlympicCoding)。

现在的代码库仍然面向竞赛编程，但实现已经重组为类型化内核、可移植 JSON 存储、集成格式化能力，以及更清晰的 Sublime 适配层。

[English](README.md)

# ArenaForge

[![CI](https://github.com/yviscool/ArenaForge/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/yviscool/ArenaForge/actions/workflows/ci.yml)

ArenaForge 是一个给 Sublime Text 使用的竞赛编程工具。
它围绕日常写题最核心的几件事来设计：打开源码、快速运行、整理样例，并且直接从题目链接或比赛链接生成干净的工作区。

整个流程尽量留在编辑器里完成。
运行历史、对拍、诊断、模板插入、比赛初始化和 Codeforces 提交，都放在同一套工作界面里。

## 它能做什么

- 在独立的测试面板里运行当前文件。
- 把样例测试和更完整的会话快照存成靠近源码树的 JSON 文件。
- 对比程序输出与期望答案，并给出第一个不匹配的位置。
- 在运行面板里保留交互输入历史，并提供基础的类终端编辑操作。
- 为当前源文件提供独立的测试编辑视图和运行历史视图。
- 从 Codeforces、AtCoder、Luogu、AcWing 链接初始化比赛或单题工作区。
- 直接在 Sublime Text 里提交 Codeforces 代码，凭据通过 `keyring` 保存。
- 使用 `<task>__Good` 和 `<task>__Generator` 做对拍。
- 插入本地算法模板，并提供轻量的 C++ 补全辅助。
- 用 `lint_compile_cmd` 做 C++ 诊断。
- 通过 `Doctor` 命令检查包文件、资源、运行配置和凭据后端是否可用。

## 当前 Provider 支持

| Provider | 工作区初始化 | 提交 |
| --- | --- | --- |
| Codeforces | 比赛工作区，自动抓取样例 | 支持 |
| AtCoder | 比赛工作区，自动抓取样例 | 暂不支持 |
| Luogu | 单题工作区 | 暂不支持 |
| AcWing | 单题工作区 | 暂不支持 |

Codeforces 提交需要 `requests` 和可用的 `keyring` 后端。
仓库里的 `dependencies.json` 已声明 `requests`。

## 项目结构

- `arena_forge/core`：类型化领域模型、输出比对、会话用例
- `arena_forge/adapters`：Sublime 集成、provider、存储、runner、i18n、工作区脚手架、凭据存储
- `tests`：覆盖 provider、存储、设置、运行面板行为和命令面的 pytest 测试
- `docs`：架构、迁移和国际化说明
- 仓库根目录：Sublime 包资源，例如快捷键、语法文件、HTML 渲染资源、图标、调试桥接模块，以及薄封装命令

## 安装

1. 把这个目录放到 Sublime Text 的 `Packages/` 目录下。
2. 如果是手动安装，建议把外层包目录重命名为 `ArenaForge`。
3. 重启 Sublime Text。
4. 打开命令面板，运行 `ArenaForge: Open Settings`。

你还需要本地可用的语言工具链，例如 `g++`、`python` 或 `javac`。

## 基本流程

1. 打开一个源文件，例如 `A.cpp` 或 `main.py`。
2. 运行 `ArenaForge: Run`。
3. 在运行面板里添加或编辑测试。
4. 需要从链接建比赛目录或单题目录时，运行 `ArenaForge: Setup Contest`。
5. 第一次提交 Codeforces 之前，先运行 `ArenaForge: Configure Credentials`。
6. 在比赛工作区里的源文件上运行 `ArenaForge: Submit`。

常用快捷键：

- 运行当前文件：Windows/Linux 上是 `Ctrl+Alt+B`，macOS 上是 `Ctrl+B`
- 新建测试：`Ctrl+Enter`
- 停止当前进程：所有平台都可以用 `Ctrl+C`，Windows/Linux 额外支持 `Ctrl+X`

完整列表见：

- `Default (Windows).sublime-keymap`
- `Default (Linux).sublime-keymap`
- `Default (OSX).sublime-keymap`

## 配置

主设置文件是 `ArenaForge.sublime-settings`。
仓库里还附带了按平台整理的推荐设置：

- `ArenaForge (Windows).sublime-settings`
- `ArenaForge (Linux).sublime-settings`
- `ArenaForge (OSX).sublime-settings`

最常会改到的设置项有：

- `run_settings`：语言配置、文件扩展名、编译命令、运行命令，以及可选的 `lint_compile_cmd`
- `contests_root`：生成比赛或题目工作区的位置
- `tests_relative_dir`、`session_relative_dir`、`tests_file_suffix`：测试索引和会话快照的存放位置
- `preferred_locale`：`en`、`zh-Hans`、`ja`、`ko` 或 `ru`
- `credential_backend`：当前是 `keyring`
- `stress_time_limit_seconds`：对拍超时时间
- `algorithms_base`：本地 C++ 模板或片段的根目录
- `cpp_complete_enabled` 和 `cpp_complete_settings`：轻量 C++ 补全相关设置
- `submission_language_ids`：不同 provider 的提交语言 ID 映射
- `ui_variant` 和 `ui_density`：运行面板的基础显示风格

示例：

```json
{
  "preferred_locale": "zh-Hans",
  "contests_root": "~/Contests/ArenaForge",
  "tests_relative_dir": ".arena-forge/tests",
  "session_relative_dir": ".arena-forge/sessions",
  "stress_time_limit_seconds": 2,
  "credential_backend": "keyring",
  "algorithms_base": "Algorithms",
  "run_settings": [
    {
      "name": "C++",
      "extensions": ["cpp", "cc", "cxx"],
      "compile_cmd": "g++ \"{source_file}\" -std=gnu++17 -O2 -pipe -o \"{file_name}\"",
      "run_cmd": "./{file_name} {args}",
      "lint_compile_cmd": "g++ -std=gnu++17 \"{source_file}\" -I \"{source_file_dir}\""
    },
    {
      "name": "Python",
      "extensions": ["py"],
      "compile_cmd": null,
      "run_cmd": "python \"{source_file}\"",
      "lint_compile_cmd": null
    }
  ]
}
```

测试数据和会话数据都是普通 JSON 文件，保存在你的源码树附近。
具体路径由 `tests_relative_dir` 和 `session_relative_dir` 控制。
仓库里随包附带的不同平台设置文件在目录布局上略有差异，上面的示例更适合当模板看，而不是要求逐字照抄。

## 开发

- Python：`3.8+`
- 依赖管理：`uv`
- 运行时依赖：`keyring`

本地初始化与校验：

```bash
uv sync --group dev
uv run ruff check arena_forge tests
uv run pytest -q
uv run mypy
```

CI 覆盖范围：

- 工作流文件：`.github/workflows/ci.yml`
- 触发条件：`push`、`pull_request`、手动 `workflow_dispatch`
- 矩阵平台：`ubuntu-latest`、`windows-latest`
- 双平台检查：`ruff`、`pytest`
- Ubuntu 额外检查：`mypy`

## 致谢

这个项目的思路和工作流来自 [FastOlympicCoding](https://github.com/Jatana/FastOlympicCoding) by Jatana。

当前代码库仍然面向竞赛编程场景，但实现已经重组为类型化核心、可移植的 JSON 存储，以及更清晰的 Sublime 适配层。

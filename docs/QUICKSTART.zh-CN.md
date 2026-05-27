# ArenaForge 快速上手

这份文档的目标是让你尽快把 ArenaForge 跑起来，用于日常刷题。

## 1. 连接包目录

Windows 本地开发时，优先用仓库里的 junction 脚本：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\link_sublime_package.ps1
```

然后在 Sublime Text 里执行 `Tools -> Developer -> Reload Plugins`。

## 2. 写用户配置

编辑：

```text
Packages/User/ArenaForge.sublime-settings
```

最小示例：

```json
{
  "preferred_locale": "zh-Hans",
  "default_contest_language": "cpp",
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

最佳实践：

- 这里主要放个人路径和工作流开关
- 风格规则放到 `.clang-format`、`pyproject.toml`、`rustfmt.toml` 等项目原生配置文件里

## 3. 检查工具链

确认你常用的语言已经在本机可用。

常见例子：

- C++：`g++`
- Python：`python`
- Java：`javac` 和 `java`
- Kotlin：`kotlinc`
- Go：`go`
- Rust：`rustc` 和 `rustfmt`
- Python formatter：`ruff`

如果路径或工具状态不确定，先跑一次 `ArenaForge: Doctor`。

## 4. 第一次跑 C++

1. 打开 `A.cpp`
2. 运行 `ArenaForge: Run`
3. 在右侧面板里加测试
4. 故意写一个 C++ 错误并保存，确认诊断标记能出来
5. 运行 `ArenaForge: Format`，或者直接保存触发格式化

说明：

- C++ 红框 / 错误标记依赖 `lint_enabled` 和 C++ profile 里的 `lint_compile_cmd`
- 如果没出来，先 `Reload Plugins`，再跑 `ArenaForge: Doctor`

## 5. 第一次跑 Python

1. 打开 `main.py`
2. 运行 `ArenaForge: Run`
3. 在运行面板里填样例输入
4. 保存，或者运行 `ArenaForge: Format`

Python 格式化走的是 `ruff format`。

## 6. 第一次跑 Java

1. 打开 `Main.java`
2. 运行 `ArenaForge: Run`
3. 需要的话配置 `google-java-format` 后再运行 `ArenaForge: Format`

如果 `google-java-format` 不在 `PATH`，可以这样配：

```json
{
  "formatting": {
    "commands": {
      "google-java-format": ["java", "-jar", "tools/google-java-format.jar"]
    }
  }
}
```

## 7. 创建比赛工作区

1. 运行 `ArenaForge: Setup Contest`
2. 粘贴支持的比赛或题目链接
3. 在语言选择面板里选目标语言
4. ArenaForge 会生成工作区、源码文件、测试和元数据

你选的语言会决定：

- 源文件扩展名
- 内置比赛模板
- 后续运行方式
- 对应 formatter

## 8. 格式化相关命令

常用命令：

- `ArenaForge: Format`
- `ArenaForge: Diagnose Formatter`
- `ArenaForge: Formatter Install Guide`
- `ArenaForge: Create Workspace Format Configs`

如果某个文件没有按预期格式化，先跑 `Diagnose Formatter`。

## 9. 日常循环

推荐的日常节奏：

1. 打开文件
2. 跑测试
3. 格式化
4. 看诊断
5. 需要时对拍
6. 在比赛工作区里提交

# ArenaForge 快速上手

这份文档的目标是让你尽快把 ArenaForge 跑起来，开始日常刷题。

## 1. 连接包目录

Windows 本地开发时，优先使用仓库里的 junction 脚本：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\link_sublime_package.ps1
```

然后在 Sublime Text 中执行 `Tools -> Developer -> Reload Plugins`。

## 2. 编写用户设置

编辑：

```text
Packages/User/ArenaForge.sublime-settings
```

最小示例：

```json
{
  "preferred_locale": "zh-Hans",
  "default_contest_language": "cpp",
  "language_profiles": {
    "profiles": {
      "cpp": {
        "compile_cmd": "g++ \"{source_file}\" -std=c++14 -g -Wall -Winvalid-pch -finput-charset=UTF-8 -fexec-charset=UTF-8 -o \"{source_file_dir}\\\\{file_name}.exe\"",
        "lint_compile_cmd": "g++ -std=c++14 -g -Wall -fsyntax-only -fdiagnostics-color=never -Winvalid-pch -finput-charset=UTF-8 -fexec-charset=UTF-8 \"{source_file}\" -I \"{source_file_dir}\""
      }
    }
  },
  "formatting": {
    "format_on_save": true,
    "commands": {
      "clang-format": ["C:/Program Files/LLVM/bin/clang-format.exe"]
    }
  }
}
```

建议：

- 个人路径和工作流开关放在这里。
- 格式风格放在 `.clang-format`、`pyproject.toml`、`rustfmt.toml` 等项目文件里。

## 3. 检查工具链

确认你要用的语言已经在本机可用。

常见例子：

- C++：`g++`
- Python：`python`
- Java：`javac` 和 `java`
- Kotlin：`kotlinc`
- Go：`go`
- Rust：`rustc` 和 `rustfmt`
- Python formatter：`ruff`

如果路径或工具状态不确定，先运行 `ArenaForge: Doctor`。

## 4. 第一次跑 C++

1. 打开 `A.cpp`。
2. 运行 `ArenaForge: Run`。
3. 在右侧 run panel 里添加测试。
4. 如果你用了 `bits/stdc++.h`，先运行一次 `bash scripts/pch.sh` 生成匹配的 `.gch`。
5. 故意写一个 C++ 错误并保存，确认红框或错误标记出现。
6. 运行 `ArenaForge: Format`，或者开启 `format_on_save`。

补充说明：

- Windows 默认把 `Ctrl+Alt+B` 绑定到 `ArenaForge: Run`。
- 右侧 run panel 常用快捷键：
  - `Enter`：新增测试行
  - `Ctrl+Enter`：创建或切换测试
  - `Ctrl+C` / `Ctrl+X`：停止当前进程
  - `Ctrl+L`：清空全部测试
  - `Ctrl+U`：清空当前输入
  - `Ctrl+W`：删除前一个单词
  - `Alt+B` / `Alt+F`：按单词移动
  - `Ctrl+Up` / `Ctrl+Down`：浏览输入历史
  - `Ctrl+Shift+Up` / `Ctrl+Shift+Down`：交换测试顺序

## 5. 第一次跑 Python

1. 打开 `main.py`。
2. 运行 `ArenaForge: Run`。
3. 在运行面板里添加样例输入。
4. 保存文件，或者运行 `ArenaForge: Format`。

Python 默认使用 `ruff format`。

## 6. 第一次跑 Java

1. 打开 `Main.java`。
2. 运行 `ArenaForge: Run`。
3. 按需配置 `google-java-format` 后再运行 `ArenaForge: Format`。

ArenaForge 也会自动发现项目内的 `tools/google-java-format.jar` 和 `tools/ktfmt.jar`。
如果 JAR 在别处，可以这样配置：

```json
{
  "formatting": {
    "commands": {
      "google-java-format": ["java", "-jar", "tools/google-java-format.jar"]
    }
  }
}
```

`ktfmt` 也是同样写法。

## 7. 创建比赛工作区

1. 运行 `ArenaForge: Setup Contest`。
2. 粘贴支持的比赛或题目 URL。
3. 在语言选择面板里选目标语言。
4. ArenaForge 会生成工作区、源文件、测试和元数据。

所选语言会影响：

- 源文件扩展名
- 内置比赛模板
- 后续运行行为
- 对应 formatter

## 8. 格式化相关

常用命令：

- `ArenaForge: Format`
- `ArenaForge: Diagnose Formatter`
- `ArenaForge: Formatter Install Guide`
- `ArenaForge: Create Workspace Format Configs`

如果某个文件没有按预期格式化，先运行 `Diagnose Formatter`。

## 9. 每日流程

推荐的日常节奏：

1. 打开文件
2. 跑测试
3. 格式化
4. 修诊断
5. 需要时做对拍
6. 准备好后在比赛工作区提交

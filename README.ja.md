[English](README.md) | [简体中文](README.zh-CN.md) | [日本語](README.ja.md) | [한국어](README.ko.md) | [Русский](README.ru.md)

# ArenaForge

[![CI](https://github.com/yviscool/ArenaForge/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/yviscool/ArenaForge/actions/workflows/ci.yml)

ArenaForge は、Sublime Text 向けの競技プログラミング用ワークベンチです。ローカル実行、サンプル管理、コンテスト作成、整形、C++ 診断、対拍、Codeforces 提出を 1 つのパッケージにまとめます。

## 主要リンク

- [Quickstart](docs/QUICKSTART.md)
- [Configuration](docs/CONFIGURATION.md)
- [PCH workflow](docs/PCH.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Sublime shell migration notes](docs/SUBLIME_SHELL_MIGRATION.md)

## 機能

- 専用のテストパネルで現在のファイルを実行
- テストとセッションをソースツリー近くの JSON に保存
- 出力と期待値を比較し、最初の不一致を表示
- 実行パネルで入力履歴と端末風編集を維持
- 対応 OJ の URL からコンテスト / 単体問題ワークスペースを生成
- コンテスト作成時に対象言語を選択
- 対応言語を ArenaForge 内で直接整形
- `lint_compile_cmd` で C++ の診断マークを表示
- `<task>__Good` / `<task>__Generator` で対拍
- `keyring` で資格情報を保存し、Codeforces に直接提出

## 言語対応

### 実行 / コンテストテンプレート

| 言語 | 実行 | テンプレート | formatter |
| --- | --- | --- | --- |
| C | 対応 | 対応 | `clang-format` |
| C++ | 対応 | 対応 | `clang-format` |
| Python | 対応 | 対応 | `ruff format` |
| Java | 対応 | 対応 | `google-java-format` |
| Kotlin | 対応 | 対応 | `ktfmt` |
| Go | 対応 | 対応 | `gofmt` |
| Rust | 対応 | 対応 | `rustfmt` |
| JavaScript | 対応 | 対応 | `oxfmt` |

### 整形のみ `oxfmt` 対応

- TypeScript / TSX
- JSON / YAML / TOML
- HTML / Vue / Svelte
- CSS / SCSS / Less
- Markdown / MDX
- GraphQL

## Provider

| Provider | ワークスペース生成 | 提出 |
| --- | --- | --- |
| Codeforces | サンプル付きコンテストワークスペース | 対応 |
| AtCoder | サンプル付きコンテストワークスペース | 非対応 |
| Luogu | 単体問題ワークスペース | 非対応 |
| AcWing | 単体問題ワークスペース | 非対応 |

Codeforces 提出には `requests` と利用可能な `keyring` backend が必要です。

## インストール

### 通常

1. このフォルダを Sublime Text の `Packages/` に置く。
2. 外側のパッケージ名は `ArenaForge` のままにする。
3. Sublime Text を再起動、または `Tools -> Developer -> Reload Plugins` を実行。
4. コマンドパレットで `ArenaForge: Open Settings` を開く。

### Windows 開発用リンク

ローカル開発では `Packages/` へのコピーより junction を推奨します。

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\link_sublime_package.ps1
```

## コマンド

### 実行 / コンテスト

- `ArenaForge: Run`
- `ArenaForge: Setup Contest`
- `ArenaForge: Submit`
- `ArenaForge: Configure Credentials`
- `ArenaForge: Doctor`
- `ArenaForge: Run History`

Windows では `Ctrl+Alt+B` が `ArenaForge: Run` に割り当てられています。

### 整形

- `ArenaForge: Format`
- `ArenaForge: Format Document`
- `ArenaForge: Format Selection`
- `ArenaForge: Diagnose Formatter`
- `ArenaForge: Formatter Install Guide`
- `ArenaForge: Create Format Config For Current File`
- `ArenaForge: Create Workspace Format Configs`

## 推奨ワークフロー

1. ローカル開発では junction で Sublime に接続する。
2. 個人設定は `Packages/User/ArenaForge.sublime-settings` に書く。
3. `A.cpp`、`main.py`、`Main.java` のようなソースを開く。
4. `ArenaForge: Run` を実行し、右側の run panel でテストを編集する。
5. 必要なら `ArenaForge: Format`、または `format_on_save` を使う。
6. 新しいコンテスト用ディレクトリが必要なら `ArenaForge: Setup Contest` を使う。
7. 初期化パネルで対象言語を選ぶ。
8. コンパイラや formatter のパスを変えたら `ArenaForge: Doctor` を実行する。

## ユーザー設定

メイン設定は `ArenaForge.sublime-settings` です。個人の上書きは次へ置きます。

```text
Packages/User/ArenaForge.sublime-settings
```

推奨方針:

- ユーザー設定には個人のパスとワークフロー切り替えだけを書く。
- 言語ごとのスタイルは `.clang-format`、`pyproject.toml`、`rustfmt.toml` などに置く。
- `formatting.commands` にはローカルの formatter パスやコマンドプレフィックスを書く。

例:

```json
{
  "preferred_locale": "ja",
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

## 重要な設定

- `language_profiles`
- `formatting.format_on_save`
- `formatting.commands`
- `formatting.extra_args`
- `formatting.selector_overrides`
- `submission_language_ids`
- `stress_time_limit_seconds`
- `tests_relative_dir` / `session_relative_dir` / `tests_file_suffix`

## トラブルシュート

### C++ の赤枠やエラー表示が出ない

- `lint_enabled` が `true`
- 対象が `.cpp` などの対応拡張子
- `language_profiles.profiles.cpp.lint_compile_cmd` が有効
- `g++` が Sublime から呼べる
- 設定変更後にプラグインを再読み込み

`bits/stdc++.h` を使うなら、先に `.gch` を作成してください。

```bash
bash scripts/pch.sh
```

### 整形が効かない

- 対応 adapter に認識されているか
- formatter が `PATH` か `formatting.commands` にあるか
- Java / Kotlin は `tools/google-java-format.jar` / `tools/ktfmt.jar` を見つけられるか

`ArenaForge: Diagnose Formatter` で詳細を確認できます。

## プロジェクト構成

- `arena_forge/core`: ドメインモデル、出力比較、セッションユースケース
- `arena_forge/adapters`: Sublime 統合、provider、保存、runner、i18n、ワークスペース生成、認証保存
- `arena_forge/formatting`: formatter adapter、実行ファイル探索、設定生成、整形実行時
- `arena_forge/templates`: 標準コンテストテンプレート
- `tests`: provider、保存、設定、run panel、整形の pytest
- `docs`: アーキテクチャ、設定、quickstart

## 開発

- Python: `3.8+`
- 依存管理: `uv`
- 実行時依存: `keyring`

```bash
uv sync --group dev
uv run ruff check arena_forge tests
uv run pytest -q
uv run mypy
```

## 謝辞

このプロジェクトは [FastOlympicCoding](https://github.com/Jatana/FastOlympicCoding) のアイデアとワークフローを参考にしています。

[English](README.md) | [简体中文](README.zh-CN.md) | [日本語](README.ja.md) | [한국어](README.ko.md) | [Русский](README.ru.md)

# ArenaForge

[![CI](https://github.com/yviscool/ArenaForge/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/yviscool/ArenaForge/actions/workflows/ci.yml)

ArenaForge は Sublime Text 向けの競技プログラミングツールキットです。
日々の問題解決で繰り返す作業、つまりソースを開く、素早く実行する、サンプルを整理する、問題やコンテストの URL からクリーンな作業ディレクトリを作る、という流れのために設計されています。

このパッケージは、そのワークフローをエディタ内で完結させます。
実行履歴、ストレステスト、診断、テンプレート挿入、コンテストセットアップ、Codeforces への提出まで、同じ作業画面の中で扱えます。

## できること

- 現在のファイルを専用のテストパネルで実行します。
- サンプルテストや詳細なセッションスナップショットを、ソースツリーの近くに JSON ファイルとして保存します。
- 出力と期待値を比較し、最初に不一致になった位置を表示します。
- 実行パネル内で対話入力の履歴を保持し、基本的なターミナル風編集を行えます。
- 現在のソースファイル専用のテストエディタと、別個の実行履歴ビューを開けます。
- Codeforces、AtCoder、Luogu、AcWing の URL から、コンテストまたは単問用の作業ディレクトリを生成します。
- 認証情報を `keyring` に保存したうえで、Sublime Text から Codeforces の解答を提出できます。
- `<task>__Good` と `<task>__Generator` を使ってストレステストを実行します。
- ローカルのアルゴリズムテンプレートを挿入し、軽量な C++ 補完支援を提供します。
- `lint_compile_cmd` を使って C++ の診断を実行します。
- `Doctor` レポートで、パッケージファイル、リソース、実行プロファイル、認証バックエンドの利用可否を確認できます。

## 現在の Provider サポート

| Provider | ワークスペース生成 | 提出 |
| --- | --- | --- |
| Codeforces | サンプル付きコンテストワークスペース | はい |
| AtCoder | サンプル付きコンテストワークスペース | いいえ |
| Luogu | 単問ワークスペース | いいえ |
| AcWing | 単問ワークスペース | いいえ |

Codeforces への提出には `requests` と、動作する `keyring` バックエンドが必要です。
リポジトリでは `dependencies.json` に `requests` を宣言しています。

## プロジェクト構成

- `arena_forge/core`: 型付けされたドメインモデル、出力比較、セッションユースケース
- `arena_forge/adapters`: Sublime 連携、provider、ストレージ、runner、i18n、ワークスペース生成、認証情報保存
- `tests`: provider、ストレージ、設定、実行パネルの挙動、コマンド面を対象にした pytest カバレッジ
- `docs`: アーキテクチャ、移行、i18n に関するメモ
- リポジトリルート: キーマップ、シンタックスファイル、HTML 描画アセット、アイコン、デバッガー、薄いラッパーコマンドなどの Sublime パッケージリソース

## インストール

1. このフォルダを Sublime Text の `Packages/` ディレクトリに配置します。
2. 手動でインストールする場合は、外側のパッケージフォルダ名を `ArenaForge` に変更してください。
3. Sublime Text を再起動します。
4. コマンドパレットから `ArenaForge: Open Settings` を実行します。

実行したい言語に応じて、`g++`、`python`、`javac` などのローカルツールチェーンも必要です。

## 基本ワークフロー

1. `A.cpp` や `main.py` のようなソースファイルを開きます。
2. `ArenaForge: Run` を実行します。
3. 実行パネルでテストを追加または編集します。
4. URL からコンテストや問題用のワークスペースを作る場合は `ArenaForge: Setup Contest` を使います。
5. 初回の Codeforces 提出前に `ArenaForge: Configure Credentials` を実行します。
6. コンテストワークスペース内のファイルから `ArenaForge: Submit` を実行します。

よく使うショートカット:

- 現在のファイルを実行: Windows/Linux は `Ctrl+Alt+B`、macOS は `Ctrl+B`
- 新しいテストを追加: `Ctrl+Enter`
- 現在のプロセスを停止: 全プラットフォームで `Ctrl+C`、Windows/Linux では `Ctrl+X` も利用可
- 選択中のテストブロックを削除: `Ctrl+D`
- テスト順を入れ替え: Windows/Linux は `Ctrl+Shift+Up` / `Ctrl+Shift+Down`、macOS は `Ctrl+Super+Up` / `Ctrl+Super+Down`
- 右側のテスターパネルを切り替え: Windows/Linux は `Ctrl+K`、`Ctrl+P`、macOS は `Super+K`、`Super+P`

実行パネルでは、Windows/Linux で次のようなターミナル風編集キーも使えます。

- すべてのテストをクリア: `Ctrl+L`
- 現在の入力行をクリア: `Ctrl+U`
- 入力履歴を移動: `Ctrl+Up` / `Ctrl+Down`
- 行頭または行末へ移動: `Ctrl+A` / `Ctrl+E`
- 単語単位で移動または削除: `Alt+B`、`Alt+F`、`Ctrl+W`

macOS では追加で次も使えます。

- デバッガー付きで実行: `Ctrl+Shift+B`
- インライン phantom 表示を切り替え: `Ctrl+Super+Shift+H`

一覧は以下を参照してください。

- `Default (Windows).sublime-keymap`
- `Default (Linux).sublime-keymap`
- `Default (OSX).sublime-keymap`

## 設定

メインの設定ファイルは `ArenaForge.sublime-settings` です。
リポジトリには、プラットフォーム別の推奨デフォルト設定も含まれています。

- `ArenaForge (Windows).sublime-settings`
- `ArenaForge (Linux).sublime-settings`
- `ArenaForge (OSX).sublime-settings`

よく調整する設定項目は次のとおりです。

- `run_settings`: 言語プロファイル、拡張子、コンパイルコマンド、実行コマンド、任意の `lint_compile_cmd`
- `contests_root`: 生成したコンテストまたは問題ワークスペースの配置先
- `tests_relative_dir`, `session_relative_dir`, `tests_file_suffix`: テストインデックスとセッションスナップショットの保存場所
- `preferred_locale`: `en`、`zh-Hans`、`ja`、`ko`、`ru`
- `credential_backend`: 現在は `keyring`
- `stress_time_limit_seconds`: ストレステストで使うタイムアウト
- `algorithms_base`: ローカル C++ テンプレートやスニペットのベースディレクトリ
- `cpp_complete_enabled` と `cpp_complete_settings`: 軽量 C++ 補完の挙動
- `submission_language_ids`: provider ごとの提出用言語 ID マッピング
- `ui_variant` と `ui_density`: 実行パネルの基本的な表示設定

例:

```json
{
  "preferred_locale": "ja",
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

テストデータとセッションデータは、通常の JSON ファイルとして作業中のソースツリーの近くに保存されます。
正確な場所は `tests_relative_dir` と `session_relative_dir` の設定によって決まります。
同梱の設定ファイルはプラットフォームごとにディレクトリ構成が少し異なるため、上の例は固定の記述ではなくテンプレートとして扱ってください。

## 開発

- Python: `3.8+`
- 依存管理: `uv`
- 実行時依存: `keyring`

ローカルセットアップと確認:

```bash
uv sync --group dev
uv run ruff check arena_forge tests
uv run pytest -q
uv run mypy
```

CI と Release 自動化:

- ワークフローファイル: `.github/workflows/ci.yml`
- トリガー: `push`、`pull_request`、手動の `workflow_dispatch`
- 品質チェックのマトリクス: `ubuntu-latest` と `windows-latest`
- 両プラットフォームで実行するチェック: `ruff`、`pytest`
- Ubuntu での追加チェック: `mypy`
- リリース条件: `main` への push が品質チェックを通過すると、`ci-<short-sha>` というタグの GitHub プレリリースを自動公開
- リリース資産: `ArenaForge.sublime-package`。追跡対象のパッケージファイルから生成し、そのプレリリースに添付

## 謝辞

このプロジェクトは、Jatana による [FastOlympicCoding](https://github.com/Jatana/FastOlympicCoding) のアイデアとワークフローを土台にしています。

現在のコードベースも競技プログラミングに焦点を当てていますが、実装は型付けされたコア、移植性の高い JSON ストレージ、より整理された Sublime アダプター構成へと再編されています。

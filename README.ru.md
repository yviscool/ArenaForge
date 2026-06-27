[English](README.md) | [简体中文](README.zh-CN.md) | [日本語](README.ja.md) | [한국어](README.ko.md) | [Русский](README.ru.md)

# ArenaForge

[![CI](https://github.com/yviscool/ArenaForge/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/yviscool/ArenaForge/actions/workflows/ci.yml)

ArenaForge — это рабочая среда для спортивного программирования в Sublime Text. Она объединяет локальный запуск, управление тестами, создание контестов, форматирование, C++-диагностику, сравнение запусков и отправку на Codeforces.

## Быстрые ссылки

- [Quickstart](docs/QUICKSTART.md)
- [Configuration](docs/CONFIGURATION.md)
- [PCH workflow](docs/PCH.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Sublime shell migration notes](docs/SUBLIME_SHELL_MIGRATION.md)

## Что умеет

- Запускать текущий файл в отдельной панели тестов.
- Сохранять тесты и снимки сессий в JSON рядом с деревом исходников.
- Сравнивать вывод программы с ожидаемым ответом и показывать первое расхождение.
- Сохранять историю ввода и терминальный стиль редактирования в панели запуска.
- Создавать рабочие пространства контестов и отдельных задач по URL поддерживаемых OJ.
- Спрашивать целевой язык перед созданием файлов контеста.
- Форматировать поддерживаемые языки внутри ArenaForge.
- Показывать C++-метки диагностики через `lint_compile_cmd`.
- Запускать сравнение через `<task>__Good` и `<task>__Generator`.
- Сохранять учётные данные через `keyring` и отправлять решения в Codeforces.

## Поддержка языков

### Запуск / шаблоны контестов

| Язык | Запуск | Шаблон | formatter |
| --- | --- | --- | --- |
| C | Да | Да | `clang-format` |
| C++ | Да | Да | `clang-format` |
| Python | Да | Да | `ruff format` |
| Java | Да | Да | `google-java-format` |
| Kotlin | Да | Да | `ktfmt` |
| Go | Да | Да | `gofmt` |
| Rust | Да | Да | `rustfmt` |
| JavaScript | Да | Да | `oxfmt` |

### Форматирование только через `oxfmt`

- TypeScript / TSX
- JSON / YAML / TOML
- HTML / Vue / Svelte
- CSS / SCSS / Less
- Markdown / MDX
- GraphQL

## Поддержка provider

| Provider | Создание рабочего пространства | Отправка |
| --- | --- | --- |
| Codeforces | Контест с загруженными примерами | Да |
| AtCoder | Контест с загруженными примерами | Нет |
| Luogu | Рабочее пространство для одной задачи | Нет |
| AcWing | Рабочее пространство для одной задачи | Нет |

Для отправки в Codeforces нужны `requests` и доступный backend `keyring`.

## Установка

### Обычная установка

1. Поместите эту папку в `Packages/` Sublime Text.
2. Имя внешней папки оставьте `ArenaForge`.
3. Перезапустите Sublime Text или выполните `Tools -> Developer -> Reload Plugins`.
4. Откройте command palette и запустите `ArenaForge: Open Settings`.

Локально всё равно должны быть установлены нужные компиляторы и formatter-ы: `g++`, `python`, `javac`, `ruff`, `rustfmt`.

### Windows-линк для разработки

Для локальной разработки лучше использовать junction, а не копировать файлы в `Packages/`.

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\link_sublime_package.ps1
```

## Команды

### Запуск / контест

- `ArenaForge: Run`
- `ArenaForge: Setup Contest`
- `ArenaForge: Submit`
- `ArenaForge: Configure Credentials`
- `ArenaForge: Doctor`
- `ArenaForge: Run History`

В Windows `Ctrl+Alt+B` по умолчанию вызывает `ArenaForge: Run`.

### Форматирование

- `ArenaForge: Format`
- `ArenaForge: Format Document`
- `ArenaForge: Format Selection`
- `ArenaForge: Diagnose Formatter`
- `ArenaForge: Formatter Install Guide`
- `ArenaForge: Create Format Config For Current File`
- `ArenaForge: Create Workspace Format Configs`

## Рекомендуемый workflow

1. При локальной разработке подключите пакет через junction.
2. Личные переопределения пишите только в `Packages/User/ArenaForge.sublime-settings`.
3. Откройте исходник вроде `A.cpp`, `main.py` или `Main.java`.
4. Запустите `ArenaForge: Run` и ведите тесты в правой панели.
5. При необходимости запускайте `ArenaForge: Format` или включите `format_on_save`.
6. Для нового контестного каталога используйте `ArenaForge: Setup Contest`.
7. В панели инициализации выберите целевой язык.
8. После изменения путей компилятора или formatter-а запустите `ArenaForge: Doctor`.

## Пользовательские настройки

Основной файл настроек — `ArenaForge.sublime-settings`. Ваши личные переопределения должны лежать здесь:

```text
Packages/User/ArenaForge.sublime-settings
```

Рекомендации:

- В пользовательских настройках храните только личные пути и переключатели workflow.
- Языковой стиль храните в `.clang-format`, `pyproject.toml`, `rustfmt.toml` и подобных файлах проекта.
- `formatting.commands` используйте для локальных путей к formatter-ам или командных префиксов.

Пример:

```json
{
  "preferred_locale": "ru",
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

## Важные настройки

- `language_profiles`
- `formatting.format_on_save`
- `formatting.commands`
- `formatting.extra_args`
- `formatting.selector_overrides`
- `submission_language_ids`
- `stress_time_limit_seconds`
- `tests_relative_dir` / `session_relative_dir` / `tests_file_suffix`

## Поиск проблем

### Нет красной рамки или ошибок C++

- `lint_enabled` должен быть `true`
- Текущий файл должен быть поддерживаемым расширением, например `.cpp`
- `language_profiles.profiles.cpp.lint_compile_cmd` должен быть валиден
- `g++` должен вызываться из Sublime
- После изменения настроек нужно перезагрузить плагины

Если используете `bits/stdc++.h`, сначала сгенерируйте `.gch`:

```bash
bash scripts/pch.sh
```

### Форматирование не срабатывает

- Язык должен распознаваться нужным formatter adapter
- formatter должен быть в `PATH` или в `formatting.commands`
- Для Java / Kotlin должны находиться `tools/google-java-format.jar` / `tools/ktfmt.jar`

Проверить детали можно через `ArenaForge: Diagnose Formatter`.

## Структура проекта

- `arena_forge/core`: доменные модели, сравнение вывода, сценарии сессий
- `arena_forge/adapters`: интеграция с Sublime, provider-ы, хранение, runner-ы, i18n, генерация рабочих пространств, хранилище учётных данных
- `arena_forge/formatting`: formatter adapters, поиск исполняемых файлов, генерация конфигов и runtime форматирования
- `arena_forge/templates`: встроенные шаблоны контестов
- `tests`: pytest для provider-ов, хранилища, настроек, run panel и форматирования
- `docs`: архитектура, настройки, quickstart

## Разработка

- Python: `3.8+`
- Управление зависимостями: `uv`
- Runtime dependency: `keyring`

```bash
uv sync --group dev
uv run ruff check arena_forge tests
uv run pytest -q
uv run mypy
```

## Благодарности

Идеи и workflow этого проекта опираются на [FastOlympicCoding](https://github.com/Jatana/FastOlympicCoding).

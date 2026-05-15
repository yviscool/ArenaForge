[English](README.md) | [简体中文](README.zh-CN.md) | [日本語](README.ja.md) | [한국어](README.ko.md) | [Русский](README.ru.md)

# ArenaForge

[![CI](https://github.com/yviscool/ArenaForge/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/yviscool/ArenaForge/actions/workflows/ci.yml)

ArenaForge - это набор инструментов для соревновательного программирования в Sublime Text.
Он рассчитан на повседневный цикл решения задач: открыть файл, быстро запустить его, привести в порядок примеры и создать чистое рабочее пространство по URL задачи или контеста.

Пакет сохраняет этот рабочий процесс внутри редактора.
История запусков, стресс-тесты, диагностика, вставка шаблонов, настройка контестов и отправка решений на Codeforces работают в одной рабочей поверхности.

## Возможности

- Запускает текущий файл в отдельной панели тестов.
- Сохраняет примеры тестов и более подробные снимки сессий в JSON-файлы рядом с деревом исходников.
- Сравнивает вывод с ожидаемым ответом и показывает позицию первого несовпадения.
- Хранит историю интерактивного ввода в панели запуска и поддерживает базовое редактирование в стиле терминала.
- Открывает отдельный редактор тестов и отдельное представление истории запусков для текущего файла.
- Создает рабочие пространства для контестов или отдельных задач по ссылкам Codeforces, AtCoder, Luogu и AcWing.
- Позволяет отправлять решения на Codeforces прямо из Sublime Text, сохраняя учетные данные через `keyring`.
- Запускает стресс-тесты с помощью `<task>__Good` и `<task>__Generator`.
- Вставляет локальные алгоритмические шаблоны и дает легковесные подсказки для C++.
- Выполняет диагностику C++ через `lint_compile_cmd`.
- Показывает отчет `Doctor` по файлам пакета, ресурсам, профилям запуска и доступности backend для учетных данных.

## Текущая поддержка Provider

| Provider | Создание рабочего пространства | Отправка |
| --- | --- | --- |
| Codeforces | Рабочее пространство контеста с разобранными примерами | Да |
| AtCoder | Рабочее пространство контеста с разобранными примерами | Нет |
| Luogu | Рабочее пространство для одной задачи | Нет |
| AcWing | Рабочее пространство для одной задачи | Нет |

Для отправки на Codeforces нужны `requests` и рабочий backend `keyring`.
Репозиторий объявляет `requests` в `dependencies.json`.

## Структура проекта

- `arena_forge/core`: типизированные доменные модели, проверка вывода и сценарии работы с сессиями
- `arena_forge/adapters`: интеграция с Sublime, provider, хранилище, runner, i18n, генерация рабочих пространств и хранение учетных данных
- `tests`: покрытие pytest для provider, хранилища, настроек, поведения панели запуска и командной поверхности
- `docs`: заметки по архитектуре, миграции и i18n
- корень репозитория: ресурсы пакета Sublime, такие как keymap, syntax-файлы, HTML-ассеты для рендера, иконки, отладчики и тонкие команды-обертки

## Установка

1. Поместите эту папку в каталог `Packages/` вашего Sublime Text.
2. Если устанавливаете вручную, переименуйте внешнюю папку пакета в `ArenaForge`.
3. Перезапустите Sublime Text.
4. Откройте палитру команд и выполните `ArenaForge: Open Settings`.

Также нужны локальные toolchain для языков, которые вы хотите запускать, например `g++`, `python` или `javac`.

## Базовый рабочий процесс

1. Откройте исходный файл, например `A.cpp` или `main.py`.
2. Выполните `ArenaForge: Run`.
3. Добавьте или отредактируйте тесты в панели запуска.
4. Если нужно создать рабочее пространство контеста или задачи по URL, используйте `ArenaForge: Setup Contest`.
5. Перед первой отправкой на Codeforces выполните `ArenaForge: Configure Credentials`.
6. Выполните `ArenaForge: Submit` из файла, находящегося внутри рабочего пространства контеста.

Часто используемые горячие клавиши:

- Запуск текущего файла: `Ctrl+Alt+B` в Windows/Linux, `Ctrl+B` в macOS
- Добавить новый тест: `Ctrl+Enter`
- Остановить текущий процесс: `Ctrl+C` на всех платформах, `Ctrl+X` также работает в Windows/Linux

Полный список смотрите в:

- `Default (Windows).sublime-keymap`
- `Default (Linux).sublime-keymap`
- `Default (OSX).sublime-keymap`

## Конфигурация

Основной файл настроек - `ArenaForge.sublime-settings`.
В репозитории также есть рекомендуемые настройки по платформам:

- `ArenaForge (Windows).sublime-settings`
- `ArenaForge (Linux).sublime-settings`
- `ArenaForge (OSX).sublime-settings`

Настройки, которые вы, скорее всего, будете менять чаще всего:

- `run_settings`: языковые профили, расширения файлов, команды компиляции, команды запуска и необязательный `lint_compile_cmd`
- `contests_root`: место, где создаются рабочие пространства контестов или задач
- `tests_relative_dir`, `session_relative_dir`, `tests_file_suffix`: где хранятся индексы тестов и снимки сессий
- `preferred_locale`: `en`, `zh-Hans`, `ja`, `ko` или `ru`
- `credential_backend`: сейчас это `keyring`
- `stress_time_limit_seconds`: таймаут для стресс-тестов
- `algorithms_base`: базовый каталог для локальных C++ шаблонов или сниппетов
- `cpp_complete_enabled` и `cpp_complete_settings`: поведение легковесного автодополнения C++
- `submission_language_ids`: отображение идентификаторов языков отправки для каждого provider
- `ui_variant` и `ui_density`: базовое оформление панели запуска

Пример:

```json
{
  "preferred_locale": "ru",
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

Тестовые данные и данные сессий хранятся как обычные JSON-файлы рядом с рабочим деревом исходников.
Точные пути зависят от настроек `tests_relative_dir` и `session_relative_dir`.
Файлы настроек, поставляемые с репозиторием, немного различаются по структуре каталогов в зависимости от платформы, поэтому пример выше стоит воспринимать как шаблон, а не как обязательную копию.

## Разработка

- Python: `3.8+`
- Менеджер зависимостей: `uv`
- Зависимость времени выполнения: `keyring`

Локальная настройка и проверка:

```bash
uv sync --group dev
uv run ruff check arena_forge tests
uv run pytest -q
uv run mypy
```

Покрытие CI:

- Файл workflow: `.github/workflows/ci.yml`
- Триггеры: `push`, `pull_request` и ручной `workflow_dispatch`
- Матрица: `ubuntu-latest` и `windows-latest`
- Проверки на обеих платформах: `ruff`, `pytest`
- Дополнительная проверка на Ubuntu: `mypy`

## Благодарности

Этот проект основан на идеях и рабочем процессе [FastOlympicCoding](https://github.com/Jatana/FastOlympicCoding) от Jatana.

Текущая кодовая база сохраняет фокус на соревновательном программировании, но ее реализация перестроена вокруг типизированного ядра, переносимого JSON-хранилища и более чистых адаптеров Sublime.

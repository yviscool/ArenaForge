[English](README.md) | [简体中文](README.zh-CN.md) | [日本語](README.ja.md) | [한국어](README.ko.md) | [Русский](README.ru.md)

# ArenaForge

[![CI](https://github.com/yviscool/ArenaForge/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/yviscool/ArenaForge/actions/workflows/ci.yml)

ArenaForge는 Sublime Text용 경쟁 프로그래밍 작업대입니다. 로컬 실행, 샘플 관리, 콘테스트 생성, 포맷팅, C++ 진단, 대조 실행, Codeforces 제출을 하나의 패키지로 묶습니다.

## 바로가기

- [Quickstart](docs/QUICKSTART.md)
- [Configuration](docs/CONFIGURATION.md)
- [PCH workflow](docs/PCH.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Sublime shell migration notes](docs/SUBLIME_SHELL_MIGRATION.md)

## 주요 기능

- 전용 테스트 패널에서 현재 파일 실행
- 테스트와 세션 스냅샷을 소스 트리 근처의 JSON으로 저장
- 출력과 정답을 비교하고 첫 번째 불일치를 표시
- 실행 패널에서 입력 히스토리와 터미널식 편집 유지
- 지원되는 OJ URL로 콘테스트 / 단일 문제 작업공간 생성
- 콘테스트 생성 전에 목표 언어 선택
- ArenaForge 내부에서 지원 언어 직접 포맷
- `lint_compile_cmd`로 C++ 진단 마커 표시
- `<task>__Good` / `<task>__Generator`로 대조 실행
- `keyring`으로 자격 증명을 저장하고 Codeforces에 직접 제출

## 언어 지원

### 실행 / 콘테스트 템플릿

| 언어 | 실행 | 템플릿 | formatter |
| --- | --- | --- | --- |
| C | 지원 | 지원 | `clang-format` |
| C++ | 지원 | 지원 | `clang-format` |
| Python | 지원 | 지원 | `ruff format` |
| Java | 지원 | 지원 | `google-java-format` |
| Kotlin | 지원 | 지원 | `ktfmt` |
| Go | 지원 | 지원 | `gofmt` |
| Rust | 지원 | 지원 | `rustfmt` |
| JavaScript | 지원 | 지원 | `oxfmt` |

### `oxfmt` 전용 포맷 지원

- TypeScript / TSX
- JSON / YAML / TOML
- HTML / Vue / Svelte
- CSS / SCSS / Less
- Markdown / MDX
- GraphQL

## Provider 지원

| Provider | 작업공간 생성 | 제출 |
| --- | --- | --- |
| Codeforces | 샘플이 포함된 콘테스트 작업공간 | 지원 |
| AtCoder | 샘플이 포함된 콘테스트 작업공간 | 미지원 |
| Luogu | 단일 문제 작업공간 | 미지원 |
| AcWing | 단일 문제 작업공간 | 미지원 |

Codeforces 제출에는 `requests`와 사용 가능한 `keyring` 백엔드가 필요합니다.

## 설치

### 일반 설치

1. 이 폴더를 Sublime Text의 `Packages/` 아래에 둡니다.
2. 바깥 패키지 이름은 `ArenaForge`로 유지합니다.
3. Sublime Text를 재시작하거나 `Tools -> Developer -> Reload Plugins`를 실행합니다.
4. 커맨드 팔레트에서 `ArenaForge: Open Settings`를 엽니다.

여전히 로컬에 필요한 컴파일러와 formatter는 직접 설치해야 합니다. 예: `g++`, `python`, `javac`, `ruff`, `rustfmt`.

### Windows 개발 링크

로컬 개발에서는 `Packages/`로 복사하기보다 junction을 권장합니다.

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\link_sublime_package.ps1
```

## 명령

### 실행 / 콘테스트

- `ArenaForge: Run`
- `ArenaForge: Setup Contest`
- `ArenaForge: Submit`
- `ArenaForge: Configure Credentials`
- `ArenaForge: Doctor`
- `ArenaForge: Run History`

Windows 기본 키맵은 `Ctrl+Alt+B`를 `ArenaForge: Run`에 연결합니다.

### 포맷팅

- `ArenaForge: Format`
- `ArenaForge: Format Document`
- `ArenaForge: Format Selection`
- `ArenaForge: Diagnose Formatter`
- `ArenaForge: Formatter Install Guide`
- `ArenaForge: Create Format Config For Current File`
- `ArenaForge: Create Workspace Format Configs`

## 권장 워크플로

1. 로컬 개발 시 junction으로 Sublime에 연결합니다.
2. 개인 설정은 `Packages/User/ArenaForge.sublime-settings`에만 씁니다.
3. `A.cpp`, `main.py`, `Main.java` 같은 소스 파일을 엽니다.
4. `ArenaForge: Run`을 실행하고 오른쪽 run panel에서 테스트를 관리합니다.
5. 필요할 때 `ArenaForge: Format`을 실행하거나 `format_on_save`를 켭니다.
6. 새 콘테스트 폴더가 필요하면 `ArenaForge: Setup Contest`를 사용합니다.
7. 초기화 패널에서 목표 언어를 선택합니다.
8. 컴파일러나 formatter 경로를 바꾼 뒤에는 `ArenaForge: Doctor`를 실행합니다.

## 사용자 설정

메인 설정 파일은 `ArenaForge.sublime-settings`입니다. 개인 오버라이드는 다음에 둡니다.

```text
Packages/User/ArenaForge.sublime-settings
```

권장 원칙:

- 사용자 설정에는 개인 경로와 워크플로 스위치만 넣습니다.
- 언어별 스타일은 `.clang-format`, `pyproject.toml`, `rustfmt.toml` 같은 프로젝트 파일에 둡니다.
- `formatting.commands`에는 로컬 formatter 경로나 명령 접두어를 넣습니다.

예시:

```json
{
  "preferred_locale": "ko",
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

## 중요 설정

- `language_profiles`
- `formatting.format_on_save`
- `formatting.commands`
- `formatting.extra_args`
- `formatting.selector_overrides`
- `submission_language_ids`
- `stress_time_limit_seconds`
- `tests_relative_dir` / `session_relative_dir` / `tests_file_suffix`

## 문제 해결

### C++ 빨간 박스나 에러 표시가 안 나옴

- `lint_enabled`가 `true`인지 확인
- 현재 파일이 `.cpp` 같은 지원 확장자인지 확인
- `language_profiles.profiles.cpp.lint_compile_cmd`가 유효한지 확인
- Sublime에서 `g++`를 호출할 수 있는지 확인
- 설정을 바꾼 뒤 플러그인을 다시 불러오기

`bits/stdc++.h`를 쓴다면 먼저 `.gch`를 만들어야 합니다.

```bash
bash scripts/pch.sh
```

### 포맷팅이 동작하지 않음

- 현재 문법이 어떤 formatter adapter에 의해 인식되는지
- formatter가 `PATH` 또는 `formatting.commands`에 있는지
- Java / Kotlin은 `tools/google-java-format.jar` / `tools/ktfmt.jar`를 찾을 수 있는지

자세한 내용은 `ArenaForge: Diagnose Formatter`로 확인할 수 있습니다.

## 프로젝트 구조

- `arena_forge/core`: 도메인 모델, 출력 비교, 세션 유스케이스
- `arena_forge/adapters`: Sublime 통합, provider, 저장소, runner, i18n, 작업공간 생성, 자격 증명 저장
- `arena_forge/formatting`: formatter adapter, 실행 파일 탐색, 설정 생성, 포맷 런타임
- `arena_forge/templates`: 기본 콘테스트 템플릿
- `tests`: provider, 저장소, 설정, run panel, 포맷팅에 대한 pytest
- `docs`: 아키텍처, 설정, quickstart

## 개발

- Python: `3.8+`
- 의존성 관리: `uv`
- 런타임 의존성: `keyring`

```bash
uv sync --group dev
uv run ruff check arena_forge tests
uv run pytest -q
uv run mypy
```

## 감사의 말

이 프로젝트는 [FastOlympicCoding](https://github.com/Jatana/FastOlympicCoding)의 아이디어와 워크플로를 참고했습니다.

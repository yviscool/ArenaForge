[English](README.md) | [简体中文](README.zh-CN.md) | [日本語](README.ja.md) | [한국어](README.ko.md) | [Русский](README.ru.md)

# ArenaForge

[![CI](https://github.com/yviscool/ArenaForge/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/yviscool/ArenaForge/actions/workflows/ci.yml)

ArenaForge는 Sublime Text용 경쟁 프로그래밍 툴킷입니다.
문제를 푸는 일상적인 흐름, 즉 파일을 열고, 빠르게 실행하고, 샘플 테스트를 정리하고, 문제나 대회 URL에서 깔끔한 작업 공간을 만드는 과정을 중심으로 설계되었습니다.

이 패키지는 그 워크플로를 에디터 안에서 끝낼 수 있게 해 줍니다.
실행 기록, 스트레스 테스트, 진단, 템플릿 삽입, 대회 설정, Codeforces 제출까지 모두 같은 작업 화면 안에서 처리할 수 있습니다.

## 주요 기능

- 현재 파일을 전용 테스트 패널에서 실행합니다.
- 샘플 테스트와 더 풍부한 세션 스냅샷을 소스 트리 근처의 JSON 파일로 저장합니다.
- 출력과 기대 답안을 비교하고, 처음으로 불일치한 위치를 표시합니다.
- 실행 패널 안에서 대화형 입력 기록을 유지하고 기본적인 터미널 스타일 편집을 지원합니다.
- 현재 소스 파일용 전용 테스트 편집기와 별도의 실행 기록 뷰를 엽니다.
- Codeforces, AtCoder, Luogu, AcWing URL에서 대회 또는 단일 문제 작업 공간을 생성합니다.
- 자격 증명을 `keyring`에 저장한 상태로 Sublime Text 안에서 Codeforces 풀이를 제출할 수 있습니다.
- `<task>__Good`과 `<task>__Generator`로 스트레스 테스트를 실행합니다.
- 로컬 알고리즘 템플릿을 삽입하고 가벼운 C++ 자동완성 보조 기능을 제공합니다.
- `lint_compile_cmd`로 C++ 진단을 실행합니다.
- `Doctor` 보고서로 패키지 파일, 리소스, 실행 프로필, 자격 증명 백엔드 사용 가능 여부를 확인합니다.

## 현재 Provider 지원

| Provider | 워크스페이스 생성 | 제출 |
| --- | --- | --- |
| Codeforces | 샘플이 포함된 대회 워크스페이스 | 예 |
| AtCoder | 샘플이 포함된 대회 워크스페이스 | 아니오 |
| Luogu | 단일 문제 워크스페이스 | 아니오 |
| AcWing | 단일 문제 워크스페이스 | 아니오 |

Codeforces 제출에는 `requests`와 정상 동작하는 `keyring` 백엔드가 필요합니다.
리포지토리는 `dependencies.json`에 `requests`를 선언하고 있습니다.

## 프로젝트 구조

- `arena_forge/core`: 타입이 지정된 도메인 모델, 출력 비교, 세션 유스케이스
- `arena_forge/adapters`: Sublime 통합, provider, 저장소, runner, i18n, 워크스페이스 스캐폴딩, 자격 증명 저장
- `tests`: provider, 저장소, 설정, 실행 패널 동작, 명령 표면을 다루는 pytest 커버리지
- `docs`: 아키텍처, 마이그레이션, i18n 문서
- 저장소 루트: 키맵, 구문 파일, HTML 렌더링 자산, 아이콘, 디버거, 얇은 래퍼 명령 같은 Sublime 패키지 리소스

## 설치

1. 이 폴더를 Sublime Text의 `Packages/` 디렉터리에 넣습니다.
2. 수동 설치라면 바깥쪽 패키지 폴더 이름을 `ArenaForge`로 바꿉니다.
3. Sublime Text를 다시 시작합니다.
4. 명령 팔레트에서 `ArenaForge: Open Settings`를 실행합니다.

`g++`, `python`, `javac` 같은 로컬 툴체인도 실행할 언어에 맞게 준비되어 있어야 합니다.

## 기본 워크플로

1. `A.cpp`나 `main.py` 같은 소스 파일을 엽니다.
2. `ArenaForge: Run`을 실행합니다.
3. 실행 패널에서 테스트를 추가하거나 수정합니다.
4. URL에서 대회 또는 문제 작업 공간을 만들고 싶다면 `ArenaForge: Setup Contest`를 사용합니다.
5. Codeforces에 처음 제출하기 전에 `ArenaForge: Configure Credentials`를 실행합니다.
6. 대회 작업 공간 안의 파일에서 `ArenaForge: Submit`을 실행합니다.

자주 쓰는 단축키:

- 현재 파일 실행: Windows/Linux는 `Ctrl+Alt+B`, macOS는 `Ctrl+B`
- 새 테스트 추가: `Ctrl+Enter`
- 현재 프로세스 중지: 모든 플랫폼에서 `Ctrl+C`, Windows/Linux에서는 `Ctrl+X`도 지원
- 선택한 테스트 블록 삭제: `Ctrl+D`
- 테스트 순서 바꾸기: Windows/Linux는 `Ctrl+Shift+Up` / `Ctrl+Shift+Down`, macOS는 `Ctrl+Super+Up` / `Ctrl+Super+Down`
- 오른쪽 테스터 패널 전환: Windows/Linux는 `Ctrl+K`, `Ctrl+P`, macOS는 `Super+K`, `Super+P`

실행 패널에서는 Windows/Linux에서 다음과 같은 터미널 스타일 편집 키도 지원합니다.

- 모든 테스트 지우기: `Ctrl+L`
- 현재 입력 줄 지우기: `Ctrl+U`
- 입력 기록 탐색: `Ctrl+Up` / `Ctrl+Down`
- 줄 처음이나 끝으로 이동: `Ctrl+A` / `Ctrl+E`
- 단어 단위 이동 또는 삭제: `Alt+B`, `Alt+F`, `Ctrl+W`

macOS에서는 추가로 다음도 사용할 수 있습니다.

- 디버거로 실행: `Ctrl+Shift+B`
- 인라인 phantom 표시 전환: `Ctrl+Super+Shift+H`

전체 목록은 다음 파일을 참고하세요.

- `Default (Windows).sublime-keymap`
- `Default (Linux).sublime-keymap`
- `Default (OSX).sublime-keymap`

## 설정

주 설정 파일은 `ArenaForge.sublime-settings`입니다.
리포지토리에는 플랫폼별 권장 기본 설정도 포함되어 있습니다.

- `ArenaForge (Windows).sublime-settings`
- `ArenaForge (Linux).sublime-settings`
- `ArenaForge (OSX).sublime-settings`

가장 자주 만질 설정은 다음과 같습니다.

- `run_settings`: 언어 프로필, 파일 확장자, 컴파일 명령, 실행 명령, 선택적 `lint_compile_cmd`
- `contests_root`: 생성된 대회 또는 문제 작업 공간이 위치할 경로
- `tests_relative_dir`, `session_relative_dir`, `tests_file_suffix`: 테스트 인덱스와 세션 스냅샷 저장 위치
- `preferred_locale`: `en`, `zh-Hans`, `ja`, `ko`, `ru`
- `credential_backend`: 현재는 `keyring`
- `stress_time_limit_seconds`: 스트레스 테스트에 사용하는 타임아웃
- `algorithms_base`: 로컬 C++ 템플릿이나 스니펫의 기본 디렉터리
- `cpp_complete_enabled`와 `cpp_complete_settings`: 가벼운 C++ 자동완성 동작
- `submission_language_ids`: provider별 제출 언어 ID 매핑
- `ui_variant`와 `ui_density`: 실행 패널의 기본 표시 설정

예시:

```json
{
  "preferred_locale": "ko",
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

### Formatter 참고

- Java / Kotlin에서는 프로젝트 안의 `tools/google-java-format.jar` 와 `tools/ktfmt.jar` 도 자동으로 감지합니다.
- JAR 파일이 다른 위치에 있으면 `formatting.commands` 에 `["java", "-jar", "..."]` 형태로 지정하세요.

테스트 데이터와 세션 데이터는 일반 JSON 파일로 작업 중인 소스 트리 근처에 저장됩니다.
정확한 위치는 `tests_relative_dir`와 `session_relative_dir` 설정에 따라 달라집니다.
함께 제공되는 설정 파일은 플랫폼마다 디렉터리 배치가 조금씩 다르므로, 위 예시는 그대로 복사할 값이 아니라 템플릿으로 보는 편이 좋습니다.

## 개발

- Python: `3.8+`
- 의존성 관리자: `uv`
- 런타임 의존성: `keyring`

로컬 설정 및 검증:

```bash
uv sync --group dev
uv run ruff check arena_forge tests
uv run pytest -q
uv run mypy
```

CI 및 Release 자동화:

- 워크플로 파일: `.github/workflows/ci.yml`
- 트리거: `push`, `pull_request`, 수동 `workflow_dispatch`
- 품질 검사 매트릭스: `ubuntu-latest`, `windows-latest`
- 두 플랫폼 공통 검사: `ruff`, `pytest`
- Ubuntu 추가 검사: `mypy`
- 배포 규칙: `main` 브랜치로 push되고 품질 검사 매트릭스를 통과하면 `ci-<short-sha>` 태그의 GitHub 프리릴리스를 자동 발행
- 배포 자산: 추적 중인 패키지 파일로 만든 `ArenaForge.sublime-package`를 해당 프리릴리스에 첨부

## 감사의 말

이 프로젝트는 Jatana의 [FastOlympicCoding](https://github.com/Jatana/FastOlympicCoding)에서 아이디어와 워크플로를 이어받았습니다.

현재 코드베이스도 경쟁 프로그래밍에 초점을 유지하지만, 구현은 타입이 지정된 코어, 이식 가능한 JSON 저장소, 더 정돈된 Sublime 어댑터 구조를 중심으로 재구성되었습니다.

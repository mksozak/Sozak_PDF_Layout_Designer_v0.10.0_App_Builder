---
title: "Sozak PDF Layout Designer Codex 문제해결 작업설명서"
author: "Moonkyu Lee"
created: 2026-08-19
updated: 2026-08-19
type: guide
phase: seedling
status: active
project: "[[Sozak PDF Layout Designer]]"
tags:
  - "sozak-pdf-layout-designer"
  - "codex"
  - "troubleshooting"
  - "handoff"
  - "macos"
aliases:
  - "PDF Layout Designer Codex Troubleshooting"
derived_from:
  - "[[Sozak PDF Layout Designer 유지보수·오류진단·복구 가이드]]"
version: "1.1"
description: "v0.10.0 문제 발생 시 Codex가 안전한 진단 순서와 보존해야 할 기능을 이해하도록 하는 인수인계 문서."
note: "최신 App Builder, 개발문서, smoke-test output, 오류 screenshot/log를 함께 제공할 것."
---
# Sozak PDF Layout Designer Codex 문제해결 작업설명서

## 프로젝트 핵심

```text
UI/browser: sozak_pdf_designer.html
local server/YAML/dialog: sozak_pdf_designer.py
actual PDF: sozak_pdf_overlay.py
preset/default: presets/howon-handout.json
regression: tests/release_smoke_test.py + tests/http_smoke_test.py + optional ui_runtime_smoke_test.py
build: build-macos-app.command + SozakPDFLayoutDesigner.spec
```

Body PDF가 있으면 기존 PDF에 overlay하고, 없으면 `stamp_dummy_pdf()`로 2페이지 test body를 만들어 overlay한다.

## 먼저 할 일

```bash
python3 -m py_compile sozak_pdf_designer.py sozak_pdf_overlay.py tests/release_smoke_test.py
python3 tests/release_smoke_test.py
python3 tests/http_smoke_test.py
# Playwright/Chromium 환경이면:
python3 tests/ui_runtime_smoke_test.py --require
```

첫 실패를 기준으로 범위를 좁힌다.

## v0.10.0에서 보존해야 할 기능

```text
Vertical default
Vertical Documentation Name/Week-Version ON
Horizontal/Vertical 독립 Header geometry/visibility
Header line X/Y/Width/enabled
Footer line1/2 독립 X/Y/Width/enabled
Footer body-margin quick align
Right Rule 0~210mm
Margin Guides
Smart Guides + Snap separate toggles
Position Reset
Bounds Warning
Dummy 2-page preview/export
real Body preview/export
week_version + legacy week
Preset text persistence
source overwrite protection
Fedora PDF app icon
coffee joke
```

## 안전한 macOS 진단

```bash
ls -ld "/Applications/Sozak PDF Layout Designer.app"
xattr "/Applications/Sozak PDF Layout Designer.app"
uname -m
file "/Applications/Sozak PDF Layout Designer.app/Contents/MacOS/Sozak PDF Layout Designer"
codesign -dv --verbose=4 "/Applications/Sozak PDF Layout Designer.app"
```

quarantine 해제가 필요하면 앱 하나만:

```bash
xattr -dr com.apple.quarantine "/Applications/Sozak PDF Layout Designer.app"
```

## 증상별 파일

| 증상 | 먼저 볼 곳 |
|---|---|
| UI control/guide | HTML |
| YAML/filename/export | designer.py |
| preview와 PDF 불일치 | HTML + overlay.py |
| layout switch 후 상태 유실 | HTML snapshot/apply + preset |
| Dummy export | designer.py + overlay.py |
| Footer X/align | HTML + overlay.py + test |
| app icon/build | spec + build command + assets |

## Codex 지시문

```text
첨부한 Sozak PDF Layout Designer v0.10.0 이상 App Builder와 개발문서를 먼저 읽어줘.
실제 source version을 확인하고 tests/release_smoke_test.py와 tests/http_smoke_test.py를 먼저 실행해줘.

지금 발생한 문제를 재현하고 원인 파일을 특정한 뒤 최소 수정해줘.
기존 v0.10.0 기능을 훼손하지 말고, 수정 후 smoke test와 실제 PDF 생성 검증을 해줘.

경로가 확정되지 않은 상태에서 홈 폴더 전체에 xattr/chmod/rm 재귀 명령을 실행하지 마.
릴리스 수준 수정이면 버전, CHANGELOG, 관련 개발문서도 함께 업데이트해줘.
```

## 문서 수정 이력

| 문서 버전 | 날짜 | 기준 앱 | 내용 |
|---|---|---|---|
| 1.0 | 2026-08-19 | v0.9.2 | 최초 Codex 문제해결 설명 |
| 1.1 | 2026-08-19 | v0.10.0 | v0.10.0 보존 기능과 smoke-test-first 절차 반영 |

---
title: "Sozak PDF Layout Designer Codex 개발·수정 작업지시 템플릿"
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
  - "development"
  - "prompt"
  - "handoff"
  - "maintenance"
aliases:
  - "PDF Layout Designer Codex Dev Prompt"
derived_from:
  - "[[Sozak PDF Layout Designer 개발 아키텍처와 코드 구조]]"
  - "[[Sozak PDF Layout Designer 릴리스 체크리스트와 문서 동기화 규칙]]"
version: "1.1"
description: "v0.10.0 이후 친구나 후속 개발자가 Codex에 앱 수정·업데이트·검증을 안전하게 지시하기 위한 템플릿."
note: "최신 App Builder 전체와 개발 문서, 재현 자료를 함께 제공하고 smoke test 통과를 완료 조건으로 요구할 것."
---
# Sozak PDF Layout Designer Codex 개발·수정 작업지시 템플릿

## 기본 지시문

```text
첨부한 Sozak PDF Layout Designer 최신 App Builder 전체와 개발 문서를 먼저 읽어줘.
파일명이나 기억만으로 버전을 추정하지 말고 source의 실제 version string을 확인해라.

현재 v0.10.0 이상에서 반드시 보존해야 하는 기능:
- Vertical default
- Horizontal/Vertical 독립 geometry + visibility
- Header line별 X/Y/Width/enabled
- Vertical Documentation Name / Week-Version 기본 표시
- Footer 1/2 독립 X/Y/Width/enabled + 본문 좌/중/우 quick-align
- Right Rule 0~210mm
- Margin Guides
- Smart Guides와 Snap의 독립 ON/OFF
- Position Reset와 A4 bounds warning
- Body 없는 2-page Dummy preview/export
- 실제 Body PDF preview/export
- documentation_name + week_version, legacy week alias
- Preset = 디자인 + 입력 텍스트 전체 snapshot
- source Body overwrite protection
- built-in logos/fonts
- Fedora PDF app icon
- coffee joke button

작업 원칙:
1. 재현하고 원인/수정 파일을 먼저 특정한다.
2. geometry 변경은 HTML preview와 PyMuPDF overlay를 함께 수정한다.
3. schema 변경은 구 preset migration을 넣는다.
4. 홈 폴더 전체에 xattr/chmod/rm 재귀 명령을 실행하지 않는다.
5. 수정 후 Python/JavaScript syntax를 검사한다.
6. 반드시 python3 tests/release_smoke_test.py 와 python3 tests/http_smoke_test.py 를 실행한다. Playwright/Chromium 환경이면 ui_runtime_smoke_test.py --require도 실행한다.
7. 새 기능은 해당 regression/HTTP test에도 검증을 추가한다.
8. 실제 PDF를 생성해 검증한다.
9. 릴리스면 version, CHANGELOG, 영향을 받은 개발 문서를 함께 갱신한다.
10. patch만 주지 말고 최종적으로 전체 App Builder를 보존한다.

이번 요구사항:
[여기에 작성]

완료 보고:
- base/new version
- 수정 파일
- 이유
- schema/migration
- tests
- 실제 PDF 검증
- macOS에서만 남은 검증
- artifacts
```

## Preview/Final mismatch

```text
sozak_pdf_designer.html의 현재 element geometry 계산과
sozak_pdf_overlay.py의 apply_selected_layout/draw_header/draw_footer를 비교해라.
visibility와 X/Y/Width를 모두 비교하고 actual PDF test를 추가해라.
```

## Metadata 수정

```text
canonical은 documentation_name + week_version이다.
legacy week를 읽는 compatibility를 깨지 마라.
YAML에 없는 field는 _present에 들어가면 안 된다.
```

## Dummy 수정

```text
Body 없는 preview와 stamp_dummy_pdf 실제 출력 둘 다 확인해라.
Dummy 2페이지의 Header first-page-only / Footer all-pages 규칙을 깨지 마라.
```

## Build 문제

```text
pwd와 build-macos-app.command 실제 위치를 확인한 뒤 진단해라.
홈 폴더에서 xattr ... . 또는 rm -rf를 실행하지 마라.
build script는 smoke test를 먼저 통과해야 한다.
```

## 새 릴리스

```text
새 version string을 HTML/Python/spec/preset/README/build artifact/docs에 모두 반영하고,
CHANGELOG + Developer Docs history를 갱신해라.
두 smoke test 통과 결과와 macOS build 미실행/실행 여부를 명확히 구분해 보고해라.
```

## 문서 수정 이력

| 문서 버전 | 날짜 | 기준 앱 | 내용 |
|---|---|---|---|
| 1.0 | 2026-08-19 | v0.9.2 | 최초 Codex 개발 템플릿 |
| 1.1 | 2026-08-19 | v0.10.0 | v0.10.0 보존 기능과 smoke-test 의무 추가 |

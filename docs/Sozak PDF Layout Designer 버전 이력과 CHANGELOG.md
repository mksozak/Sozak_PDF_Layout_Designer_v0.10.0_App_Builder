---
title: "Sozak PDF Layout Designer 버전 이력과 CHANGELOG"
author: "Moonkyu Lee"
created: 2026-08-19
updated: 2026-08-19
type: documentation-ai
phase: seedling
status: active
project: "[[Sozak PDF Layout Designer]]"
tags:
  - "sozak-pdf-layout-designer"
  - "changelog"
  - "release"
  - "version-history"
  - "development"
aliases:
  - "Sozak PDF Layout Designer CHANGELOG"
derived_from:
  - "[[Sozak PDF Layout Designer 개발문서 허브]]"
version: "1.1"
description: "확인 가능한 과거 개발 기록과 앞으로의 릴리스 변경사항을 누적 기록하는 CHANGELOG."
note: "새 앱 버전을 배포하기 전에 최상단에 새 버전 항목을 추가하고 테스트·호환성·알려진 제한까지 기록할 것."
---
# Sozak PDF Layout Designer 버전 이력과 CHANGELOG

## 기록 원칙

과거 기록을 덮어쓰지 않는다. 릴리스마다 최소한 **목적, 변경 파일, schema, 하위 호환, 실제 테스트, 알려진 제한**을 남긴다.

# v0.10.0 — Smart Layout & Dummy Review

**날짜:** 2026-08-19

## 목적

PDF가 준비되기 전에도 2페이지 문서를 보며 설계·출력할 수 있게 하고, Header/Footer 요소의 자유로운 배치와 표시/숨김을 일관된 schema로 통합하며, 후속 개발자가 회귀를 자동으로 잡을 수 있게 한 기능/유지보수 릴리스.

## 사용자 기능

- Vertical에서도 Documentation Name · Week / Version 기본 표시
- 각 요소 panel 좌측 `●/○` 표시/숨김 토글
- Header visibility를 Horizontal/Vertical별로 독립 저장
- 각 요소 `↺ 위치 초기화`
- Right Rule X 범위 0~210mm
- Footer 1/2 독립 X / Y / Text Width / enabled
- Footer 1/2 `본문 좌측 / 가운데 / 우측` quick align
- Smart Guides와 Snap 별도 ON/OFF
- 이동 중에만 A4/margin/center/other-element guide 표시
- A4 out-of-bounds warning
- Body PDF 없는 2-page Dummy preview
- Body PDF 없는 실제 Dummy test PDF export
- 우측 상단 `☕ 개발자에게 커피 사기` → `만나서 사주세요. ☕`
- 큰 갈색 Fedora를 쓴 PDF app icon

## Metadata

canonical:

```yaml
documentation_name: "CLASS HANDOUT WEEKLY SERIES"
week_version: "WEEK 08"
```

legacy `week:`와 `week/version`, `week version`, `week-version`, `weekVersion`은 import alias로 유지.

YAML omitted-field 처리도 수정하여 없는 `instructors`를 `_present`로 잘못 표시하지 않게 함.

## Preset schema

Header line:

```text
enabled
```

layout info:

```text
line_enabled[]
```

Footer text:

```text
line1_enabled / line2_enabled
line1_x / line2_x
line1_width / line2_width
```

v0.9.x preset에 새 field가 없으면 legacy 값/default를 이용해 normalization한다.

## Overlay/Server

- `stamp_dummy_pdf()` 추가
- `/api/generate`: Body 유무에 따라 real/dummy route
- `/api/pick-output`: Body 없이도 Dummy filename 제안
- 원본 Body overwrite 차단 유지

## 개발/배포

- `tests/release_smoke_test.py` 추가
- `tests/http_smoke_test.py` 추가: local API integration 검증
- `tests/ui_runtime_smoke_test.py` 추가: 선택적 browser interaction 검증
- `build-macos-app.command`가 build 전에 두 smoke test를 실행하며 실패 시 중단
- macOS에서 `sips`/`iconutil`로 app icon 생성 가능
- spec에 ICNS 지정
- ZIP/DMG filename에 v0.10.0 포함
- README YAML version을 실제 앱 버전과 일치시킴

## 검증

2026-08-19 source 기준 다음이 통과함.

```text
Python syntax
JavaScript syntax
preset v0.10.0 / Vertical default
Vertical Series 실제 PDF
Header/Footer visibility 실제 PDF
Footer X 50mm 이동량 실제 PDF
Header independent X regression
Right Rule 5mm / 205mm 실제 PDF
2-page Dummy body
Header first page only
Footer all pages
week_version + legacy aliases
omitted metadata preservation
real Body PDF stamping
numbered safe output
HTTP /api/default
HTTP dummy generate
HTTP real-body generate
HTTP source overwrite 409
HTTP week_version metadata / PDF info
UI runtime: Dummy 1/2page, Series toggle, Coffee, Footer align, Smart Guides/Snap, Reset
dummy missing-glyph replacement 없음
```

macOS `.app`/DMG/Gatekeeper 실행은 macOS에서만 최종 확인한다.

---

# v0.9.2 — Independent Text X / Width

**날짜:** 2026-08-19

- 기관명, 메인 제목, 강사 1·2, Series/Week에 독립 X/Text Width
- layout `info.line_x[]`, `info.line_width[]`
- Horizontal auto-after-logo 유지
- 실제 PDF에서 32mm X 이동과 width wrapping 검증

# v0.9.1 — Adaptive Margin Guides

**날짜:** 2026-08-19

- A4 preview Left/Right/Top/Bottom guide
- 1P Top=current layout first_top, 2P+=other_top
- preview-only
- Vertical default 유지

# v0.9 — Safe Export + Built-in Logos

**날짜:** 2026-08-19

- `Lecture (1).pdf`, `(2)` numbered candidate
- source Body overwrite server-side 차단
- built-in logos 7종
- Application Support/Built-in Logos 사용자 폴더
- PyInstaller `.app`/ZIP/DMG builder

# v0.8 — YAML / Markdown Metadata

**날짜:** 2026-08-19

- same-stem `.md/.markdown/.yaml/.yml` 자동 탐색
- metadata alias normalization
- explicit blank/omitted 구분
- 당시 canonical `week`; v0.10.0부터 canonical은 `week_version`

# v0.7 계열 — Dual Layout / Actual PDF Preview

**patch 기록 불완전**

- 한 preset에 Horizontal/Vertical geometry
- actual Body PDF 1/2page preview
- page1 Header / all-page Footer
- page1/2+ top margin 분리

# v0.5.4 — Interactive Designer Foundation

- Body PDF + JSON preset + Designer + PyMuPDF overlay 구조
- Accordion/editor selection
- Instructor 1/2
- Footer line Y 독립
- Page Number
- installed font lookup

# v0.4 계열 — Body CSS + Post-stamping Split

**patch 기록 불완전**

- Typora=Body 조판, Designer=Header/Footer 후처리
- A4 print margin variables 기반 확립

## 앞으로 사용할 릴리스 템플릿

```markdown
# vX.Y.Z — 제목
**날짜:** YYYY-MM-DD

## 목적
## 사용자 기능
## 수정 파일
## Schema
## Compatibility
## Tests
## Build
## Known limitations
```

## 문서 수정 이력

| 문서 버전 | 날짜 | 기준 앱 | 내용 |
|---|---|---|---|
| 1.0 | 2026-08-19 | v0.9.2 | 과거 기록 통합 및 CHANGELOG 시작 |
| 1.1 | 2026-08-19 | v0.10.0 | v0.10.0 Smart Layout & Dummy Review 릴리스 기록 추가 |

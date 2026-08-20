---
title: "Sozak PDF Layout Designer 개발문서 허브"
author: "Moonkyu Lee"
created: 2026-08-19
updated: 2026-08-19
type: documentation-ai
phase: seedling
status: active
project: "[[Sozak PDF Layout Designer]]"
tags:
  - "sozak-pdf-layout-designer"
  - "development"
  - "documentation"
  - "hub"
  - "macos"
  - "pdf"
aliases:
  - "Sozak PDF Layout Designer Dev Docs"
  - "PDF Layout Designer 개발 허브"
derived_from: []
version: "1.1"
description: "Sozak PDF Layout Designer의 개발·유지보수·빌드·배포·오류 해결 문서를 연결하는 최상위 허브."
note: "앱 릴리스 시 앱 버전, CHANGELOG, 관련 개발문서의 updated/version/history를 한 작업 묶음에서 갱신할 것."
---
# Sozak PDF Layout Designer 개발문서 허브

## 현재 기준

| 항목 | 값 |
|---|---|
| 제품명 | Sozak PDF Layout Designer |
| 현재 앱 기준 버전 | **v0.10.0** |
| 개발문서 세트 버전 | **v1.1** |
| 기준일 | 2026-08-19 |
| 실행 형태 | macOS `.app` + 로컬 브라우저 UI |
| PDF 엔진 | PyMuPDF |
| 설정 저장 | JSON preset |
| 문서 메타데이터 | Markdown/YAML front matter (선택) |
| 배포 | DMG 권장 |

v0.10.0부터 이 문서 세트는 코드와 함께 관리하는 **living documentation**이다. 릴리스가 바뀌었는데 문서의 기준 버전이 이전 버전이면 릴리스 미완료로 본다.

## 문서 지도

- [[Sozak PDF Layout Designer 개발 아키텍처와 코드 구조]] — 파일·API·preset·렌더링·Dummy·Smart Guides 구조
- [[Sozak PDF Layout Designer 버전 이력과 CHANGELOG]] — 버전별 기능과 schema 변경
- [[Sozak PDF Layout Designer 수정·빌드·배포 가이드]] — 수정, 회귀 테스트, 앱/DMG 빌드
- [[Sozak PDF Layout Designer 유지보수·오류진단·복구 가이드]] — 실행/렌더링/YAML/빌드 오류 진단
- [[Sozak PDF Layout Designer 릴리스 체크리스트와 문서 동기화 규칙]] — 릴리스 gate와 문서 추적 규칙
- [[Sozak PDF Layout Designer Codex 개발·수정 작업지시 템플릿]] — 후속 개발용 재사용 지시문
- [[Sozak PDF Layout Designer 친구용 설치·실행 설명서]] — 사용자 설치와 첫 실행
- [[Sozak PDF Layout Designer Codex 문제해결 작업설명서]] — 오류 발생 시 Codex 인수인계

## Source of Truth 우선순위

```text
1. 해당 릴리스의 실제 source code
2. presets/howon-handout.json
3. tests/release_smoke_test.py 및 실제 테스트 PDF
4. CHANGELOG
5. 개발 문서
6. 과거 인수인계 문서
```

문서와 코드가 다르면 무조건 문서를 코드에 맞추기 전에 **코드가 회귀한 것인지** 확인한다.

## v0.10.0 핵심 설계 결정

```text
Vertical = 기본 Header Layout
Preset = 디자인 + 입력 텍스트 전체 스냅샷
YAML = 문서별 텍스트/메타데이터 override
Body PDF 있음 = 실제 Body 위에 overlay
Body PDF 없음 = 2-page Dummy Body 생성 후 overlay
Smart Guides/Snap = preview-only
Header visibility = Horizontal/Vertical별 독립
Footer visibility/geometry = 전역
```

YAML의 Series 영역 canonical field는 다음으로 확정한다.

```yaml
documentation_name: "CLASS HANDOUT WEEKLY SERIES"
week_version: "WEEK 08"
```

기존 `week:`는 하위 호환 alias로 읽되 새 문서에는 `week_version`을 사용한다.

## 문서/릴리스 동기화 흐름

```text
요구사항 확정
→ source branch/copy
→ 코드 수정
→ Python/JS syntax
→ tests/release_smoke_test.py + tests/http_smoke_test.py
→ 실제 PDF 생성·렌더 검토
→ 앱 버전 갱신
→ CHANGELOG
→ 영향 받은 개발문서 갱신
→ macOS build
→ DMG 설치 테스트
→ 릴리스 보관
```

## Obsidian 보관 권장

이 9개 Markdown 파일을 한 폴더에 함께 두면 위키링크가 바로 연결된다. 파일명은 YAML `title`과 동일하게 유지한다.

## 문서 수정 이력

| 문서 버전 | 날짜 | 기준 앱 | 내용 |
|---|---|---|---|
| 1.0 | 2026-08-19 | v0.9.2 | 최초 통합 개발문서 세트 |
| 1.1 | 2026-08-19 | v0.10.0 | Smart Guides, 요소 토글, Footer geometry, Dummy export, week_version, 아이콘, 회귀 테스트 반영 |

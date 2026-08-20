---
title: "Sozak PDF Layout Designer v0.10.0 릴리스 검증 보고서"
author: "Moonkyu Lee"
created: 2026-08-19
updated: 2026-08-19
type: system-audit
phase: seed-stock
status: stable
project: "[[Sozak PDF Layout Designer]]"
tags:
  - "sozak-pdf-layout-designer"
  - "release-audit"
  - "regression-test"
  - "pdf"
  - "macos"
aliases:
  - "Sozak PDF Layout Designer v0.10.0 Verification"
derived_from:
  - "[[Sozak PDF Layout Designer 개발문서 허브]]"
  - "[[Sozak PDF Layout Designer 버전 이력과 CHANGELOG]]"
version: "1.0"
description: "Sozak PDF Layout Designer v0.10.0의 신규 기능, 회귀 테스트, HTTP/UI integration, 실제 PDF 렌더 및 배포 준비 상태를 검증한 릴리스 보고서."
note: "source/PDF/browser-level test는 통과. macOS .app/DMG/codesign/Gatekeeper 실기동은 macOS에서 build-macos-app.command 실행 후 최종 확인할 것."
---

# Sozak PDF Layout Designer v0.10.0 릴리스 검증 보고서

## 결론

**v0.10.0 source release는 현재 환경에서 검증 가능한 코드·UI interaction·local HTTP API·actual PDF 출력 테스트를 모두 통과했다.** 새 App Builder에는 자동 회귀 test 3종, 업데이트된 개발문서 v1.1, 새 Fedora PDF 아이콘, 실제 Body/Dummy 데모 PDF가 포함된다.

다만 현재 검증 환경은 Linux이므로 **macOS 전용 `.app` 생성, `codesign`, `hdiutil` DMG 생성, Finder 아이콘 표시, Gatekeeper 첫 실행**은 여기서 실행하지 않았다. 이 부분은 Mac에서 `build-macos-app.command`를 실행해 최종 확인해야 한다. Builder 자체는 macOS build 전에 필수 release/HTTP smoke test를 자동 실행하도록 구성했다.

## 기준

| 항목 | 값 |
|---|---|
| App | Sozak PDF Layout Designer |
| Release | **v0.10.0** |
| Developer Docs | **v1.1** |
| 기준 preset | `presets/howon-handout.json` |
| 기본 Header Layout | **Vertical** |
| 검증일 | 2026-08-19 |

## 이번 릴리스 구현 확인

- [x] Vertical에서 Documentation Name / Week-Version 기본 표시
- [x] 요소별 `●/○` 표시·숨김 토글
- [x] Header 표시 상태 Horizontal/Vertical 독립 저장
- [x] 요소별 `↺ 위치 초기화`
- [x] Right Rule X `0~210mm`
- [x] Footer 1/2 독립 X/Y/Text Width/enabled
- [x] Footer 본문 좌측/가운데/우측 quick-align
- [x] Smart Guides
- [x] Snap 별도 ON/OFF
- [x] A4 bounds warning
- [x] Body PDF 없는 2-page Dummy preview
- [x] Body PDF 없는 실제 2-page Dummy PDF export
- [x] `documentation_name` + `week_version`
- [x] legacy `week` / `week/version` 호환
- [x] Preset에 입력 text + 디자인 상태 저장 구조 유지
- [x] `☕ 개발자에게 커피 사기` → `만나서 사주세요. ☕`
- [x] 흰 배경 PDF + 큰 갈색 Fedora app icon
- [x] 개발문서 v1.1 및 CHANGELOG 갱신

## 검토 중 발견하여 추가로 수정한 사항

### 1. Dummy PDF의 missing glyph

초기 Dummy PDF에서 Helvetica가 `•` bullet과 em dash를 일부 환경에서 `?`로 렌더링했다. 실제 render 검토에서 발견했다.

수정:

```text
• → ASCII -
— → ASCII -
```

회귀 test에 `dummy body has no missing-glyph replacement`를 추가했다.

### 2. 기존 demo-body.pdf와 Vertical 112mm Header 충돌

기존 demo Body는 이전 layout 기준으로 본문이 너무 위에서 시작해 v0.10.0 Vertical Header와 겹쳤다. 앱의 결함이라기보다 Body PDF가 새로운 margin을 반영하지 않은 사례였으나, 릴리스 demo가 잘못 보이므로 demo Body를 2페이지로 재생성했다.

새 demo:

```text
1P body start: Vertical Header 아래
2P body start: Other Top margin 근처
Footer: 두 페이지 모두 검토 가능
```

최종 render에서 Header/Body overlap이 없음을 눈으로 확인했다.

### 3. `1페이지 Top` slider 최대값

Vertical default는 `112mm`인데 slider max가 이전 값 `100`에 머물 수 있는 문제를 점검해 **max 180mm**로 확장했다.

### 4. YAML omitted-field 처리

YAML에 `instructors`가 없는 경우 normalization 순서 때문에 `_present`가 잘못 설정될 가능성을 수정했다. raw key 존재 여부를 먼저 기록하므로, 없는 metadata가 기존 Designer 값을 불필요하게 덮어쓰지 않는다.

### 5. v0.9.2 README version 불일치 해소

이전 bundle의 README title은 v0.9.2인데 YAML `version: "0.9"`가 남아 있던 추적성 문제를 v0.10.0에서 해소했다. 현재 주요 version location은 모두 `0.10.0`으로 일치한다.

## 자동 테스트 결과

### Python syntax

통과:

```text
sozak_pdf_designer.py
sozak_pdf_overlay.py
tests/release_smoke_test.py
tests/http_smoke_test.py
tests/ui_runtime_smoke_test.py
```

### JavaScript syntax

`sozak_pdf_designer.html`의 script를 추출하여 `node --check` 통과.

### Release smoke test

`python3 tests/release_smoke_test.py`

통과 항목:

```text
preset version
Vertical default
Vertical Series visible
layout visibility schema
Horizontal/Vertical visibility independence
Footer independent geometry schema
Smart Guides static feature
Element visibility toggles
Footer quick align
Right Rule full X
Vertical first-top slider range
Dummy preview
Coffee joke
Bounds warning
Position reset
Week/Version
App icon + spec icon
week_version / legacy week / week-version aliases
metadata omitted-field preservation
Dummy PDF 2 pages
Dummy text both pages
Dummy missing-glyph 없음
Vertical Series actual PDF
Header first page only
Footer all pages
Header/Series/Footer visibility actual PDF
Footer X actual PDF movement
Header independent X regression
Right Rule actual PDF 5mm / 205mm
Existing Body PDF workflow
Real output numbered filename
Dummy output numbered filename
```

### HTTP integration smoke test

`python3 tests/http_smoke_test.py`

실제 `ThreadingHTTPServer` + Handler로 통과:

```text
/api/default → v0.10.0
/api/generate → Dummy PDF
/api/generate → real Body PDF
source Body와 같은 output → HTTP 409 차단
/api/load-metadata → week_version
/api/pdf-info → 2 pages
```

### UI runtime smoke test

`python3 tests/ui_runtime_smoke_test.py --require`

Playwright + Chromium으로 실제 DOM interaction을 검증했다. 현재 실행환경은 Chromium의 localhost navigation이 정책상 막혀 있어, UI test에서는 API 함수만 mock하고 **원본 HTML/JS interaction code는 그대로 실행**했다. 실제 HTTP Handler는 위의 별도 HTTP integration test로 검증했다.

통과:

```text
Dummy Page 1 / 2 전환
Vertical Series 표시
Series ●/○ toggle
Coffee toast
Footer quick-align
Footer X / Width dynamic limit
Smart Guides 표시
Snap 독립 OFF
Right Rule 0~210
1P Top 112 / max 180
Position Reset
Dummy export label
browser page error 없음
```

## 실제 PDF 검증

검증 PDF:

```text
demo-final.pdf
demo-dummy-final.pdf
```

둘 다:

```text
A4
2 pages
PyMuPDF openable
not encrypted
not scanned
XFA 없음
```

PDFium render로 1/2페이지를 이미지화하여 다음을 시각 확인했다.

- Header와 Body 충돌 없음
- Vertical Documentation Name / Week-Version 위치 정상
- 2페이지 Header 미출력
- Footer 반복 정상
- clipping 없음
- Dummy bullet/heading missing glyph 없음
- 1페이지와 2페이지 body start 차이 정상

## App icon 검증

```text
assets/app_icon_1024.png
→ 1024 x 1024 RGB PNG

assets/SozakPDFLayoutDesigner.icns
→ valid Mac OS X icon file
```

디자인: **흰 배경 PDF 문서 + 큰 갈색 Fedora**.

## Build script 검증

정적 shell syntax와 spec Python syntax를 통과했다.

Mac에서 실행 시 순서:

```text
1. Python 탐색
2. build venv
3. PyInstaller / PyMuPDF / PyYAML
4. PNG → ICNS (sips/iconutil)
5. release_smoke_test.py
6. http_smoke_test.py
7. PyInstaller .app
8. ad-hoc codesign
9. versioned ZIP / DMG
```

예상 산출물:

```text
dist/Sozak PDF Layout Designer.app
dist/Sozak_PDF_Layout_Designer_v0.10.0_macOS.zip
dist/Sozak_PDF_Layout_Designer_v0.10.0_macOS.dmg
```

## macOS에서 남은 최종 검증

이 항목은 **아직 실행되지 않은 것**으로 명확히 남긴다.

- [ ] `build-macos-app.command` 실제 zsh 실행
- [ ] PyInstaller app 생성
- [ ] Fedora app icon Finder/Dock 표시
- [ ] ad-hoc `codesign` 성공
- [ ] DMG mount/create
- [ ] Applications drag 설치
- [ ] Gatekeeper first-launch
- [ ] 설치된 app에서 Dummy export
- [ ] 설치된 app에서 real Body export
- [ ] 가능하면 Intel/Apple Silicon 대상 architecture 확인

현재 spec은 `target_arch=None`이므로 실제 executable architecture는 빌드 Mac/Python에 영향을 받는다.

## 배포 관련 제한

현재 설계는 ad-hoc signing이다. 공개 배포에서 Gatekeeper 경고를 최소화하려면 향후 다음이 필요하다.

```text
Apple Developer ID Application signing
→ notarization
→ stapling
```

## 문서 수정 이력

| 문서 버전 | 날짜 | 기준 앱 | 내용 |
|---|---|---|---|
| 1.0 | 2026-08-19 | v0.10.0 | 최초 v0.10.0 릴리스 검증 보고서 |

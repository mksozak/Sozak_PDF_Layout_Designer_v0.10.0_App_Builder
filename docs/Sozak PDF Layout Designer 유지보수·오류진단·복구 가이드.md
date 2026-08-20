---
title: "Sozak PDF Layout Designer 유지보수·오류진단·복구 가이드"
author: "Moonkyu Lee"
created: 2026-08-19
updated: 2026-08-19
type: guide
phase: seedling
status: active
project: "[[Sozak PDF Layout Designer]]"
tags:
  - "sozak-pdf-layout-designer"
  - "maintenance"
  - "troubleshooting"
  - "recovery"
  - "macos"
  - "codex"
aliases:
  - "PDF Layout Designer Troubleshooting"
derived_from:
  - "[[Sozak PDF Layout Designer 개발 아키텍처와 코드 구조]]"
version: "1.1"
description: "v0.10.0 설치·실행·preview·actual PDF·Smart Guides·Dummy·metadata·font·build 오류를 안전하게 진단하는 가이드."
note: "재현과 읽기 전용 진단을 먼저 하고 홈 폴더 전체 재귀 명령을 금지한다."
---
# Sozak PDF Layout Designer 유지보수·오류진단·복구 가이드

## 1. 기본 진단 순서

```text
증상 기록 → 재현 → 로그 → 영향 범위 → 읽기 전용 확인
→ smoke test → 최소 수정 → 실제 PDF → 회귀 test → release
```

## 2. 먼저 실행할 것

개발 source가 있다면:

```bash
python3 -m py_compile sozak_pdf_designer.py sozak_pdf_overlay.py tests/release_smoke_test.py
python3 tests/release_smoke_test.py
python3 tests/http_smoke_test.py
```

이 단계가 실패하면 UI를 임의로 다시 작성하기보다 첫 실패 test를 원인 단서로 사용한다.

## 3. 위험 명령

경로 확인 없이 다음을 하지 않는다.

```text
xattr -dr ... .
chmod -R ... .
rm -rf ...
```

특히 `~`가 현재 디렉터리면 홈 전체를 건드릴 수 있다.

## 4. 친구 Mac에서 앱 차단

```bash
ls -ld "/Applications/Sozak PDF Layout Designer.app"
```

존재 확인 후:

```bash
xattr -dr com.apple.quarantine "/Applications/Sozak PDF Layout Designer.app"
open "/Applications/Sozak PDF Layout Designer.app"
```

권한 문제일 때만 `sudo`를 사용한다.

## 5. 앱/아키텍처/서명

```bash
sw_vers
uname -m
file "/Applications/Sozak PDF Layout Designer.app/Contents/MacOS/Sozak PDF Layout Designer"
codesign -dv --verbose=4 "/Applications/Sozak PDF Layout Designer.app"
```

## 6. 브라우저가 안 열림

가능성:

- local server 시작 실패
- 8765~8784 포트 범위 문제
- browser auto-open 실패
- PyInstaller resource path

개발 source:

```bash
python3 sozak_pdf_designer.py --no-browser
```

출력 URL을 직접 연다.

## 7. Dummy가 안 보임 / 2페이지가 안 됨

관련:

```text
HTML dummyPages / dummy preview render
preview page state
page.first_top / other_top
```

Body PDF가 없어도 1P/2P가 동작해야 한다.

## 8. Dummy PDF 내보내기 실패

관련:

```text
sozak_pdf_designer.py /api/pick-output /api/generate
sozak_pdf_overlay.py stamp_dummy_pdf / draw_dummy_body
```

정상은 2페이지이며 Header는 1페이지, Footer는 양쪽 페이지에 출력된다.

## 9. 실제 Body PDF preview 실패

확인:

- file 존재
- PDF 손상/암호화
- page index
- PyMuPDF open
- `/api/pdf-info`
- `/api/pdf-preview`

## 10. Preview와 actual PDF가 다름

우선 비교:

```text
sozak_pdf_designer.html render/state
vs
sozak_pdf_overlay.py apply_selected_layout/draw_header/draw_footer
```

X/Y/Width/enabled를 함께 비교한다.

## 11. 요소 토글이 layout 전환 후 풀림

Header:

```text
line.enabled
layouts.<layout>.info.line_enabled[]
logo/divider/series/right_rule enabled
captureActiveLayout/applyLayoutGeometry
```

Footer는 layout-independent이므로 Horizontal/Vertical 전환에 따라 바뀌지 않아야 한다.

## 12. Vertical Documentation Name이 안 보임

기본 preset:

```text
header.layouts.vertical.series.enabled = true
header.series.enabled = true (Vertical active baseline)
```

layout switch 후 apply가 false로 덮어쓰지 않는지 본다.

## 13. Smart Guides가 안 뜸

Smart Guides는 PDF overlay 기능이 아니라 browser interaction이다.

확인:

```text
showSmartGuides
pointer/input lifecycle
guide overlay elements
current active element bounds
```

Snap을 꺼도 guide 자체는 표시 가능해야 한다.

## 14. Snap이 너무 강함/약함

현재 약 1.5mm tolerance 기준이다. UX를 바꿀 수 있지만 guide와 snap toggle을 하나로 합치지 않는다.

## 15. Footer X/Width 문제

관련 schema:

```text
line1_x / line2_x
line1_width / line2_width
```

실제 PDF에서도 각 line이 독립 이동해야 한다. width가 커지면 max X가 작아지는 것이 정상이다.

## 16. Footer quick-align이 틀림

page margin 기준을 사용해야 한다.

```text
left = page.left
right edge = 210 - page.right
```

텍스트 block width까지 포함해 X를 계산한다.

## 17. Right Rule가 왼쪽으로 안 감

UI range가 `0..210`인지 확인하고 actual PDF `x`도 clamp하지 않는지 본다. smoke test는 5mm와 205mm를 검증한다.

## 18. YAML Week/Version 문제

새 canonical:

```yaml
week_version: "VERSION 1.2"
```

legacy:

```yaml
week: "08"
```

도 읽어야 한다. parser의 key normalization과 `_present`를 확인한다.

## 19. YAML에 강사가 없는데 강사가 지워짐/덮어씀

v0.10.0에서 raw key 존재 여부를 먼저 기록한다. `instructors`가 YAML에 없으면 `_present`에도 없어야 하며 기존 Designer 값이 불필요하게 overwrite되지 않아야 한다.

## 20. App icon이 안 보임

확인:

```text
assets/app_icon_1024.png
assets/SozakPDFLayoutDesigner.icns
SozakPDFLayoutDesigner.spec icon=
build script sips/iconutil result
```

앱 아이콘 캐시 때문에 Finder가 이전 icon을 잠시 보여줄 수도 있으므로 새 app bundle 자체에 icon file이 포함되었는지 먼저 본다.

## 21. Page Margin 바꿨는데 실제 Body 본문이 안 움직임

정상일 수 있다. 이미 만든 Body PDF를 Designer가 재조판하지 않는다.

```text
margin 변경 → CSS 저장 → Typora Body PDF 재출력 → 다시 선택
```

Dummy Body는 Designer가 직접 생성하므로 현재 margin을 사용한다.

## 22. Build 실패

먼저:

```bash
pwd
ls -l ./build-macos-app.command
python3 --version
```

release smoke / HTTP smoke에서 실패했는지 PyInstaller/codesign/hdiutil 단계에서 실패했는지 로그를 분리한다.

`.build-venv` 삭제가 필요해도 App Builder 폴더 안이 맞는지 `pwd`를 확인한 뒤에만 한다.

## 23. 오류 보고에 필요한 자료

```text
앱/source version
macOS version
uname -m
재현 순서
정확한 오류 문구/screenshot
preset JSON
YAML/MD (metadata 문제 시)
Body PDF (real workflow 문제 시)
output PDF
smoke-test output
```

## 문서 수정 이력

| 문서 버전 | 날짜 | 기준 앱 | 내용 |
|---|---|---|---|
| 1.0 | 2026-08-19 | v0.9.2 | 최초 오류진단·복구 통합 |
| 1.1 | 2026-08-19 | v0.10.0 | Dummy/Smart Guides/visibility/Footer/week_version/icon/smoke-test 진단 추가 |

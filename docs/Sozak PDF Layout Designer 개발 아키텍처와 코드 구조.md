---
title: "Sozak PDF Layout Designer 개발 아키텍처와 코드 구조"
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
  - "architecture"
  - "python"
  - "javascript"
  - "pymupdf"
  - "macos"
aliases:
  - "PDF Layout Designer Architecture"
derived_from:
  - "[[Sozak PDF Layout Designer 개발문서 허브]]"
version: "1.1"
description: "v0.10.0 기준 런타임 구조, 주요 파일, API, preset schema, preview/overlay, Dummy PDF 및 Smart Guides 설계."
note: "UI geometry나 preset schema가 바뀌면 preview와 overlay 양쪽을 함께 점검하고 이 문서를 갱신할 것."
---
# Sozak PDF Layout Designer 개발 아키텍처와 코드 구조

## 1. 제품 정의

**Typora 등에서 만든 Body PDF를 그대로 배경으로 사용하거나, Body PDF가 없으면 2페이지 Dummy Body를 생성하고, Header·Footer·Logo·Line·Page Number를 브라우저 Designer에서 시각적으로 배치해 PyMuPDF로 최종 PDF를 합성하는 macOS 로컬 앱**이다.

## 2. 두 가지 출력 경로

```text
[A. 실제 문서]
Body PDF ─┐
YAML/MD ──┼→ Designer/Preset → PyMuPDF overlay → Final PDF
          │
[B. 테스트]
Body 없음 ─→ Dummy 2-page Body 생성 ────────┘
```

역할 분리:

- `sozak_pdf_designer.html`: 시각 편집·preview·Smart Guides/Snap
- `sozak_pdf_designer.py`: local HTTP server, Finder dialog, YAML, preview raster, export routing
- `sozak_pdf_overlay.py`: 실제 PDF의 source of truth; real/dummy 출력
- `presets/howon-handout.json`: 기본 상태와 layout schema
- `tests/release_smoke_test.py`: PDF/schema/UI feature 회귀 gate
- `tests/http_smoke_test.py`: local API integration gate
- `tests/ui_runtime_smoke_test.py`: Playwright/Chromium이 있을 때 Dummy page, toggle, Coffee, Footer align, Smart Guides/Snap, Reset을 실제 DOM interaction으로 검증하는 선택적 test
- `build-macos-app.command`: macOS app/ZIP/DMG builder + 사전 테스트

## 3. v0.10.0 파일 구조

```text
Sozak_PDF_Layout_Designer_v0.10.0_App_Builder/
├── README.md
├── CHANGELOG.md
├── SozakPDFLayoutDesigner.spec
├── build-macos-app.command
├── start-designer.command
├── sozak_pdf_designer.html
├── sozak_pdf_designer.py
├── sozak_pdf_overlay.py
├── sozak-pdf-body.css
├── demo-body.md
├── demo-body.pdf
├── demo-final.pdf
├── demo-dummy-final.pdf
├── presets/
│   └── howon-handout.json
├── tests/
│   ├── release_smoke_test.py
│   ├── http_smoke_test.py
│   └── ui_runtime_smoke_test.py
├── docs/
│   └── 개발문서 9종
└── assets/
    ├── app_icon_1024.png
    ├── SozakPDFLayoutDesigner.icns
    └── built-in logos 7종
```

## 4. Header data model

기본 시작 layout:

```text
header.layout = vertical
```

하나의 preset 안에 두 layout을 함께 저장한다.

```text
header.layouts.horizontal
header.layouts.vertical
```

### Header line

기관명, 메인 제목, 강사 블록은 각각 다음을 가진다.

```text
text
x
y
width
size
font
bold
color
enabled
```

layout별 geometry/visibility:

```text
info.line_x[]
info.line_y[]
info.line_width[]
info.line_enabled[]
```

`enabled`와 `line_enabled[]`의 의미가 충돌하지 않도록 현재 layout을 capture/apply 할 때 동기화해야 한다.

### Horizontal auto-after-logo

Horizontal 기본:

```text
info.auto_after_logo = true
```

로고 폭을 늘리면 information group 기준 X가 로고 오른쪽 + gap으로 이동한다. 개별 `line_x`는 group 기준에 대한 offset을 유지하므로 v0.10.0의 요소별 X 기능과 함께 작동한다.

Vertical 기본은 `auto_after_logo=false`다.

## 5. 요소별 표시/숨김

UI panel 좌측 원형 토글:

```text
● 표시
○ 숨김
```

Header:

- Logo
- Institution
- Main title
- Instructor block
- Divider
- Documentation Name / Week-Version
- Right Rule

Header의 visibility는 Horizontal/Vertical별로 독립 저장한다.

Footer:

- Footer Line
- Footer 1
- Footer 2
- Page Number

Footer visibility는 layout과 무관한 전역 footer 설정이다.

## 6. Documentation Name / Week-Version

과거 UI 이름 `Series / Week`의 역할은 v0.10.0에서 의미를 명확히 하여 다음 metadata를 사용한다.

```yaml
documentation_name: "CLASS HANDOUT WEEKLY SERIES"
week_version: "WEEK 08"
```

표시 문자열:

```text
CLASS HANDOUT WEEKLY SERIES · WEEK 08
```

`week_version: "VERSION 1.2"`처럼 주차가 아닌 문서 버전도 쓸 수 있다.

호환 alias:

```text
week
week version
week-version
week/version
weekVersion
```

새 저장/작성 기준은 `week_version`이다.

## 7. Footer v0.10.0 model

Footer 1과 Footer 2가 독립적으로 가진다.

```text
line1_enabled / line2_enabled
line1_x / line2_x
line1_y / line2_y
line1_width / line2_width
line1_size / line2_size
line1_font / line2_font
line1_bold / line2_bold
line1_color / line2_color
```

legacy `text.x`, `text.width`, `y`, `line_gap`은 load 시 fallback/migration 용도로만 유지한다.

X slider의 실질 최대값은 텍스트 block이 A4 밖으로 나가지 않도록:

```text
maxX = 210 - textWidth
```

로 제한한다.

빠른 정렬은 현재 page margin을 사용한다.

```text
본문 좌측   = page.left
본문 우측   = 210 - page.right - textWidth
본문 가운데 = body 영역 중앙 - textWidth / 2
```

## 8. Right Rule

v0.10.0 UI X 범위:

```text
0 ~ 210 mm
```

실제 PDF에서도 near-left와 near-right 좌표가 정상 출력되는지를 regression test로 확인한다.

## 9. Preview system

Body PDF가 있으면 Python server가 해당 페이지를 PNG로 rasterize해 HTML preview 배경으로 제공한다.

Body PDF가 없으면 HTML/CSS로 2페이지 Dummy 문서를 그린다. Dummy에는 H1/H2/본문/목록/인용/표가 포함되어 Header와 Footer가 실제 본문과 충돌하지 않는지 볼 수 있다.

Preview page controls는 Body 유무와 무관하게 1페이지/2페이지를 지원한다.

## 10. Smart Guides + Snap

Smart Guides는 `sozak_pdf_designer.html`에만 존재하는 **preview interaction layer**다.

이동/폭 조절 중:

- 선택 요소 left / center / right
- A4 edge 0 / 210
- page.left / 210-page.right
- page center 105
- 다른 visible element의 left / center / right
- 주요 Y target

을 비교해 안내선을 잠시 표시한다.

Snap은 별도 checkbox이며 약 1.5mm 근처에서 target에 붙는다. Smart Guides와 Snap은 서로 독립적으로 끌 수 있다.

최종 PDF에는 guide가 그려지지 않는다.

## 11. Position Reset / Bounds Warning

`↺ 위치 초기화`는 현재 text/style은 유지하고 해당 요소의 기본 geometry/visibility를 current layout default로 복원한다.

A4 bounds warning은 preview에서 요소가 종이 밖으로 나간 경우 경고만 제공하고 강제로 이동시키지 않는다.

## 12. Dummy PDF export

`sozak_pdf_overlay.py`의 핵심 경로:

```text
stamp_pdf(body_pdf, preset, output)
stamp_dummy_pdf(preset, output)
```

`stamp_dummy_pdf()`는 A4 2페이지를 만들고 `draw_dummy_body()`로 샘플 본문을 그린 뒤 같은 `draw_header()` / `draw_footer()`를 사용한다. 따라서 실제/더미 출력이 동일한 overlay code path를 공유한다.

서버 `/api/generate`가 Body path 유무에 따라 두 함수를 선택한다.

Dummy 출력 기본 후보:

```text
~/Desktop/Sozak PDF Layout Test (1).pdf
```

같은 이름이 있으면 `(2)`, `(3)` 순으로 올린다.

## 13. 안전한 내보내기

실제 Body PDF가 있을 때 source와 output path가 같으면 server-side에서 거부한다. UI를 우회해도 원본 overwrite가 되지 않아야 한다.

```text
Lecture.pdf
→ Lecture (1).pdf
→ Lecture (2).pdf
```

Dummy는 source가 없으므로 별도의 numbered test filename을 제안한다.

## 14. YAML parser

canonical:

```text
instructors
institution
department
course
semester
week_version
date
documentation_name
footer1
footer2
```

v0.10.0에서는 `_present`를 raw normalization 전에 계산하여 YAML에 없는 `instructors`를 존재한 것으로 오인하던 문제를 수정했다.

## 15. App icon

원본 PNG:

```text
assets/app_icon_1024.png
```

준비된 ICNS:

```text
assets/SozakPDFLayoutDesigner.icns
```

이미지는 흰 배경의 PDF 문서가 큰 갈색 Fedora를 쓴 형태다. spec은 ICNS를 app icon으로 지정한다. macOS builder는 가능하면 `sips` + `iconutil`로 PNG에서 ICNS를 다시 생성한다.

## 16. Coffee button

UI 우측 상단의:

```text
☕ 개발자에게 커피 사기
```

클릭 시 local toast:

```text
만나서 사주세요. ☕
```

만 표시하며 외부 URL/결제 기능은 없다.

## 17. API

GET:

| Endpoint | 역할 |
|---|---|
| `/` | Designer HTML |
| `/api/pdf-preview?path=...&page=...` | 실제 PDF page PNG |
| `/api/image?path=...` | Logo image |

POST:

| Endpoint | 역할 |
|---|---|
| `/api/default` | 기본 preset/CSS/logo |
| `/api/pdf-info` | page count/size |
| `/api/load-metadata` | YAML front matter |
| `/api/find-sibling-metadata` | same-stem metadata 탐색 |
| `/api/pick` | 파일 선택 |
| `/api/pick-output` | real/dummy save dialog + numbered name |
| `/api/load-preset` | preset load |
| `/api/save-preset` | preset save |
| `/api/save-css` | page margin CSS |
| `/api/generate` | real or dummy PDF generate |

## 18. 렌더링 일치 원칙

geometry를 바꾸면 다음 chain 전체가 같은 의미를 가져야 한다.

```text
preset default
→ normalize/migration
→ UI control
→ event binding
→ layout capture/apply
→ preview render
→ preset save/load
→ overlay apply_selected_layout
→ draw_header/draw_footer
→ actual PDF regression test
```

Preview만 맞거나 PDF만 맞으면 미완료다.

## 19. 자동 회귀 테스트

```bash
python3 tests/release_smoke_test.py
python3 tests/http_smoke_test.py
```

`release_smoke_test.py`는 schema, metadata alias, Horizontal/Vertical visibility independence, footer X, Header X, Right Rule 전체 X, dummy 2-page, real Body workflow, safe numbering을 실제 PDF 생성까지 검사한다. `http_smoke_test.py`는 `/api/default`, real/dummy `/api/generate`, source overwrite 409, `week_version`, PDF info를 실제 local HTTP server로 검사한다. `ui_runtime_smoke_test.py --require`는 브라우저가 있는 개발 환경에서 실제 UI interaction을 추가 검증한다.

## 문서 수정 이력

| 문서 버전 | 날짜 | 기준 앱 | 내용 |
|---|---|---|---|
| 1.0 | 2026-08-19 | v0.9.2 | 최초 아키텍처 문서 |
| 1.1 | 2026-08-19 | v0.10.0 | v0.10.0 전체 schema/preview/dummy/test/icon 구조 반영 |

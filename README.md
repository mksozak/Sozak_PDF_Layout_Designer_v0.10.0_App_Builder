---
title: "Sozak PDF Layout Designer v0.10.0 macOS App Builder"
author: "Moonkyu Lee"
created: 2026-08-19
updated: 2026-08-19
type: documentation
phase: source
status: stable
version: "0.10.0"
description: "Smart Guides/Snap, 요소별 표시 토글, Vertical Series 기본 표시, Footer 독립 X·Width와 여백 정렬, Body PDF 없는 2페이지 Dummy PDF 출력, week_version YAML, 앱 아이콘과 자동 회귀 테스트를 포함한 macOS App Builder."
note: "새 릴리스에서 코드가 바뀌면 docs의 CHANGELOG와 릴리스 체크리스트도 함께 갱신할 것."
---

# Sozak PDF Layout Designer v0.10.0

`Sozak PDF Layout Designer`는 Typora 등에서 출력한 **Body PDF를 배경으로 두고**, Header·Footer·Logo·Line·Page Number를 시각적으로 배치한 뒤 PyMuPDF로 최종 PDF를 합성하는 로컬 macOS 앱이다.

v0.10.0은 배치 편집 기능과 테스트/유지보수 체계를 크게 확장한 릴리스다.

## v0.10.0 핵심 변경

### 1. Vertical에서도 Documentation Name · Week / Version 표시

기존 v0.9.2의 Vertical layout에는 Series 영역 좌표가 있었지만 기본 `enabled: false`라 보이지 않았다.

v0.10.0 기본 preset에서는 Vertical도 다음 영역을 표시한다.

```text
Documentation Name · Week / Version
```

Horizontal과 Vertical 각각 위치와 표시 상태를 독립 저장한다.

### 2. 요소별 표시 / 숨김

각 편집 패널 제목 왼쪽의 작은 원형 버튼으로 요소를 즉시 넣고 뺄 수 있다.

```text
● 표시
○ 숨김
```

대상:

- Logo
- 기관 / 대학명
- 메인 제목
- 강사 1 / 강사 2
- Header Divider
- Documentation Name · Week / Version
- Right Rule
- Footer Line
- 꼬리말 1
- 꼬리말 2
- 페이지 번호

Header 요소의 표시 상태는 Horizontal / Vertical별로 독립 저장된다.

### 3. 위치 초기화

각 요소 패널에 `↺ 위치 초기화`가 추가되었다.

현재 입력된 텍스트와 스타일은 보존하면서 현재 Header Layout의 기본 위치/폭/표시 상태로 돌아간다.

### 4. Right Rule X 전체 폭

우측 세로선의 X 범위를 기존 오른쪽 영역 제한에서 A4 전체 폭으로 확장했다.

```text
0 ~ 210 mm
```

### 5. Footer 1 / Footer 2 독립 X · Width

두 꼬리말은 이제 각각 다음 값을 가진다.

```text
Text
X position
Text width
Y position
Font size
Font
Weight
Color
```

X는 텍스트 블록이 A4 밖으로 나가지 않는 범위에서 왼쪽 끝부터 오른쪽 끝까지 움직인다.

### 6. Footer 빠른 정렬

꼬리말 1·2 각각에 다음 버튼이 있다.

```text
[본문 좌측] [본문 가운데] [본문 우측]
```

현재 `Page Margins`의 본문 안쪽 경계를 기준으로 X를 자동 계산한다.

예: Left 20 mm / Right 20 mm이면 본문 영역은 20~190 mm다.

### 7. Smart Guides + Snap

슬라이더로 X/Y/Width를 움직이는 동안에만 Photoshop식 정렬 안내선이 나타난다.

기준:

- A4 왼쪽 / 가운데 / 오른쪽
- 현재 Page Margins의 좌·우 경계
- 다른 표시 중인 요소의 왼쪽 / 가운데 / 오른쪽
- Y 방향의 주요 정렬 위치

`Smart Guides`와 `Snap`은 따로 ON/OFF할 수 있다. Snap은 약한 범위 안에서만 정렬점에 붙는다.

Smart Guides는 preview 전용이며 최종 PDF에는 출력되지 않는다.

### 8. A4 밖 요소 경고

표시 중인 요소가 페이지 경계를 벗어나면 preview 위에 경고가 나타난다. 위치를 강제로 막지는 않으므로 개발/디자인 의도에 따라 다시 조절할 수 있다.

### 9. Body PDF 없는 2페이지 Dummy Document

Body PDF를 선택하지 않아도 Designer가 자동으로 2페이지짜리 샘플 본문을 보여준다.

Dummy에는 다음이 포함된다.

- H1
- H2
- 본문 단락
- bullet list
- numbered list
- quote block
- 간단한 table

1페이지와 2페이지의 서로 다른 Top margin, Footer 반복, 페이지 번호 등을 실제 문서처럼 검토할 수 있다.

### 10. Body PDF 없이도 테스트 PDF 내보내기

Body PDF가 없을 때 `더미 테스트 PDF 내보내기…`를 누르면 화면용 더미가 아니라 **실제 2페이지 PDF**를 생성하고 현재 Header/Footer를 합성한다.

Body PDF가 있으면 기존처럼 실제 Body PDF를 기반으로 출력한다.

```text
Body PDF 있음  → Body PDF + Header/Footer
Body PDF 없음  → 2-page Dummy Body + Header/Footer
```

### 11. YAML: `documentation_name` + `week_version`

새 canonical metadata:

```yaml
documentation_name: "CLASS HANDOUT WEEKLY SERIES"
week_version: "WEEK 08"
```

출력:

```text
CLASS HANDOUT WEEKLY SERIES · WEEK 08
```

버전 문서도 가능하다.

```yaml
documentation_name: "CLT WORKSHOP HANDOUT"
week_version: "VERSION 1.2"
```

기존 YAML의 `week:`는 하위 호환 alias로 계속 읽는다. `week/version`, `week version`, `week-version`, `weekVersion`도 정규화한다.

### 12. Preset은 디자인 + 입력 텍스트 전체 스냅샷

Preset JSON에는 위치만이 아니라 현재 입력된 텍스트도 같이 저장된다.

- 기관명
- 메인 제목
- 강사 1·2
- Documentation Name / Week-Version 조합 텍스트
- Footer 1·2
- Page number format
- Logo path
- 요소별 enabled
- X/Y/Width
- 폰트·크기·굵기·색
- Horizontal / Vertical geometry

YAML은 필요할 때 문서별 metadata로 해당 텍스트를 덮어쓴다.

### 13. 앱 아이콘

`assets/app_icon_1024.png`에 PDF 문서가 큰 갈색 Fedora를 쓴 아이콘을 포함한다.

`build-macos-app.command`는 macOS의 `sips` + `iconutil`을 사용해 `.icns`를 다시 만들고 앱에 적용한다. 준비된 `SozakPDFLayoutDesigner.icns`도 함께 포함되어 있다.

### 14. 개발자 커피 버튼

오른쪽 상단:

```text
☕ 개발자에게 커피 사기
```

클릭하면:

```text
만나서 사주세요. ☕
```

라고 나온다. 결제 기능은 없다.

## 기존 주요 기능 유지

- Vertical 기본 시작 layout
- Horizontal / Vertical 원클릭 전환
- 프리셋 하나에 두 Header Layout 저장
- Horizontal의 `로고 폭에 따라 텍스트 블록 자동 이동`
- Header 텍스트별 독립 X/Y/Width
- Margin Guides
- 실제 Body PDF 1·2페이지 preview
- YAML / Markdown metadata 자동 연결
- Built-in Logos 7종
- 설치된 Mac font 탐색
- Footer line / Page number
- 안전한 numbered output 이름
- 원본 Body PDF overwrite server-side 차단

## 권장 작업 흐름

Body PDF가 아직 없을 때:

```text
앱 실행
→ 2-page Dummy Preview
→ Header / Footer 설계
→ Smart Guides / 정렬 버튼으로 위치 조절
→ Dummy 테스트 PDF 출력
→ 레이아웃 검토
→ Preset 저장
```

실제 문서가 준비된 뒤:

```text
Body PDF 선택
→ 같은 stem의 Markdown/YAML 자동 검색·적용
→ 1·2페이지 실제 PDF 확인
→ 필요 시 미세조정
→ 최종 PDF 내보내기…
```

## macOS 앱 빌드

App Builder 폴더 안에서:

```bash
pwd
ls -l ./build-macos-app.command
./build-macos-app.command
```

빌더는 먼저 release smoke test를 실행한다. 테스트가 실패하면 앱 빌드를 중단한다.

성공 결과:

```text
dist/
├── Sozak PDF Layout Designer.app
├── Sozak_PDF_Layout_Designer_v0.10.0_macOS.zip
└── Sozak_PDF_Layout_Designer_v0.10.0_macOS.dmg
```

친구에게는 DMG 전달을 권장한다.

## 자동 회귀 테스트

직접 테스트:

```bash
python3 tests/release_smoke_test.py
python3 tests/http_smoke_test.py
# Playwright + Chromium이 있는 개발 환경에서 선택적으로:
python3 tests/ui_runtime_smoke_test.py --require
```

검사 항목에는 다음이 포함된다.

- Vertical Series 기본 표시
- Header element visibility
- Footer visibility
- Footer X 실제 PDF 이동량
- Header 독립 X 회귀
- Right Rule 5 mm / 205 mm 실제 PDF 위치
- 2-page Dummy PDF
- 기존 Body PDF workflow
- YAML `week_version` 및 legacy `week`
- metadata omitted-field 보존
- 안전한 real/dummy output numbering
- local HTTP default / dummy generate / real-body generate / overwrite 409 / metadata / PDF info
- 앱 아이콘 / 주요 UI feature 존재
- 선택적 browser interaction: Dummy 1/2P, Series toggle, Coffee, Footer align, Smart Guides/Snap, Reset

## 개발 문서

`docs/` 폴더를 먼저 읽는다.

특히:

- `Sozak PDF Layout Designer 개발문서 허브.md`
- `Sozak PDF Layout Designer 개발 아키텍처와 코드 구조.md`
- `Sozak PDF Layout Designer 버전 이력과 CHANGELOG.md`
- `Sozak PDF Layout Designer 수정·빌드·배포 가이드.md`
- `Sozak PDF Layout Designer 유지보수·오류진단·복구 가이드.md`
- `Sozak PDF Layout Designer 릴리스 체크리스트와 문서 동기화 규칙.md`
- `Sozak PDF Layout Designer Codex 개발·수정 작업지시 템플릿.md`

코드 변경과 문서 변경은 같은 릴리스 작업에서 처리한다.

릴리스 검증 결과는 루트의 `RELEASE_VERIFICATION.md`에 기록한다.

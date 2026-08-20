---
title: "Sozak PDF Layout Designer 수정·빌드·배포 가이드"
author: "Moonkyu Lee"
created: 2026-08-19
updated: 2026-08-19
type: guide
phase: seedling
status: active
project: "[[Sozak PDF Layout Designer]]"
tags:
  - "sozak-pdf-layout-designer"
  - "development"
  - "build"
  - "release"
  - "pyinstaller"
  - "dmg"
  - "macos"
aliases:
  - "PDF Layout Designer Build Guide"
derived_from:
  - "[[Sozak PDF Layout Designer 개발 아키텍처와 코드 구조]]"
  - "[[Sozak PDF Layout Designer 릴리스 체크리스트와 문서 동기화 규칙]]"
version: "1.1"
description: "v0.10.0 소스 수정부터 회귀 테스트, 버전 갱신, PyInstaller 앱 빌드, ZIP/DMG 배포까지의 표준 절차."
note: "빌드는 macOS에서 수행하며 build script의 smoke test가 실패하면 앱을 배포하지 않을 것."
---
# Sozak PDF Layout Designer 수정·빌드·배포 가이드

## 1. 수정 시작

기존 릴리스 폴더를 직접 덮어쓰기보다 전체 source를 복사해 새 working release를 만든다.

```text
v0.10.0 release
→ v0.10.1 or v0.11.0 working copy
```

최신 App Builder, 대표 Body PDF, 대표 preset, 개발문서, 정상 출력 PDF를 함께 둔다.

## 2. 파일별 책임

| 수정 내용 | 주 파일 | 함께 확인 |
|---|---|---|
| UI/slider/Smart Guide | `sozak_pdf_designer.html` | preset, overlay |
| Finder/YAML/API/export | `sozak_pdf_designer.py` | HTML, tests |
| actual PDF geometry | `sozak_pdf_overlay.py` | HTML preview, tests |
| default/schema | `presets/howon-handout.json` | normalization/migration |
| Body margin | `sozak-pdf-body.css` | Typora 재출력 |
| packaging | `.spec`, `build-macos-app.command` | icon/tests |
| regression | `tests/release_smoke_test.py`, `tests/http_smoke_test.py`, 선택적 `tests/ui_runtime_smoke_test.py` | changed feature |

## 3. Geometry 변경의 필수 chain

```text
preset default
→ normalize/migration
→ accessor/state
→ UI range + number input
→ binding
→ layout capture/apply
→ preview
→ preset save/load
→ overlay
→ actual PDF test
```

Footer X나 Header enabled처럼 저장 필드가 늘어나면 구버전 preset에 필드가 없을 때 어떻게 복원할지도 구현한다.

## 4. v0.10.0 이후 Metadata 규칙

새 문서:

```yaml
documentation_name: "..."
week_version: "WEEK 08"
```

`week`는 import alias일 뿐 새 canonical output으로 되돌리지 않는다.

## 5. 버전 갱신

버전 변경 전/후 문자열 검색:

```bash
grep -RIn --exclude='*.pdf' --exclude='*.png' --exclude='*.icns' "0.10.0" .
```

최소 확인 위치:

```text
HTML title/subtitle
Python server_version/startup
spec CFBundleShortVersionString/CFBundleVersion
preset version
README YAML/body
friend guide
CHANGELOG
development docs baseline/history
build output filename
```

과거 CHANGELOG 안의 이전 버전 문자열은 정상이다.

## 6. Syntax

```bash
python3 -m py_compile   sozak_pdf_designer.py   sozak_pdf_overlay.py   tests/release_smoke_test.py
```

HTML의 `<script>`를 임시 JS로 추출해 Node가 있으면:

```bash
node --check temporary-check.js
```

## 7. Release smoke test

v0.10.0부터 필수 gate:

```bash
python3 tests/release_smoke_test.py
python3 tests/http_smoke_test.py
```

첫 test는 실제 PDF와 schema/geometry를, 둘째 test는 local HTTP API를 검증한다. Playwright+Chromium이 있는 개발 환경에서는 `python3 tests/ui_runtime_smoke_test.py --require`로 실제 UI interaction도 검증한다. 단순 문자열 존재 검사만으로 대체하지 않는다.

새 기능이 들어가면 해당 기능의 **actual PDF effect** 또는 상태 persistence test를 추가한다.

## 8. PDF render 검토

자동 test 후 대표 PDF를 이미지로 render해 사람 눈으로도 확인한다.

권장:

```bash
python /home/oai/skills/pdfs/scripts/render_pdf.py   demo-dummy-final.pdf --out_dir /tmp/dummy-render --dpi 160
```

확인:

- clipping/overflow
- Header/Body 충돌
- footer/page number
- 1P/2P margin 차이
- 글꼴 fallback 이상

## 9. 개발 실행

폴더 확인:

```bash
pwd
ls -l ./start-designer.command
```

확인 후:

```bash
chmod +x ./start-designer.command
./start-designer.command
```

## 10. macOS build

폴더 확인:

```bash
pwd
ls -l ./build-macos-app.command
```

확인 후:

```bash
chmod +x ./build-macos-app.command
./build-macos-app.command
```

v0.10.0 builder 순서:

```text
Python 탐색
→ .build-venv
→ PyInstaller/PyMuPDF/PyYAML
→ PNG→ICNS 준비(sips/iconutil 가능 시)
→ release_smoke_test.py
→ http_smoke_test.py
→ PyInstaller
→ ad-hoc codesign
→ versioned ZIP
→ versioned DMG
```

Smoke test 실패 시 build를 중단한다.

## 11. App icon

원본:

```text
assets/app_icon_1024.png
```

spec이 사용하는 파일:

```text
assets/SozakPDFLayoutDesigner.icns
```

macOS에서 builder가 새 ICNS를 생성할 수 있다. 아이콘을 바꾸면 PNG와 ICNS 둘 다 source에 보존한다.

## 12. 아키텍처/서명

```bash
uname -m
file "dist/Sozak PDF Layout Designer.app/Contents/MacOS/Sozak PDF Layout Designer"
codesign -dv --verbose=4 "dist/Sozak PDF Layout Designer.app"
```

현재는 ad-hoc signing이며 notarized public distribution이 아니다. 경고 없는 공용 배포를 원하면 Developer ID + notarization + stapling이 별도로 필요하다.

## 13. 결과 파일

v0.10.0 builder:

```text
dist/Sozak PDF Layout Designer.app
dist/Sozak_PDF_Layout_Designer_v0.10.0_macOS.zip
dist/Sozak_PDF_Layout_Designer_v0.10.0_macOS.dmg
```

## 14. DMG install test

```text
DMG mount
→ app to Applications
→ launch
→ Dummy 1/2 page
→ Dummy export
→ Body PDF load
→ Horizontal/Vertical
→ Smart Guides/Snap
→ visibility toggle
→ final Body export
```

## 15. 안전한 Terminal 원칙

`xattr`, `chmod`, `rm -rf` 전에 정확한 path를 확인한다. 특히 `xattr -dr com.apple.quarantine .`를 홈 폴더에서 실행하지 않는다.

친구 앱 quarantine은 앱 하나만:

```bash
xattr -dr com.apple.quarantine "/Applications/Sozak PDF Layout Designer.app"
```

## 문서 수정 이력

| 문서 버전 | 날짜 | 기준 앱 | 내용 |
|---|---|---|---|
| 1.0 | 2026-08-19 | v0.9.2 | 최초 수정·빌드·배포 표준화 |
| 1.1 | 2026-08-19 | v0.10.0 | smoke-test gate, Dummy, icon, versioned build 산출물 반영 |

---
title: "Sozak PDF Layout Designer 친구용 설치·실행 설명서"
author: "Moonkyu Lee"
created: 2026-08-19
updated: 2026-08-19
type: guide
phase: seedling
status: active
project: "[[Sozak PDF Layout Designer]]"
tags:
  - "sozak-pdf-layout-designer"
  - "installation"
  - "macos"
  - "friend-guide"
aliases:
  - "PDF Layout Designer 친구용 설치"
derived_from:
  - "[[Sozak PDF Layout Designer 개발문서 허브]]"
version: "1.1"
description: "v0.10.0 DMG 설치, Dummy/Body PDF 사용, 첫 실행 및 Gatekeeper 대응을 위한 친구용 설명서."
note: "친구는 App Builder가 아니라 DMG를 받고, 정상 사용에는 Python/Anaconda/PyMuPDF 설치가 필요 없다."
---
# Sozak PDF Layout Designer 친구용 설치·실행 설명서

## 설치

1. `Sozak_PDF_Layout_Designer_v0.10.0_macOS.dmg`를 연다.
2. `Sozak PDF Layout Designer.app`을 Applications로 드래그한다.
3. Applications에서 실행한다.

정상 사용에는 Python/Anaconda/PyMuPDF/PyYAML을 따로 설치할 필요가 없다.

## 처음 열면

Body PDF가 없어도 2페이지 Dummy 문서가 보인다. 이 상태에서 Header/Footer 위치를 설계하고 `더미 테스트 PDF 내보내기…`로 실제 2페이지 검토용 PDF를 만들 수 있다.

실제 문서 작업:

```text
Body PDF 선택
→ 필요 시 같은 stem YAML/MD 자동 적용
→ Horizontal/Vertical
→ 요소 ON/OFF, X/Y/Width, Footer 정렬
→ 1/2page preview
→ 최종 PDF 내보내기
```

## YAML 예시

```yaml
---
documentation_name: "CLASS HANDOUT WEEKLY SERIES"
week_version: "WEEK 08"
institution: "DEPT. PHYSICAL THERAPY | HOWON UNIVERSITY"
course: "NEUROLOGICAL PHYSICAL THERAPY"
instructors:
  - "Name 1"
  - "Name 2"
footer1: "Neurological Physical Therapy 2026"
footer2: "DEPT. PHYSICAL THERAPY | HOWON UNIVERSITY"
---
```

기존 `week:`도 읽지만 새 문서에는 `week_version:`을 권장한다.

## 첫 실행 차단

먼저 Finder → Applications → 앱 우클릭 → **열기**.

그래도 차단되면 앱 하나만 대상으로:

```bash
xattr -dr com.apple.quarantine "/Applications/Sozak PDF Layout Designer.app"
open "/Applications/Sozak PDF Layout Designer.app"
```

권한 오류일 때만:

```bash
sudo xattr -dr com.apple.quarantine "/Applications/Sozak PDF Layout Designer.app"
open "/Applications/Sozak PDF Layout Designer.app"
```

`sudo` password 입력 중 문자가 보이지 않는 것은 정상이다.

## 하지 말 것

홈 폴더 등에서:

```bash
xattr -dr com.apple.quarantine .
```

를 실행하지 않는다.

## 오류 보고

```bash
sw_vers
uname -m
ls -ld "/Applications/Sozak PDF Layout Designer.app"
xattr "/Applications/Sozak PDF Layout Designer.app"
file "/Applications/Sozak PDF Layout Designer.app/Contents/MacOS/Sozak PDF Layout Designer"
```

결과와 screenshot, 문제가 난 preset/YAML/PDF를 개발자에게 전달한다.

## 참고

현재 배포는 ad-hoc signing 기반일 수 있어 다른 Mac에서 첫 실행 경고가 나타날 수 있다. 정식 Developer ID notarization이 도입되면 이 절차는 단순화될 수 있다.

## 문서 수정 이력

| 문서 버전 | 날짜 | 기준 앱 | 내용 |
|---|---|---|---|
| 1.0 | 2026-08-19 | v0.9.2 | 최초 통합 |
| 1.1 | 2026-08-19 | v0.10.0 | Dummy workflow와 week_version, v0.10.0 설치 내용 반영 |

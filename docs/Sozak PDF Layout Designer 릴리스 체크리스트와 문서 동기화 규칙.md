---
title: "Sozak PDF Layout Designer 릴리스 체크리스트와 문서 동기화 규칙"
author: "Moonkyu Lee"
created: 2026-08-19
updated: 2026-08-19
type: documentation-ai
phase: seedling
status: active
project: "[[Sozak PDF Layout Designer]]"
tags:
  - "sozak-pdf-layout-designer"
  - "release"
  - "governance"
  - "documentation"
  - "checklist"
  - "versioning"
aliases:
  - "PDF Layout Designer Release Checklist"
derived_from:
  - "[[Sozak PDF Layout Designer 개발문서 허브]]"
version: "1.1"
description: "v0.10.0 이후 코드·버전·테스트·문서·아이콘·산출물을 동시에 갱신하기 위한 release gate."
note: "코드 빌드 성공만으로 릴리스 완료로 보지 않고 checklist와 실제 PDF/DMG 검증까지 완료할 것."
---
# Sozak PDF Layout Designer 릴리스 체크리스트와 문서 동기화 규칙

## 1. Release gate

다음이 모두 충족되어야 release로 본다.

```text
source complete
syntax pass
smoke test pass
actual PDF visual review
version strings aligned
docs updated
macOS build pass
DMG install/launch pass
artifacts archived
```

## 2. 변경 → 문서 매핑

| 변경 | 확인 문서 |
|---|---|
| UI/Smart Guides | Architecture, CHANGELOG, Troubleshooting |
| preset schema/enabled | Architecture, CHANGELOG, Troubleshooting |
| Footer geometry | Architecture, CHANGELOG, Build, Troubleshooting |
| YAML canonical | Architecture, CHANGELOG, Troubleshooting, Codex docs |
| Dummy preview/export | Architecture, CHANGELOG, Troubleshooting, Friend Guide |
| build/spec/icon | Build, CHANGELOG, Troubleshooting |
| install/Gatekeeper | Friend Guide, Troubleshooting |
| test change | Build, Release Checklist, CHANGELOG |

## 3. Version string

- [ ] HTML title/subtitle
- [ ] Python server_version/startup
- [ ] spec CFBundle versions
- [ ] preset version
- [ ] README YAML/body
- [ ] build ZIP/DMG name
- [ ] friend guide
- [ ] CHANGELOG
- [ ] docs baseline/history

## 4. Syntax

- [ ] Python compile
- [ ] JavaScript `node --check` 가능한 환경에서 통과

## 5. Automated regression

- [ ] `python3 tests/release_smoke_test.py`
- [ ] `python3 tests/http_smoke_test.py`
- [ ] 브라우저 환경이 있으면 `python3 tests/ui_runtime_smoke_test.py --require`
- [ ] 새 기능을 테스트가 실제로 다룸
- [ ] Dummy PDF 2 pages
- [ ] Header first page only
- [ ] Footer all pages
- [ ] Vertical default/Series visible
- [ ] Header visibility
- [ ] Series visibility
- [ ] Footer visibility
- [ ] Footer X actual movement
- [ ] Header independent X
- [ ] Right Rule full-page X
- [ ] week_version aliases
- [ ] omitted metadata preservation
- [ ] real Body workflow
- [ ] safe numbered output
- [ ] HTTP default/dummy/real-body/overwrite/week_version/pdf-info

## 6. UI/manual

- [ ] Body 없음 → Dummy 1P/2P
- [ ] Body 없음 → Dummy export
- [ ] Body 있음 → actual preview 1P/2P
- [ ] Horizontal/Vertical 전환
- [ ] 각 요소 ●/○
- [ ] Position Reset
- [ ] Smart Guides ON/OFF
- [ ] Snap ON/OFF
- [ ] Footer quick-align
- [ ] Footer X/Width
- [ ] Right Rule X full range
- [ ] Bounds warning
- [ ] Coffee toast

## 7. PDF visual

- [ ] clipped text 없음
- [ ] Header/body collision 없음
- [ ] footer outside page 없음
- [ ] 1P/2P top margin 타당
- [ ] Logo 정상
- [ ] typography fallback 수용 가능

## 8. Icon/build

- [ ] PNG 존재
- [ ] ICNS 존재
- [ ] spec icon 지정
- [ ] app build에서 아이콘 보임
- [ ] executable architecture 확인
- [ ] ad-hoc codesign 확인
- [ ] ZIP 생성
- [ ] DMG 생성

## 9. Safe export

- [ ] real Body source overwrite 409/차단
- [ ] existing numbered output 다음 번호 제안
- [ ] Dummy output도 numbered filename

## 10. Documentation

각 수정된 Markdown:

```yaml
updated: YYYY-MM-DD
version: "문서버전"
```

body의 `문서 수정 이력`에도 같은 변경을 남긴다.

- [ ] Hub current baseline
- [ ] Architecture
- [ ] CHANGELOG
- [ ] Build Guide
- [ ] Troubleshooting
- [ ] Release Checklist
- [ ] Codex template
- [ ] Friend Guide
- [ ] Codex troubleshooting

## 11. Release archive

```text
source App Builder ZIP
macOS DMG
macOS ZIP
Developer Docs ZIP
verification report
representative Body/Dummy PDFs
```

## 12. Release Record

```markdown
## Release Record — vX.Y.Z
- Date:
- Base:
- Reason:
- Changed files:
- Schema:
- Compatibility:
- Automated tests:
- Visual PDF check:
- macOS build machine:
- uname -m:
- Artifacts:
- Docs version:
- Known limitations:
```

## 문서 수정 이력

| 문서 버전 | 날짜 | 기준 앱 | 내용 |
|---|---|---|---|
| 1.0 | 2026-08-19 | v0.9.2 | 최초 release governance |
| 1.1 | 2026-08-19 | v0.10.0 | smoke-test, Dummy, Smart Guides, icon, schema 체크 강화 |

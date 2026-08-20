#!/usr/bin/env python3
"""Optional browser-level interaction smoke test.

Uses Playwright + a locally available Chromium. It mocks the API layer so it can
exercise the Designer DOM without file dialogs or a running server.

Run:
    python3 tests/ui_runtime_smoke_test.py
    python3 tests/ui_runtime_smoke_test.py --require   # fail instead of skip
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def skip_or_fail(message: str, require: bool):
    if require:
        raise RuntimeError(message)
    print(f"[SKIP] {message}")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--require", action="store_true")
    args = ap.parse_args()

    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        return skip_or_fail("Playwright is not installed; UI runtime test skipped.", args.require)

    chromium = (
        shutil.which("chromium")
        or shutil.which("chromium-browser")
        or shutil.which("google-chrome")
        or shutil.which("google-chrome-stable")
    )
    if not chromium:
        return skip_or_fail("No local Chromium/Chrome executable; UI runtime test skipped.", args.require)

    html = (ROOT / "sozak_pdf_designer.html").read_text(encoding="utf-8")
    preset = json.loads((ROOT / "presets" / "howon-handout.json").read_text(encoding="utf-8"))
    preset["header"]["logo"]["path"] = ""  # avoid external image fetch in mocked DOM
    default = {
        "ok": True,
        "preset": preset,
        "long_logo": "",
        "circle_logo": "",
        "builtin_logos": {},
        "builtin_logo_folder": "",
        "default_css": "",
    }
    stub = '''async function api(path,payload={}){\n  if(path==="/api/default") return __TEST_DEFAULT__;\n  if(path==="/api/pdf-info") return {ok:true,pages:2,sizes:[]};\n  if(path==="/api/pick-output") return {ok:true,cancelled:true};\n  return {ok:true};\n}\n'''.replace("__TEST_DEFAULT__", json.dumps(default, ensure_ascii=False))
    pattern = r'async function api\(path,payload=\{\}\)\{.*?\n\}\n(?=function imageUrl)'
    html, count = re.subn(pattern, lambda _: stub, html, flags=re.S)
    if count != 1:
        raise AssertionError(f"Could not replace API function for UI test: count={count}")
    html = html.replace(
        'function imageUrl(path){return "/api/image?path="+encodeURIComponent(path||"");}',
        'function imageUrl(path){return "";}',
    )

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, executable_path=chromium, args=["--no-sandbox"])
        page = browser.new_page(viewport={"width": 1500, "height": 1000})
        errors = []
        page.on("pageerror", lambda exc: errors.append(str(exc)))
        page.set_content(html, wait_until="load")
        page.wait_for_timeout(250)

        assert "v0.10.0" in page.title()
        assert page.locator("#pvBody").is_visible()
        assert "Sample Lecture Handout" in page.locator("#pvBody").inner_text()
        assert page.locator("#pvSeries").is_visible()
        assert "CLASS HANDOUT WEEKLY SERIES" in page.locator("#pvSeries").inner_text()

        page.locator("#previewPage2").click()
        page.wait_for_timeout(40)
        assert "Continued" in page.locator("#pvBody").inner_text()
        assert not page.locator("#pvSeries").is_visible()
        page.locator("#previewPage1").click()
        page.wait_for_timeout(40)

        toggle = page.locator('[data-vis-key="series"]')
        toggle.click(); page.wait_for_timeout(20)
        assert not page.locator("#pvSeries").is_visible()
        toggle.click(); page.wait_for_timeout(20)
        assert page.locator("#pvSeries").is_visible()

        page.locator("#coffeeBtn").click()
        page.wait_for_timeout(20)
        assert page.locator("#toast").is_visible()
        assert "만나서 사주세요" in page.locator("#toast").inner_text()

        page.locator("#editor-footer1").evaluate("(el)=>el.open=true")
        fx = page.locator('[data-style="footer1:x"]')
        fw = page.locator('[data-style="footer1:width"]')
        fx.evaluate('(el)=>{el.value="70";el.dispatchEvent(new Event("input",{bubbles:true}));}')
        page.locator('[data-footer-align="footer1:left"]').click()
        page.wait_for_timeout(20)
        assert abs(float(fx.input_value()) - 20) < 0.01
        fw.evaluate('(el)=>{el.value="80";el.dispatchEvent(new Event("input",{bubbles:true}));}')
        page.locator('[data-footer-align="footer1:right"]').click()
        page.wait_for_timeout(20)
        assert abs(float(fx.input_value()) - 110) < 0.01
        assert abs(float(fx.get_attribute("max")) - 130) < 0.01

        sx = page.locator('[data-style="series:x"]')
        sx.evaluate('(el)=>{el.value="21";el.dispatchEvent(new Event("input",{bubbles:true}));}')
        page.wait_for_timeout(15)
        guide_ids = ["#smartV1", "#smartV2", "#smartV3", "#smartVMatch", "#smartH1", "#smartHMatch"]
        assert any(page.locator(sel).is_visible() for sel in guide_ids)
        page.locator("#enableSnap").uncheck()
        assert page.locator("#showSmartGuides").is_checked()
        assert not page.locator("#enableSnap").is_checked()

        rr = page.locator('[data-path="header.right_rule.x"]')
        assert rr.get_attribute("min") == "0" and rr.get_attribute("max") == "210"
        first_top = page.locator('[data-path="page.first_top"]')
        assert first_top.get_attribute("max") == "180" and float(first_top.input_value()) == 112
        assert "더미 테스트 PDF" in page.locator("#generate").inner_text()

        reset = page.locator('[data-reset-key="series"]')
        sx.evaluate('(el)=>{el.value="55";el.dispatchEvent(new Event("input",{bubbles:true}));}')
        reset.evaluate("(el)=>el.click()")
        page.wait_for_timeout(20)
        assert abs(float(sx.input_value()) - 18) < 0.01
        assert not errors, errors
        browser.close()

    checks = [
        "dummy page 1/2",
        "Vertical Series + visibility toggle",
        "coffee toast",
        "Footer quick align / X / Width limits",
        "Smart Guides + independent Snap",
        "Right Rule / first-top ranges",
        "Position Reset",
        "dummy export label",
        "no browser page errors",
    ]
    for check in checks:
        print(f"[PASS] UI runtime: {check}")
    print("\nAll UI runtime smoke tests passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

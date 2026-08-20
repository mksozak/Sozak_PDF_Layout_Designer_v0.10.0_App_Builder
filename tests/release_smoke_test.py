#!/usr/bin/env python3
from __future__ import annotations

import copy
import importlib.util
import json
import re
import sys
import tempfile
from pathlib import Path

import pymupdf as fitz

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sozak_pdf_overlay import stamp_dummy_pdf, stamp_pdf, apply_selected_layout, PT_PER_MM
import sozak_pdf_designer as designer


def ok(name: str):
    print(f"[PASS] {name}")


def require(cond, name: str, detail: str = ""):
    if not cond:
        raise AssertionError(f"{name}: {detail}")
    ok(name)


def word_x(page, needle: str):
    for w in page.get_text("words"):
        if w[4] == needle:
            return float(w[0])
    return None


def main():
    preset_path = ROOT / "presets" / "howon-handout.json"
    preset = json.loads(preset_path.read_text(encoding="utf-8"))
    html = (ROOT / "sozak_pdf_designer.html").read_text(encoding="utf-8")
    server = (ROOT / "sozak_pdf_designer.py").read_text(encoding="utf-8")
    spec = (ROOT / "SozakPDFLayoutDesigner.spec").read_text(encoding="utf-8")

    require(preset.get("version") == "0.10.0", "preset version")
    require(preset["header"].get("layout") == "vertical", "Vertical default")
    require(preset["header"]["layouts"]["vertical"]["series"].get("enabled") is True,
            "Vertical Series visible by default")
    require(preset["header"]["layouts"]["vertical"]["info"].get("line_enabled") == [True, True, True],
            "layout line visibility schema")
    vis = copy.deepcopy(preset)
    vis["header"]["layouts"]["horizontal"]["info"]["line_enabled"][0] = False
    vis["header"]["layouts"]["horizontal"]["series"]["enabled"] = False
    vis["header"]["layouts"]["vertical"]["info"]["line_enabled"][0] = True
    vis["header"]["layouts"]["vertical"]["series"]["enabled"] = True
    vis["header"]["layout"] = "horizontal"
    h = apply_selected_layout(copy.deepcopy(vis))
    vis["header"]["layout"] = "vertical"
    v = apply_selected_layout(copy.deepcopy(vis))
    require(h["header"]["info"]["lines"][0]["enabled"] is False and h["header"]["series"]["enabled"] is False
            and v["header"]["info"]["lines"][0]["enabled"] is True and v["header"]["series"]["enabled"] is True,
            "Horizontal/Vertical visibility independence")

    ft = preset["footer"]["text"]
    require(all(k in ft for k in ("line1_x", "line2_x", "line1_width", "line2_width", "line1_enabled", "line2_enabled")),
            "independent footer geometry schema")

    static_features = {
        "Smart Guides": "showSmartGuides" in html and "enableSnap" in html,
        "element visibility toggles": "data-vis-key" in html and "setElementEnabled" in html,
        "footer quick align": "data-footer-align" in html and "alignFooter" in html,
        "Right Rule full X": 'data-path="header.right_rule.x" type="range" min="0" max="210"' in html,
        "Vertical first-top slider range": 'data-path="page.first_top" type="range" min="30" max="180"' in html,
        "dummy preview": "Dummy Document" in html and "dummyPages" in html,
        "coffee joke": "개발자에게 커피 사기" in html and "만나서 사주세요. ☕" in html,
        "bounds warning": "updateBoundsWarning" in html,
        "position reset": "resetElementPosition" in html,
        "week/version": "week_version" in html and "week_version" in server,
        "app icon": (ROOT / "assets" / "app_icon_1024.png").exists() and (ROOT / "assets" / "SozakPDFLayoutDesigner.icns").exists(),
        "spec icon": "SozakPDFLayoutDesigner.icns" in spec,
    }
    for name, cond in static_features.items():
        require(cond, name)

    # YAML compatibility: week_version is canonical; legacy week and slash spelling are accepted.
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        cases = [
            ("week_version", "VERSION 1.2", "VERSION 1.2"),
            ("week", "08", "08"),
            ("week/version", "WEEK 09", "WEEK 09"),
        ]
        for key, raw, expected in cases:
            md = td / f"meta-{key.replace('/', '-')}.md"
            md.write_text(f'---\ndocumentation_name: "TEST DOC"\n{key}: "{raw}"\n---\n', encoding="utf-8")
            meta = designer.extract_yaml_mapping(str(md))
            require(meta["week_version"] == expected and "week_version" in meta["_present"],
                    f"metadata alias {key}")
        # Omitted instructors must remain omitted, not be silently marked present.
        md = td / "no-instructors.md"
        md.write_text('---\ndocumentation_name: "TEST"\n---\n', encoding="utf-8")
        meta = designer.extract_yaml_mapping(str(md))
        require("instructors" not in meta["_present"], "metadata omitted-field preservation")

    with tempfile.TemporaryDirectory() as td:
        td = Path(td)

        # Dummy output should be a 2-page, reviewable PDF with first-page header and footer on both pages.
        dummy = td / "dummy.pdf"
        stamp_dummy_pdf(copy.deepcopy(preset), dummy, preset_root=ROOT)
        doc = fitz.open(dummy)
        require(len(doc) == 2, "dummy PDF has two pages")
        t1, t2 = doc[0].get_text(), doc[1].get_text()
        require("Sample Lecture Handout" in t1 and "Sample Lecture Handout" in t2,
                "dummy body content on both pages")
        require("?" not in t1 and "?" not in t2,
                "dummy body has no missing-glyph replacement")
        require("CLASS HANDOUT WEEKLY SERIES" in t1, "Vertical Series actual PDF output")
        require("CLASS HANDOUT WEEKLY SERIES" not in t2, "first-page header only")
        require("Neurological Physical Therapy 2026" in t1 and "Neurological Physical Therapy 2026" in t2,
                "footer repeats on all pages")
        doc.close()

        # Visibility toggles must affect actual PDF output.
        hidden_cfg = copy.deepcopy(preset)
        hidden_cfg["header"]["info"]["lines"][0]["text"] = "HEADER-ONE-UNIQUE"
        hidden_cfg["header"]["info"]["lines"][0]["enabled"] = False
        hidden_cfg["header"]["layouts"]["vertical"]["info"]["line_enabled"][0] = False
        hidden_cfg["header"]["series"]["enabled"] = False
        hidden_cfg["header"]["layouts"]["vertical"]["series"]["enabled"] = False
        hidden_cfg["footer"]["text"]["line1_enabled"] = False
        hidden = td / "hidden.pdf"
        stamp_dummy_pdf(hidden_cfg, hidden, preset_root=ROOT)
        d = fitz.open(hidden)
        txt = d[0].get_text()
        require("HEADER-ONE-UNIQUE" not in txt,
                "header text visibility affects PDF")
        require("CLASS HANDOUT WEEKLY SERIES" not in txt, "Series visibility affects PDF")
        require("Neurological Physical Therapy 2026" not in txt, "footer visibility affects PDF")
        d.close()

        # Footer X must move independently in actual PDF.
        cfg_a = copy.deepcopy(preset)
        cfg_b = copy.deepcopy(preset)
        cfg_a["footer"]["text"]["line1_x"] = 20
        cfg_a["footer"]["text"]["line1_width"] = 80
        cfg_b["footer"]["text"]["line1_x"] = 70
        cfg_b["footer"]["text"]["line1_width"] = 80
        a, b = td / "footer-a.pdf", td / "footer-b.pdf"
        stamp_dummy_pdf(cfg_a, a, preset_root=ROOT)
        stamp_dummy_pdf(cfg_b, b, preset_root=ROOT)
        da, db = fitz.open(a), fitz.open(b)
        xa = word_x(da[0], "Neurological")
        xb = word_x(db[0], "Neurological")
        require(xa is not None and xb is not None and abs((xb-xa) - 50*PT_PER_MM) < 2.5,
                "footer X actual PDF movement", f"xa={xa}, xb={xb}")
        da.close(); db.close()

        # Existing independent header X/width behavior must remain intact.
        hx = copy.deepcopy(preset)
        hx["header"]["info"]["lines"][1]["x"] = 50
        hx["header"]["layouts"]["vertical"]["info"]["line_x"][1] = 50
        out = td / "header-x.pdf"
        stamp_dummy_pdf(hx, out, preset_root=ROOT)
        d = fitz.open(out)
        title_x = word_x(d[0], "NEUROLOGICAL")
        require(title_x is not None and title_x > 135, "header independent X regression")
        d.close()

        # Right Rule must support near-left and near-right positions in actual PDF geometry.
        rr = copy.deepcopy(preset)
        rr["header"]["right_rule"]["enabled"] = True
        rr["header"]["layouts"]["vertical"]["right_rule"].update({"enabled": True, "x": 5, "y1": 12, "y2": 120})
        out_l = td / "rule-left.pdf"
        stamp_dummy_pdf(rr, out_l, preset_root=ROOT)
        rr["header"]["layouts"]["vertical"]["right_rule"]["x"] = 205
        out_r = td / "rule-right.pdf"
        stamp_dummy_pdf(rr, out_r, preset_root=ROOT)
        dl, dr = fitz.open(out_l), fitz.open(out_r)
        def vertical_rule_x(page):
            xs=[]
            for drawing in page.get_drawings():
                for item in drawing.get("items", []):
                    if item and item[0] == "l":
                        p1,p2=item[1],item[2]
                        if abs(p1.x-p2.x)<0.5 and abs(p2.y-p1.y)>200:
                            xs.append(p1.x)
            return xs
        xl, xr = vertical_rule_x(dl[0]), vertical_rule_x(dr[0])
        require(any(abs(x-5*PT_PER_MM)<2 for x in xl) and any(abs(x-205*PT_PER_MM)<2 for x in xr),
                "Right Rule full-page X actual PDF", f"left={xl}, right={xr}")
        dl.close(); dr.close()

        # Existing Body PDF workflow still works.
        body = ROOT / "demo-body.pdf"
        stamped = td / "body-stamped.pdf"
        stamp_pdf(body, copy.deepcopy(preset), stamped, preset_root=ROOT)
        bd = fitz.open(stamped)
        require(len(bd) == len(fitz.open(body)), "existing Body PDF workflow")
        bd.close()

    # Safe output numbering remains available.
    with tempfile.TemporaryDirectory() as td:
        td=Path(td)
        source=td/"Lecture.pdf";source.write_bytes(b"x")
        (td/"Lecture (1).pdf").write_bytes(b"x")
        (td/"Lecture (2).pdf").write_bytes(b"x")
        require(designer.next_output_candidate(source).name == "Lecture (3).pdf", "safe numbered output suggestion")
        (td/"Sozak PDF Layout Test (1).pdf").write_bytes(b"x")
        (td/"Sozak PDF Layout Test (2).pdf").write_bytes(b"x")
        require(designer.next_dummy_output_candidate(td).name == "Sozak PDF Layout Test (3).pdf",
                "dummy numbered output suggestion")

    print("\nAll release smoke tests passed.")


if __name__ == "__main__":
    main()

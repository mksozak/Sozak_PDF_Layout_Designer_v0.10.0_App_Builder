#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import json
import os
import sys
from pathlib import Path
import pymupdf as fitz  # PyMuPDF

PT_PER_MM = 72.0 / 25.4

def resource_root():
    env = os.environ.get("SOZAK_RESOURCE_ROOT")
    if env:
        return Path(env).expanduser().resolve()
    frozen_root = getattr(sys, "_MEIPASS", None)
    if frozen_root:
        return Path(frozen_root).resolve()
    return Path(__file__).resolve().parent


def mm(v):
    return float(v) * PT_PER_MM

def rgb(value, fallback=(0.25,0.25,0.25)):
    if isinstance(value, str):
        s = value.strip().lstrip("#")
        if len(s) == 6:
            return tuple(int(s[i:i+2], 16) / 255 for i in (0,2,4))
    return fallback

def resolve_path(preset_root: Path, value):
    if not value:
        return None
    raw = str(value)
    if raw.startswith("@designer/"):
        return (resource_root() / raw[len("@designer/"):]).resolve()
    p = Path(raw).expanduser()
    if not p.is_absolute():
        p = (preset_root / p).resolve()
    return p

class FontBook:
    # Named fonts are resolved from fonts installed on the user's Mac.
    # No font files are bundled with the Designer.
    SYSTEM_FONT_SPECS = {
        "helvetica-neue": ["helveticaneue", "helvetica neue"],
        "avenir-next": ["avenirnext", "avenir next"],
        "apple-sd-gothic-neo": ["applesdgothicneo", "apple sd gothic neo"],
        "applegothic": ["applegothic"],
        "pretendard": ["pretendard"],
        "paperlogy": ["paperlogy"],
        "noto-sans-kr": ["notosanskr", "noto sans kr", "notosanscjkkr"],
        "noto-serif-kr": ["notoserifkr", "noto serif kr", "notoserifcjkk"],
        "roboto": ["roboto"],
        "open-sans": ["opensans", "open sans"],
        "montserrat": ["montserrat"],
        "source-sans-3": ["sourcesans3", "source sans 3", "sourcesanspro"],
        "lato": ["lato"],
    }

    def __init__(self, preset_root: Path, cfg: dict):
        fonts = cfg.get("fonts", {})
        self.reg = resolve_path(preset_root, fonts.get("regular", ""))
        self.bold = resolve_path(preset_root, fonts.get("bold", ""))
        self._installed_files = None
        self._resolved = {}

    def name(self, bold=False):
        path = self.bold if bold else self.reg
        if path and path.exists():
            return "sozak_bold" if bold else "sozak_regular"
        return "hebo" if bold else "helv"

    def file(self, bold=False):
        path = self.bold if bold else self.reg
        return str(path) if path and path.exists() else None

    def _scan_installed_fonts(self):
        if self._installed_files is not None:
            return self._installed_files

        roots = [
            Path.home() / "Library" / "Fonts",
            Path("/Library/Fonts"),
            Path("/System/Library/Fonts"),
            Path("/System/Library/Fonts/Supplemental"),
        ]
        files = []
        seen = set()
        for root in roots:
            if not root.exists():
                continue
            try:
                for path in root.rglob("*"):
                    if path.suffix.lower() not in {".ttf", ".otf", ".ttc"}:
                        continue
                    sp = str(path)
                    if sp not in seen:
                        seen.add(sp)
                        files.append(path)
            except Exception:
                continue
        self._installed_files = files
        return files

    @staticmethod
    def _norm(value):
        return "".join(ch.lower() for ch in str(value) if ch.isalnum())

    def _validate_fontfile(self, path):
        try:
            fitz.Font(fontfile=str(path))
            return True
        except Exception:
            return False

    def _find_system_font(self, family, bold=False):
        key = (family, bool(bold))
        if key in self._resolved:
            return self._resolved[key]

        tokens = self.SYSTEM_FONT_SPECS.get(family, [])
        if not tokens:
            self._resolved[key] = None
            return None

        norm_tokens = [self._norm(t) for t in tokens]
        candidates = []
        for path in self._scan_installed_fonts():
            stem = self._norm(path.stem)
            if any(tok in stem for tok in norm_tokens):
                is_bold = any(mark in stem for mark in ("bold", "semibold", "demibold", "heavy", "black", "extrabold"))
                is_light = any(mark in stem for mark in ("thin", "extralight", "ultralight", "light"))
                score = 0
                if bold and is_bold:
                    score += 20
                if bold and not is_bold:
                    score -= 4
                if not bold and not is_bold:
                    score += 12
                if not bold and is_bold:
                    score -= 8
                if not bold and is_light:
                    score -= 2
                if path.suffix.lower() in {".ttf", ".otf"}:
                    score += 3
                candidates.append((score, path))

        for _, path in sorted(candidates, key=lambda item: item[0], reverse=True):
            if self._validate_fontfile(path):
                self._resolved[key] = path
                return path

        self._resolved[key] = None
        return None

    def style(self, family="helvetica", bold=False):
        family = str(family or "helvetica").lower()

        # User-selected font files.
        if family == "preset":
            return self.name(bold), self.file(bold)

        # PDF built-in fonts are always safe.
        table = {
            ("helvetica", False): "helv",
            ("helvetica", True): "hebo",
            ("times", False): "tiro",
            ("times", True): "tibo",
            ("courier", False): "cour",
            ("courier", True): "cobo",
        }
        if (family, bool(bold)) in table:
            return table[(family, bool(bold))], None

        # Named installed fonts. If unavailable, fall back safely.
        path = self._find_system_font(family, bold)
        if path:
            safe_name = "sozak_" + family.replace("-", "_") + ("_bold" if bold else "_regular")
            return safe_name, str(path)

        return ("hebo" if bold else "helv"), None

def insert_text(page, x, y, text, fontsize, fontname, color, width=None,
                align="left", fontfile=None, lineheight=1.18):
    if text is None or str(text) == "":
        return
    if width is None:
        page.insert_text(
            fitz.Point(mm(x), mm(y)), str(text),
            fontsize=float(fontsize), fontname=fontname,
            fontfile=fontfile, color=color, overlay=True
        )
        return

    rect = fitz.Rect(mm(x), mm(y), mm(x + width), mm(y + 35))
    amap = {"left": 0, "center": 1, "right": 2}
    page.insert_textbox(
        rect, str(text),
        fontsize=float(fontsize), fontname=fontname,
        fontfile=fontfile, color=color,
        align=amap.get(align, 0),
        lineheight=float(lineheight), overlay=True
    )


def apply_selected_layout(cfg):
    """Apply the selected header layout's geometry to the active render fields."""
    header = cfg.get("header", {})
    layouts = header.get("layouts", {})
    layout_name = header.get("layout", "horizontal")
    layout = layouts.get(layout_name)
    if not isinstance(layout, dict):
        return cfg

    page_cfg = cfg.setdefault("page", {})
    if "first_top" in layout:
        page_cfg["first_top"] = layout["first_top"]

    logo = header.setdefault("logo", {})
    for key in ("enabled", "x", "y", "width"):
        if key in layout.get("logo", {}):
            logo[key] = layout["logo"][key]

    info = header.setdefault("info", {})
    linfo = layout.get("info", {})
    for key in ("auto_after_logo", "gap", "x", "width"):
        if key in linfo:
            info[key] = linfo[key]

    lines = info.get("lines", [])
    line_y = linfo.get("line_y", [])
    line_x = linfo.get("line_x", [])
    line_width = linfo.get("line_width", [])
    line_enabled = linfo.get("line_enabled", [])
    for i in range(min(3, len(lines))):
        if i < len(line_y):
            lines[i]["y"] = line_y[i]
        lines[i]["x"] = line_x[i] if i < len(line_x) else linfo.get("x", info.get("x", 72))
        lines[i]["width"] = line_width[i] if i < len(line_width) else linfo.get("width", info.get("width", 115))
        if i < len(line_enabled):
            lines[i]["enabled"] = bool(line_enabled[i])
        elif "enabled" not in lines[i]:
            lines[i]["enabled"] = True
    if len(lines) >= 3 and "instructor_gap" in linfo:
        lines[2]["line_gap"] = linfo["instructor_gap"]

    divider = header.setdefault("divider", {})
    for key in ("enabled", "x1", "x2", "y"):
        if key in layout.get("divider", {}):
            divider[key] = layout["divider"][key]

    series = header.setdefault("series", {})
    for key in ("enabled", "x", "y", "width"):
        if key in layout.get("series", {}):
            series[key] = layout["series"][key]

    rr = header.setdefault("right_rule", {})
    for key in ("enabled", "x", "y1", "y2"):
        if key in layout.get("right_rule", {}):
            rr[key] = layout["right_rule"][key]

    return cfg


def draw_line(page, x1, y1, x2, y2, width=0.25, color=(.75,.75,.75)):
    page.draw_line(
        fitz.Point(mm(x1), mm(y1)),
        fitz.Point(mm(x2), mm(y2)),
        width=float(width), color=color, overlay=True
    )

def draw_header(page, cfg, fonts, page_index, preset_root):
    header = cfg.get("header", {})
    if not header.get("enabled", True) or page_index != 0:
        return

    logo = header.get("logo", {})
    logo_right = None
    if logo.get("enabled", True) and logo.get("path"):
        p = resolve_path(preset_root, logo.get("path"))
        if p and p.exists():
            x = float(logo.get("x", 18))
            y = float(logo.get("y", 14))
            w = float(logo.get("width", 40))
            pix = fitz.Pixmap(str(p))
            h = w * (pix.height / max(1, pix.width))
            page.insert_image(
                fitz.Rect(mm(x), mm(y), mm(x+w), mm(y+h)),
                filename=str(p), keep_proportion=True, overlay=True
            )
            logo_right = x + w

    info = header.get("info", {})
    info_x = float(info.get("x", 72))
    ix = info_x
    if info.get("auto_after_logo", True) and logo_right is not None:
        ix = logo_right + float(info.get("gap", 14))
    iw = float(info.get("width", 115))

    regular = fonts.name(False)
    bold = fonts.name(True)
    regular_file = fonts.file(False)
    bold_file = fonts.file(True)

    defaults = [
        {"text": "DEPT. PHYSICAL THERAPY | HOWON UNIVERSITY", "y": 15, "size": 7.8, "bold": True, "color": "#777777"},
        {"text": "NEUROLOGICAL PHYSICAL THERAPY", "y": 22, "size": 14.8, "bold": True, "color": "#2c2c2c"},
        {"text": "", "y": 34, "size": 8.4, "bold": False, "color": "#666666"},
    ]
    lines = info.get("lines", [])
    for i in range(3):
        line = lines[i] if i < len(lines) else defaults[i]
        if not line.get("enabled", True):
            continue
        is_bold = bool(line.get("bold", defaults[i]["bold"]))
        line_font, line_fontfile = fonts.style(line.get("font", "helvetica"), is_bold)
        base_y = float(line.get("y", defaults[i]["y"]))
        line_text = str(line.get("text", defaults[i]["text"]))
        line_x = float(line.get("x", info_x))
        if info.get("auto_after_logo", True) and logo_right is not None:
            line_x = ix + (line_x - info_x)
        line_width = float(line.get("width", iw))

        # The third header block uses two independent instructor strings that
        # share one style/Y base. Old presets using a newline in "text" remain supported.
        if i == 2:
            instructors = line.get("instructors")
            if not isinstance(instructors, list):
                instructors = line_text.splitlines()
            instructors = list(instructors[:2])
            while len(instructors) < 2:
                instructors.append("")
            line_gap = float(line.get("line_gap", 4.4))
            for n, instructor_text in enumerate(instructors):
                if str(instructor_text).strip():
                    insert_text(
                        page, line_x, base_y + (line_gap * n),
                        str(instructor_text),
                        float(line.get("size", defaults[i]["size"])),
                        line_font,
                        rgb(line.get("color", defaults[i]["color"])),
                        width=line_width,
                        fontfile=line_fontfile
                    )
        else:
            insert_text(
                page, line_x, base_y,
                line_text,
                float(line.get("size", defaults[i]["size"])),
                line_font,
                rgb(line.get("color", defaults[i]["color"])),
                width=line_width,
                fontfile=line_fontfile
            )

    divider = header.get("divider", {})
    if divider.get("enabled", True):
        y = float(divider.get("y", 44))
        draw_line(
            page,
            float(divider.get("x1", 15)), y,
            float(divider.get("x2", 195)), y,
            width=float(divider.get("width", 0.35)),
            color=rgb(divider.get("color", "#d0d0d0"))
        )

    series = header.get("series", {})
    if series.get("enabled", True):
        series_bold = bool(series.get("bold", True))
        series_font, series_fontfile = fonts.style(series.get("font", "helvetica"), series_bold)
        insert_text(
            page,
            float(series.get("x", 20)),
            float(series.get("y", 52)),
            series.get("text", ""),
            float(series.get("size", 10.8)),
            series_font,
            rgb(series.get("color", "#595959")),
            width=float(series.get("width", 170)),
            fontfile=series_fontfile
        )

    rr = header.get("right_rule", {})
    if rr.get("enabled", True):
        x = float(rr.get("x", 195))
        draw_line(
            page, x, float(rr.get("y1", 9)),
            x, float(rr.get("y2", 122)),
            width=float(rr.get("width", 0.35)),
            color=rgb(rr.get("color", "#555555"))
        )

def draw_footer(page, cfg, fonts, page_index, total):
    footer = cfg.get("footer", {})
    if not footer.get("enabled", True):
        return

    page_w_mm = page.rect.width / PT_PER_MM
    regular = fonts.name(False)
    regular_file = fonts.file(False)

    line = footer.get("line", {})
    if line.get("enabled", True):
        length = float(line.get("length", 78))
        cx = float(line.get("center_x", page_w_mm / 2))
        y = float(line.get("y", 278))
        draw_line(
            page, cx-length/2, y, cx+length/2, y,
            width=float(line.get("width", 0.25)),
            color=rgb(line.get("color", "#d2d2d2"))
        )

    text = footer.get("text", {})
    legacy_x = float(text.get("x", 20))
    legacy_width = float(text.get("width", page_w_mm - 40))

    # Independent X / width / Y values. Old presets remain compatible.
    line1_x = float(text.get("line1_x", legacy_x))
    line2_x = float(text.get("line2_x", legacy_x))
    line1_width = float(text.get("line1_width", legacy_width))
    line2_width = float(text.get("line2_width", legacy_width))
    legacy_y = float(text.get("y", 282))
    legacy_gap = float(text.get("line_gap", 4.2))
    line1_y = float(text.get("line1_y", legacy_y))
    line2_y = float(text.get("line2_y", legacy_y + legacy_gap))

    line1 = str(text.get("line1", "")).format(page=page_index+1, pages=total)
    line2 = str(text.get("line2", "")).format(page=page_index+1, pages=total)

    line1_bold = bool(text.get("line1_bold", False))
    line1_font, line1_fontfile = fonts.style(text.get("line1_font", "helvetica"), line1_bold)
    line2_bold = bool(text.get("line2_bold", False))
    line2_font, line2_fontfile = fonts.style(text.get("line2_font", "helvetica"), line2_bold)

    if text.get("line1_enabled", True):
        insert_text(
            page, line1_x, line1_y, line1,
            float(text.get("line1_size", 6.8)),
            line1_font, rgb(text.get("line1_color", text.get("color", "#707070"))),
            width=line1_width, align="center", fontfile=line1_fontfile
        )
    if text.get("line2_enabled", True):
        insert_text(
            page, line2_x, line2_y, line2,
            float(text.get("line2_size", 6.5)),
            line2_font, rgb(text.get("line2_color", text.get("color", "#707070"))),
            width=line2_width, align="center", fontfile=line2_fontfile
        )

    pn = footer.get("page_number", {})
    if pn.get("enabled", False):
        value = str(pn.get("format", "{page} / {pages}")).format(
            page=page_index+1, pages=total
        )
        pn_bold = bool(pn.get("bold", False))
        pn_font, pn_fontfile = fonts.style(pn.get("font", "helvetica"), pn_bold)
        insert_text(
            page,
            float(pn.get("x", 175)),
            float(pn.get("y", 286)),
            value,
            float(pn.get("size", 6.5)),
            pn_font,
            rgb(pn.get("color", "#777777")),
            width=float(pn.get("width", 20)),
            align=pn.get("align", "right"),
            fontfile=pn_fontfile
        )

DUMMY_PAGE_1 = {
    "h1": "Sample Lecture Handout",
    "h2": "Coordination and Movement",
    "paragraphs": [
        "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Integer facilisis, nibh in tincidunt feugiat, neque magna consequat sem, at tristique justo sapien at erat.",
        "This two-page dummy document is generated when no Body PDF is selected. It helps verify header, footer, margins, alignment and page-number placement before the real document is ready.",
    ],
    "bullets": [
        "Observe the relationship between task, person and environment.",
        "Check how the layout behaves around headings and lists.",
        "Use the preview guides to align header and footer elements precisely.",
    ],
    "quote": "Design first, replace the dummy body later. The layout settings remain in the preset.",
}

DUMMY_PAGE_2 = {
    "h1": "Sample Lecture Handout - Continued",
    "h2": "Review and Application",
    "paragraphs": [
        "Sed posuere consectetur est at lobortis. Donec ullamcorper nulla non metus auctor fringilla. Vestibulum id ligula porta felis euismod semper.",
        "Page two begins at the Other Top margin and intentionally omits the first-page header. Footer elements continue on every page so their repeated placement can be inspected.",
    ],
    "bullets": [
        "Compare page-one and page-two top margins.",
        "Confirm footer text and page numbers remain inside the printable area.",
        "Export this dummy PDF when a Body PDF is not yet available.",
    ],
    "quote": "The dummy PDF is a review artifact, not a replacement for the final Body PDF.",
}


def _dummy_insert(page, x, y, width, text, size=9.4, bold=False, color=(0.28, 0.28, 0.28), lineheight=1.35):
    font = "hebo" if bold else "helv"
    rect = fitz.Rect(mm(x), mm(y), mm(x + width), mm(y + 55))
    page.insert_textbox(rect, str(text), fontsize=size, fontname=font, color=color, lineheight=lineheight, overlay=True)


def draw_dummy_body(page, cfg, page_index):
    """Draw a deterministic two-page body for preview/export when no Body PDF exists."""
    page_cfg = cfg.get("page", {})
    left = float(page_cfg.get("left", 20))
    right = float(page_cfg.get("right", 20))
    bottom = float(page_cfg.get("bottom", 24))
    top = float(page_cfg.get("first_top" if page_index == 0 else "other_top", 68 if page_index == 0 else 18))
    page_w_mm = page.rect.width / PT_PER_MM
    page_h_mm = page.rect.height / PT_PER_MM
    width = max(40.0, page_w_mm - left - right)
    max_y = page_h_mm - bottom
    data = DUMMY_PAGE_1 if page_index == 0 else DUMMY_PAGE_2

    y = top + 5
    _dummy_insert(page, left, y, width, data["h1"], size=18, bold=True, color=(0.18,0.18,0.18), lineheight=1.1)
    y += 12
    _dummy_insert(page, left, y, width, data["h2"], size=12.5, bold=True, color=(0.25,0.25,0.25), lineheight=1.15)
    y += 10
    for paragraph in data["paragraphs"]:
        _dummy_insert(page, left, y, width, paragraph, size=9.4, lineheight=1.42)
        y += 18
    # Divider
    page.draw_line(fitz.Point(mm(left), mm(y)), fitz.Point(mm(left+width), mm(y)), width=0.35, color=(0.82,0.82,0.82), overlay=True)
    y += 7
    _dummy_insert(page, left, y, width, "Key Points", size=11, bold=True)
    y += 8
    for bullet in data["bullets"]:
        _dummy_insert(page, left+3, y, width-3, f"-  {bullet}", size=9.2, lineheight=1.3)
        y += 9
    y += 3
    # Quote block
    page.draw_line(fitz.Point(mm(left), mm(y)), fitz.Point(mm(left), mm(y+20)), width=1.5, color=(0.72,0.30,0.25), overlay=True)
    _dummy_insert(page, left+5, y+1, width-5, data["quote"], size=9.1, color=(0.35,0.35,0.35), lineheight=1.35)
    y += 26
    # Simple numbered items and table-like rows; keep inside body bottom.
    if y + 50 < max_y:
        _dummy_insert(page, left, y, width, "Quick Review", size=11, bold=True)
        y += 8
        for n, txt in enumerate(("Check hierarchy and white space.", "Inspect alignment guides.", "Confirm final PDF output."), 1):
            _dummy_insert(page, left+2, y, width-2, f"{n}.  {txt}", size=9.1)
            y += 8
        y += 4
        table_w = min(width, 120)
        col1 = table_w * 0.33
        row_h = 8
        rows = [("Element", "Review"), ("Header", "Position / width / visibility"), ("Footer", "Margins / alignment / page no."), ("Body", "Page 1 and page 2 flow")]
        for r, (a, b) in enumerate(rows):
            yy = y + r*row_h
            page.draw_rect(fitz.Rect(mm(left), mm(yy), mm(left+table_w), mm(yy+row_h)), color=(0.78,0.78,0.78), width=0.35, overlay=True)
            page.draw_line(fitz.Point(mm(left+col1), mm(yy)), fitz.Point(mm(left+col1), mm(yy+row_h)), width=0.35, color=(0.78,0.78,0.78), overlay=True)
            _dummy_insert(page, left+2, yy+1.5, col1-3, a, size=7.8, bold=(r==0), lineheight=1.0)
            _dummy_insert(page, left+col1+2, yy+1.5, table_w-col1-3, b, size=7.8, bold=(r==0), lineheight=1.0)


def stamp_dummy_pdf(cfg, output, preset_root=None):
    """Create a two-page A4 dummy body and stamp the current layout onto it."""
    output = Path(output).expanduser()
    preset_root = Path(preset_root).expanduser() if preset_root else resource_root()
    cfg = apply_selected_layout(copy.deepcopy(cfg))
    output.parent.mkdir(parents=True, exist_ok=True)
    doc = fitz.open()
    try:
        a4 = fitz.paper_rect("a4")
        for i in range(2):
            page = doc.new_page(width=a4.width, height=a4.height)
            draw_dummy_body(page, cfg, i)
        fonts = FontBook(preset_root, cfg)
        total = len(doc)
        for i, page in enumerate(doc):
            draw_header(page, cfg, fonts, i, preset_root)
            draw_footer(page, cfg, fonts, i, total)
        doc.save(output, garbage=4, deflate=True)
    finally:
        doc.close()
    return output


def stamp_pdf(body_pdf, cfg, output, preset_root=None):
    body_pdf = Path(body_pdf).expanduser()
    output = Path(output).expanduser()
    preset_root = Path(preset_root).expanduser() if preset_root else resource_root()

    cfg = apply_selected_layout(copy.deepcopy(cfg))

    if not body_pdf.exists():
        raise FileNotFoundError(f"Body PDF not found: {body_pdf}")

    output.parent.mkdir(parents=True, exist_ok=True)

    doc = fitz.open(body_pdf)
    try:
        fonts = FontBook(preset_root, cfg)
        total = len(doc)
        for i, page in enumerate(doc):
            draw_header(page, cfg, fonts, i, preset_root)
            draw_footer(page, cfg, fonts, i, total)
        doc.save(output, garbage=4, deflate=True)
    finally:
        doc.close()

    return output


def main():
    ap = argparse.ArgumentParser(description="Stamp header/footer onto an existing body PDF.")
    ap.add_argument("body_pdf", type=Path)
    ap.add_argument("preset_json", type=Path)
    ap.add_argument("-o", "--output", type=Path, default=None)
    args = ap.parse_args()

    cfg = json.loads(args.preset_json.read_text(encoding="utf-8"))
    output = args.output or args.body_pdf.with_name(args.body_pdf.stem + "-final.pdf")
    result = stamp_pdf(args.body_pdf, cfg, output, preset_root=args.preset_json.parent)
    print(result)


if __name__ == "__main__":
    main()

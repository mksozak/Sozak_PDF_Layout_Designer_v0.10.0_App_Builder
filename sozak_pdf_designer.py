#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import mimetypes
import os
import re
import shutil
import subprocess
import sys
import multiprocessing
import threading
import webbrowser
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse, parse_qs

import pymupdf as fitz
import yaml

from sozak_pdf_overlay import stamp_pdf, stamp_dummy_pdf

def resource_root() -> Path:
    frozen_root = getattr(sys, "_MEIPASS", None)
    if frozen_root:
        return Path(frozen_root).resolve()
    return Path(__file__).resolve().parent

ROOT = resource_root()
HTML = ROOT / "sozak_pdf_designer.html"
DEFAULT_PRESET = ROOT / "presets" / "howon-handout.json"
DEFAULT_CSS = ROOT / "sozak-pdf-body.css"

OLD_APP_SUPPORT = Path.home() / "Library" / "Application Support" / "Sozak PDF Designer"
APP_SUPPORT = Path.home() / "Library" / "Application Support" / "Sozak PDF Layout Designer"

# One-time migration from the previous app name when possible.
if not APP_SUPPORT.exists() and OLD_APP_SUPPORT.exists():
    try:
        shutil.copytree(OLD_APP_SUPPORT, APP_SUPPORT, dirs_exist_ok=True)
    except Exception:
        pass

USER_PRESETS = APP_SUPPORT / "Presets"
USER_LOGOS = APP_SUPPORT / "Built-in Logos"
USER_CSS = APP_SUPPORT / "sozak-pdf-body.css"
USER_PRESETS.mkdir(parents=True, exist_ok=True)
USER_LOGOS.mkdir(parents=True, exist_ok=True)

BUILTIN_LOGO_FILES = [
    "uni_logo_long.png",
    "uni_logo_circle.png",
    "wku_land_2.png",
    "wku_land_1.png",
    "wku_circle.png",
    "tlf_logo.png",
    "tlf_logo_text.png",
]

for logo_name in BUILTIN_LOGO_FILES:
    source = ROOT / "assets" / logo_name
    target = USER_LOGOS / logo_name
    if source.exists() and not target.exists():
        try:
            shutil.copy2(source, target)
        except Exception:
            pass

if not USER_CSS.exists() and DEFAULT_CSS.exists():
    try:
        shutil.copy2(DEFAULT_CSS, USER_CSS)
    except Exception:
        pass


def run_osascript(script: str) -> str:
    r = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    if r.returncode != 0:
        return ""
    return r.stdout.strip()


def choose_file(prompt: str, default_dir: str | None = None) -> str:
    safe_prompt = prompt.replace('"', '\\"')
    if default_dir:
        safe_dir = str(default_dir).replace('"', '\\"')
        script = f"""
try
  set f to choose file with prompt "{safe_prompt}" default location POSIX file "{safe_dir}/"
  return POSIX path of f
on error
  return ""
end try
"""
    else:
        script = f"""
try
  set f to choose file with prompt "{safe_prompt}"
  return POSIX path of f
on error
  return ""
end try
"""
    return run_osascript(script)


def choose_save(prompt: str, default_name: str, default_dir: str) -> str:
    script = f'''
try
  set f to choose file name with prompt "{prompt}" default name "{default_name}" default location POSIX file "{default_dir}/"
  return POSIX path of f
on error
  return ""
end try
'''
    return run_osascript(script)


def next_output_candidate(body_pdf: Path) -> Path:
    """Suggest original-name (1).pdf, then the next unused number."""
    body_pdf = body_pdf.expanduser()
    parent = body_pdf.parent
    stem = body_pdf.stem
    n = 1
    while True:
        candidate = parent / f"{stem} ({n}).pdf"
        if not candidate.exists():
            return candidate
        n += 1


def next_dummy_output_candidate(parent: Path | None = None) -> Path:
    """Suggest a numbered dummy-layout review PDF when no Body PDF exists."""
    parent = (parent or (Path.home() / "Desktop")).expanduser()
    parent.mkdir(parents=True, exist_ok=True)
    stem = "Sozak PDF Layout Test"
    n = 1
    while True:
        candidate = parent / f"{stem} ({n}).pdf"
        if not candidate.exists():
            return candidate
        n += 1


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def resolve_image_path(value: str):
    if value.startswith("@designer/"):
        return (ROOT / value[len("@designer/"):]).resolve()
    return Path(value).expanduser()


def sync_css(css_path: Path, preset: dict):
    page = preset.get("page", {})
    values = {
        "--pdf-page-left": f"{page.get('left', 20)}mm",
        "--pdf-page-right": f"{page.get('right', 20)}mm",
        "--pdf-page-bottom": f"{page.get('bottom', 24)}mm",
        "--pdf-first-top": f"{page.get('first_top', 68)}mm",
        "--pdf-other-top": f"{page.get('other_top', 18)}mm",
    }

    if css_path.exists():
        text = css_path.read_text(encoding="utf-8")
    else:
        text = """@media print {
  @page {
    size: A4;
    margin-top: var(--pdf-other-top);
    margin-right: var(--pdf-page-right);
    margin-bottom: var(--pdf-page-bottom);
    margin-left: var(--pdf-page-left);
  }
  @page :first {
    margin-top: var(--pdf-first-top);
    margin-right: var(--pdf-page-right);
    margin-bottom: var(--pdf-page-bottom);
    margin-left: var(--pdf-page-left);
  }
}
"""

    root = re.search(r":root\s*\{(.*?)\}", text, flags=re.S)
    if root:
        body = root.group(1)
        for var, val in values.items():
            pat = rf"({re.escape(var)}\s*:\s*)[^;]+;"
            if re.search(pat, body):
                body = re.sub(pat, rf"\g<1>{val};", body)
            else:
                body += f"\n  {var}: {val};"
        text = text[:root.start(1)] + body + text[root.end(1):]
    else:
        block = ":root {\n" + "\n".join(f"  {k}: {v};" for k, v in values.items()) + "\n}\n\n"
        text = block + text

    css_path.write_text(text, encoding="utf-8")
    return css_path


def pdf_info(path_value: str):
    path = Path(path_value).expanduser()
    if not path.exists():
        raise FileNotFoundError(f"Body PDF를 찾을 수 없습니다: {path}")
    doc = fitz.open(path)
    try:
        sizes = []
        for page in doc:
            sizes.append({
                "width_pt": float(page.rect.width),
                "height_pt": float(page.rect.height),
            })
        return {"pages": len(doc), "sizes": sizes}
    finally:
        doc.close()


def render_pdf_preview(path_value: str, page_index: int, target_width: int = 1260):
    path = Path(path_value).expanduser()
    if not path.exists():
        raise FileNotFoundError(f"Body PDF를 찾을 수 없습니다: {path}")
    doc = fitz.open(path)
    try:
        if page_index < 0 or page_index >= len(doc):
            raise IndexError("요청한 PDF 페이지가 없습니다.")
        page = doc[page_index]
        zoom = max(0.5, float(target_width) / max(1.0, page.rect.width))
        matrix = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=matrix, alpha=False)
        return pix.tobytes("png")
    finally:
        doc.close()


def normalize_metadata_key(value: str) -> str:
    """Normalize YAML keys while accepting spaces, hyphens and camelCase."""
    key = str(value or "").strip()
    key = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", key)
    key = key.lower()
    key = re.sub(r"[\s\-/]+", "_", key)
    key = re.sub(r"_+", "_", key).strip("_")
    aliases = {
        "document_name": "documentation_name",
        "documentname": "documentation_name",
        "documentationname": "documentation_name",
        "documentation": "documentation_name",
        "doc_name": "documentation_name",
        "instructor": "instructors",
        "lecturer": "instructors",
        "lecturers": "instructors",
        "teacher": "instructors",
        "teachers": "instructors",
        "school": "institution",
        "university": "institution",
        "subject": "course",
        "course_name": "course",
        "week": "week_version",
        "weekversion": "week_version",
        "footer_1": "footer1",
        "footer_2": "footer2",
    }
    return aliases.get(key, key)


def _repair_known_yaml_lines(text: str) -> str:
    """Repair a common typo: known key followed by a quoted value without ':'."""
    out = []
    known = (
        r"documentation(?:[\s_-]+name)?|document(?:[\s_-]+name)|"
        r"institution|department|course|semester|week(?:[\s_/-]+version)?|date|footer1|footer2"
    )
    pat = re.compile(rf'^(\s*)({known})\s+((?:"[^"]*"|\'[^\']*\'|[^:#][^#]*))\s*$', re.I)
    for line in text.splitlines():
        if ":" not in line:
            m = pat.match(line)
            if m:
                line = f"{m.group(1)}{m.group(2)}: {m.group(3).strip()}"
        out.append(line)
    return "\n".join(out)


def extract_yaml_mapping(path_value: str):
    path = Path(path_value).expanduser()
    if not path.exists():
        raise FileNotFoundError(f"YAML/Markdown 파일을 찾을 수 없습니다: {path}")

    text = path.read_text(encoding="utf-8-sig", errors="replace")
    suffix = path.suffix.lower()

    if suffix in {".md", ".markdown", ".mdown"}:
        m = re.match(r"^\s*---\s*\n(.*?)\n---\s*(?:\n|$)", text, flags=re.S)
        if not m:
            raise ValueError("Markdown 파일 맨 위에서 YAML front matter(--- ... ---)를 찾지 못했습니다.")
        yaml_text = m.group(1)
    else:
        yaml_text = text

    yaml_text = _repair_known_yaml_lines(yaml_text)
    data = yaml.safe_load(yaml_text) or {}
    if not isinstance(data, dict):
        raise ValueError("YAML 최상위 구조가 key: value 형식이 아닙니다.")

    normalized = {}
    for raw_key, value in data.items():
        normalized[normalize_metadata_key(raw_key)] = value
    raw_present = set(normalized.keys())

    # Some users keep instructors under other plural forms or a single string.
    instructors = normalized.get("instructors", [])
    if instructors is None:
        instructors = []
    elif isinstance(instructors, str):
        instructors = [instructors]
    elif not isinstance(instructors, list):
        instructors = [str(instructors)]
    normalized["instructors"] = [str(x).strip() for x in instructors if str(x).strip()]

    canonical_keys = (
        "institution", "department", "course", "semester", "week_version", "date",
        "documentation_name", "instructors", "footer1", "footer2"
    )
    present_keys = [key for key in canonical_keys if key in raw_present]
    canonical = {
        "institution": normalized.get("institution", ""),
        "department": normalized.get("department", ""),
        "course": normalized.get("course", ""),
        "semester": normalized.get("semester", ""),
        "week_version": normalized.get("week_version", ""),
        "date": normalized.get("date", ""),
        "documentation_name": normalized.get("documentation_name", ""),
        "instructors": normalized.get("instructors", []),
        "footer1": normalized.get("footer1", ""),
        "footer2": normalized.get("footer2", ""),
        "_present": present_keys,
    }
    # Convert scalar values to strings while preserving blank/null as blank.
    for key in ("institution", "department", "course", "semester", "week_version",
                "date", "documentation_name", "footer1", "footer2"):
        value = canonical[key]
        canonical[key] = "" if value is None else str(value).strip()

    return canonical


def find_sibling_metadata_file(pdf_path_value: str):
    pdf = Path(pdf_path_value).expanduser()
    if not pdf.exists():
        return ""
    stem = pdf.with_suffix("")
    candidates = [
        stem.with_suffix(".md"),
        stem.with_suffix(".markdown"),
        stem.with_suffix(".yaml"),
        stem.with_suffix(".yml"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    return ""


class Handler(BaseHTTPRequestHandler):
    server_version = "SozakPDFLayoutDesigner/0.10.0"

    def log_message(self, fmt, *args):
        sys.stderr.write("[designer] " + fmt % args + "\n")

    def send_json(self, status, payload):
        raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(raw)

    def read_json(self):
        n = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(n).decode("utf-8") or "{}")

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/":
            raw = HTML.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)
            return

        if parsed.path == "/api/pdf-preview":
            q = parse_qs(parsed.query)
            raw_path = q.get("path", [""])[0]
            try:
                page_index = int(q.get("page", ["1"])[0]) - 1
                raw = render_pdf_preview(raw_path, page_index)
            except Exception as exc:
                self.send_error(404, str(exc))
                return
            self.send_response(200)
            self.send_header("Content-Type", "image/png")
            self.send_header("Content-Length", str(len(raw)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(raw)
            return

        if parsed.path == "/api/image":
            q = parse_qs(parsed.query)
            path = resolve_image_path(q.get("path", [""])[0])
            if not path.exists():
                self.send_error(404)
                return
            raw = path.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", mimetypes.guess_type(str(path))[0] or "image/png")
            self.send_header("Content-Length", str(len(raw)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(raw)
            return

        self.send_error(404)

    def do_POST(self):
        try:
            body = self.read_json()
            path = urlparse(self.path).path

            if path == "/api/default":
                self.send_json(200, {
                    "ok": True,
                    "preset": load_json(DEFAULT_PRESET),
                    "default_css": str(USER_CSS if USER_CSS.exists() else DEFAULT_CSS),
                    "long_logo": "@designer/assets/uni_logo_long.png",
                    "circle_logo": "@designer/assets/uni_logo_circle.png",
                    "builtin_logos": {
                        "howon_long": "@designer/assets/uni_logo_long.png",
                        "howon_circle": "@designer/assets/uni_logo_circle.png",
                        "wku_land_2": "@designer/assets/wku_land_2.png",
                        "wku_land_1": "@designer/assets/wku_land_1.png",
                        "wku_circle": "@designer/assets/wku_circle.png",
                        "tlf_logo": "@designer/assets/tlf_logo.png",
                        "tlf_logo_text": "@designer/assets/tlf_logo_text.png"
                    },
                    "builtin_logo_folder": str(USER_LOGOS),
                })
                return

            if path == "/api/pdf-info":
                raw_pdf = str(body.get("body_pdf", "")).strip()
                if not raw_pdf:
                    self.send_json(200, {"ok": True, "pages": 0, "sizes": []})
                    return
                try:
                    info = pdf_info(raw_pdf)
                except Exception as exc:
                    self.send_json(404, {"ok": False, "error": str(exc)})
                    return
                self.send_json(200, {"ok": True, **info})
                return

            if path == "/api/load-metadata":
                raw_path = str(body.get("path", "")).strip()
                if not raw_path:
                    self.send_json(400, {"ok": False, "error": "YAML/Markdown 파일 경로가 비어 있습니다."})
                    return
                try:
                    metadata = extract_yaml_mapping(raw_path)
                except Exception as exc:
                    self.send_json(400, {"ok": False, "error": str(exc)})
                    return
                self.send_json(200, {"ok": True, "metadata": metadata, "path": raw_path})
                return

            if path == "/api/find-sibling-metadata":
                raw_pdf = str(body.get("body_pdf", "")).strip()
                found = find_sibling_metadata_file(raw_pdf) if raw_pdf else ""
                if not found:
                    self.send_json(200, {"ok": True, "found": False, "path": ""})
                    return
                try:
                    metadata = extract_yaml_mapping(found)
                except Exception as exc:
                    self.send_json(200, {"ok": True, "found": False, "path": found, "warning": str(exc)})
                    return
                self.send_json(200, {"ok": True, "found": True, "path": found, "metadata": metadata})
                return

            if path == "/api/pick":
                kind = body.get("kind", "")
                prompts = {
                    "pdf": "본문 PDF를 선택하세요.",
                    "metadata": "YAML front matter가 있는 Markdown 또는 YAML 파일을 선택하세요.",
                    "logo": "로고 이미지를 선택하세요.",
                    "css": "Typora PDF 출력용 CSS를 선택하세요.",
                    "font-regular": "Preset에서 사용할 Regular 폰트 파일을 선택하세요.",
                    "font-bold": "Preset에서 사용할 Bold 폰트 파일을 선택하세요.",
                }
                if kind == "logo":
                    chosen = choose_file(prompts.get(kind, "파일을 선택하세요."), str(USER_LOGOS))
                else:
                    chosen = choose_file(prompts.get(kind, "파일을 선택하세요."))
                self.send_json(200, {"ok": True, "path": chosen})
                return

            if path == "/api/pick-output":
                raw_pdf = str(body.get("body_pdf", "")).strip()
                if raw_pdf:
                    bp = Path(raw_pdf).expanduser()
                    if not bp.exists():
                        self.send_json(404, {"ok": False, "error": f"Body PDF를 찾을 수 없습니다: {bp}"})
                        return
                    suggestion = next_output_candidate(bp)
                    prompt = "최종 PDF 저장 위치"
                    dummy = False
                else:
                    suggestion = next_dummy_output_candidate()
                    prompt = "더미 문서 포함 테스트 PDF 저장 위치"
                    dummy = True
                chosen = choose_save(prompt, suggestion.name, str(suggestion.parent))
                self.send_json(200, {
                    "ok": True,
                    "path": chosen,
                    "cancelled": not bool(chosen),
                    "suggested": str(suggestion),
                    "dummy": dummy
                })
                return

            if path == "/api/load-preset":
                chosen = choose_file("저장된 프리셋 JSON을 선택하세요.")
                if not chosen:
                    self.send_json(200, {"ok": True, "cancelled": True})
                    return
                p = Path(chosen).expanduser()
                preset = load_json(p)
                self.send_json(200, {"ok": True, "preset": preset, "path": str(p)})
                return

            if path == "/api/save-preset":
                preset = body.get("preset", {})
                name = str(preset.get("name", "sozak-pdf-preset")).strip() or "sozak-pdf-preset"
                safe = re.sub(r"[^A-Za-z0-9._-]+", "-", name).strip("-") or "sozak-pdf-preset"
                chosen = choose_save("프리셋 저장 위치", safe + ".json", str(USER_PRESETS))
                if not chosen:
                    self.send_json(200, {"ok": True, "cancelled": True})
                    return
                p = Path(chosen).expanduser()
                if p.suffix.lower() != ".json":
                    p = p.with_suffix(".json")
                save_json(p, preset)
                self.send_json(200, {"ok": True, "path": str(p)})
                return

            if path == "/api/save-css":
                preset = body.get("preset", {})
                raw_css = str(body.get("css_path", "")).strip()
                if raw_css:
                    css_path = Path(raw_css).expanduser()
                else:
                    chosen = choose_save("Typora 본문 여백 CSS 저장 위치", "sozak-pdf-body.css", str(Path.home() / "Desktop"))
                    if not chosen:
                        self.send_json(200, {"ok": True, "cancelled": True})
                        return
                    css_path = Path(chosen).expanduser()
                    if css_path.suffix.lower() != ".css":
                        css_path = css_path.with_suffix(".css")
                saved = sync_css(css_path, preset)
                self.send_json(200, {"ok": True, "path": str(saved)})
                return

            if path == "/api/generate":
                raw_pdf = str(body.get("body_pdf", "")).strip()
                pdf = Path(raw_pdf).expanduser() if raw_pdf else None
                if pdf is not None and not pdf.exists():
                    self.send_json(404, {
                        "ok": False,
                        "error": f"Body PDF를 찾을 수 없습니다: {pdf}"
                    })
                    return

                preset = body.get("preset", {})
                output_raw = str(body.get("output_pdf", "")).strip()
                if not output_raw:
                    self.send_json(400, {
                        "ok": False,
                        "error": "저장 위치가 지정되지 않았습니다. 내보내기를 다시 실행하세요."
                    })
                    return
                output = Path(output_raw).expanduser()
                if output.suffix.lower() != ".pdf":
                    output = output.with_suffix(".pdf")

                if pdf is not None:
                    try:
                        same_as_source = output.resolve() == pdf.resolve()
                    except Exception:
                        same_as_source = str(output.absolute()) == str(pdf.absolute())
                    if same_as_source:
                        self.send_json(409, {
                            "ok": False,
                            "error": "원본 Body PDF에는 덮어쓸 수 없습니다. 다른 이름이나 저장 위치를 선택하세요."
                        })
                        return

                try:
                    if pdf is None:
                        stamp_dummy_pdf(preset, output, preset_root=ROOT)
                    else:
                        stamp_pdf(pdf, preset, output, preset_root=ROOT)
                except Exception as exc:
                    self.send_json(500, {
                        "ok": False,
                        "error": f"최종 PDF 생성에 실패했습니다: {exc}"
                    })
                    return

                self.send_json(200, {"ok": True, "output": str(output), "dummy": pdf is None})
                return

            self.send_json(404, {"ok": False, "error": "Unknown endpoint"})
        except Exception as e:
            self.send_json(500, {"ok": False, "error": str(e)})


def main():
    multiprocessing.freeze_support()
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--no-browser", action="store_true")
    args = ap.parse_args()

    server = None
    selected_port = None
    last_error = None
    for port in range(args.port, args.port + 20):
        try:
            server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
            selected_port = port
            break
        except OSError as exc:
            last_error = exc

    if server is None:
        raise last_error or RuntimeError("사용 가능한 로컬 포트를 찾지 못했습니다.")

    url = f"http://127.0.0.1:{selected_port}/"
    print(f"Sozak PDF Layout Designer v0.10.0: {url}")
    if selected_port != args.port:
        print(f"[designer] {args.port} 포트가 사용 중이어서 {selected_port} 포트를 사용합니다.")

    if not args.no_browser:
        threading.Timer(0.5, lambda: webbrowser.open(url)).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
from __future__ import annotations

import json
import tempfile
import threading
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path
import sys

import pymupdf as fitz

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import sozak_pdf_designer as designer


def require(cond, name, detail=''):
    if not cond:
        raise AssertionError(f'{name}: {detail}')
    print(f'[PASS] {name}')


def main():
    server = ThreadingHTTPServer(('127.0.0.1', 0), designer.Handler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f'http://127.0.0.1:{port}'

    def post(path, data):
        req = urllib.request.Request(
            base + path,
            data=json.dumps(data).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='POST',
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as r:
                return r.status, json.loads(r.read().decode('utf-8'))
        except urllib.error.HTTPError as exc:
            return exc.code, json.loads(exc.read().decode('utf-8'))

    try:
        status, default = post('/api/default', {})
        require(status == 200 and default['preset']['version'] == '0.10.0', 'HTTP default preset v0.10.0')
        preset = default['preset']

        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            dummy = td / 'dummy-http.pdf'
            status, data = post('/api/generate', {
                'body_pdf': '', 'preset': preset, 'output_pdf': str(dummy)
            })
            require(status == 200 and data.get('dummy') is True and dummy.exists(), 'HTTP dummy generate')
            d = fitz.open(dummy)
            require(len(d) == 2 and 'Sample Lecture Handout' in d[0].get_text(), 'HTTP dummy PDF content')
            d.close()

            body = ROOT / 'demo-body.pdf'
            real = td / 'body-http.pdf'
            status, data = post('/api/generate', {
                'body_pdf': str(body), 'preset': preset, 'output_pdf': str(real)
            })
            require(status == 200 and data.get('dummy') is False and real.exists(), 'HTTP real Body generate')

            status, data = post('/api/generate', {
                'body_pdf': str(body), 'preset': preset, 'output_pdf': str(body)
            })
            require(status == 409 and '덮어쓸 수 없습니다' in data.get('error', ''), 'HTTP source overwrite blocked')

            meta_file = td / 'metadata.md'
            meta_file.write_text(
                '---\ndocumentation_name: "HTTP TEST"\nweek_version: "VERSION 2.0"\n---\n',
                encoding='utf-8',
            )
            status, data = post('/api/load-metadata', {'path': str(meta_file)})
            require(status == 200 and data['metadata']['week_version'] == 'VERSION 2.0', 'HTTP week_version metadata')

            status, data = post('/api/pdf-info', {'body_pdf': str(body)})
            require(status == 200 and data.get('pages') == 2, 'HTTP PDF info')
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)

    print('\nAll HTTP smoke tests passed.')


if __name__ == '__main__':
    main()

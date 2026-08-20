#!/bin/zsh
cd "$(dirname "$0")"

if [ -x "/opt/anaconda3/envs/pymupdf311/bin/python" ]; then
  PY="/opt/anaconda3/envs/pymupdf311/bin/python"
else
  PY="$(command -v python3)"
fi

if [ -z "$PY" ]; then
  echo "Python을 찾지 못했습니다."
  read
  exit 1
fi

"$PY" - <<'PY'
try:
    import pymupdf
except Exception as e:
    print("PyMuPDF가 설치된 Python 환경이 필요합니다:", e)
    raise SystemExit(1)
PY

if [ $? -ne 0 ]; then
  read
  exit 1
fi

"$PY" sozak_pdf_designer.py

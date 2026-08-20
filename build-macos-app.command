#!/bin/zsh
set -euo pipefail

cd "$(dirname "$0")"

APP_VERSION="0.10.0"
APP_NAME="Sozak PDF Layout Designer"

echo ""
echo "=========================================="
echo "  $APP_NAME v$APP_VERSION - macOS App Builder"
echo "=========================================="
echo ""
echo "이 작업은 이 Mac에서 실행되는 독립형 .app을 만듭니다."
echo "빌드 전에 release smoke test를 실행하고 앱 아이콘을 갱신합니다."
echo "완료되면 dist 폴더에 .app / versioned .zip / .dmg가 생성됩니다."
echo ""

PY=""
if [ -x "/opt/anaconda3/envs/pymupdf311/bin/python" ]; then
  PY="/opt/anaconda3/envs/pymupdf311/bin/python"
elif command -v python3 >/dev/null 2>&1; then
  PY="$(command -v python3)"
fi

if [ -z "$PY" ]; then
  echo "Python 3를 찾지 못했습니다."
  echo "이 빌더를 실행하는 Mac에 Python 3가 한 번은 필요합니다."
  echo "앱이 만들어진 뒤 친구의 Mac에는 Python이 필요하지 않습니다."
  echo ""
  read "?Enter를 누르면 종료합니다..."
  exit 1
fi

echo "[1/9] Build Python: $PY"

VENV=".build-venv"
if [ ! -x "$VENV/bin/python" ]; then
  echo "[2/9] 빌드 전용 가상환경 생성..."
  "$PY" -m venv "$VENV"
else
  echo "[2/9] 기존 빌드 환경 사용..."
fi
VPY="$VENV/bin/python"

echo "[3/9] PyInstaller / PyMuPDF 준비..."
"$VPY" -m pip install --upgrade pip wheel
"$VPY" -m pip install "pyinstaller>=6.10,<7" "pymupdf>=1.26,<2" "PyYAML>=6,<7"

echo "[4/9] 앱 아이콘 생성..."
ICON_SRC="assets/app_icon_1024.png"
ICON_ICNS="assets/SozakPDFLayoutDesigner.icns"
if [ -f "$ICON_SRC" ] && command -v sips >/dev/null 2>&1 && command -v iconutil >/dev/null 2>&1; then
  ICONSET=".sozak-app-icon.iconset"
  rm -rf "$ICONSET"
  mkdir -p "$ICONSET"
  sips -z 16 16     "$ICON_SRC" --out "$ICONSET/icon_16x16.png" >/dev/null
  sips -z 32 32     "$ICON_SRC" --out "$ICONSET/icon_16x16@2x.png" >/dev/null
  sips -z 32 32     "$ICON_SRC" --out "$ICONSET/icon_32x32.png" >/dev/null
  sips -z 64 64     "$ICON_SRC" --out "$ICONSET/icon_32x32@2x.png" >/dev/null
  sips -z 128 128   "$ICON_SRC" --out "$ICONSET/icon_128x128.png" >/dev/null
  sips -z 256 256   "$ICON_SRC" --out "$ICONSET/icon_128x128@2x.png" >/dev/null
  sips -z 256 256   "$ICON_SRC" --out "$ICONSET/icon_256x256.png" >/dev/null
  sips -z 512 512   "$ICON_SRC" --out "$ICONSET/icon_256x256@2x.png" >/dev/null
  sips -z 512 512   "$ICON_SRC" --out "$ICONSET/icon_512x512.png" >/dev/null
  sips -z 1024 1024 "$ICON_SRC" --out "$ICONSET/icon_512x512@2x.png" >/dev/null
  iconutil -c icns "$ICONSET" -o "$ICON_ICNS"
  rm -rf "$ICONSET"
  echo "  아이콘 갱신: $ICON_ICNS"
elif [ -f "$ICON_ICNS" ]; then
  echo "  macOS iconutil을 사용할 수 없어 포함된 ICNS를 사용합니다."
else
  echo "앱 아이콘 파일을 만들 수 없습니다: $ICON_ICNS"
  exit 1
fi

echo "[5/9] Release smoke test..."
"$VPY" tests/release_smoke_test.py

echo "[6/9] HTTP integration smoke test..."
"$VPY" tests/http_smoke_test.py

echo "[7/9] macOS 앱 빌드..."
rm -rf build dist
"$VPY" -m PyInstaller --noconfirm --clean SozakPDFLayoutDesigner.spec

APP="dist/$APP_NAME.app"
if [ ! -d "$APP" ]; then
  echo "앱 생성에 실패했습니다: $APP"
  read "?Enter를 누르면 종료합니다..."
  exit 1
fi

echo "[8/9] 앱 ad-hoc 서명..."
codesign --force --deep --sign - "$APP"

echo "[9/9] 친구에게 전달할 ZIP / DMG 생성..."
ZIP="dist/Sozak_PDF_Layout_Designer_v${APP_VERSION}_macOS.zip"
DMG="dist/Sozak_PDF_Layout_Designer_v${APP_VERSION}_macOS.dmg"
rm -f "$ZIP" "$DMG"
ditto -c -k --sequesterRsrc --keepParent "$APP" "$ZIP"

DMG_STAGE="dist/_dmg_stage"
rm -rf "$DMG_STAGE"
mkdir -p "$DMG_STAGE"
cp -R "$APP" "$DMG_STAGE/"
ln -s /Applications "$DMG_STAGE/Applications"

hdiutil create \
  -volname "$APP_NAME v$APP_VERSION" \
  -srcfolder "$DMG_STAGE" \
  -ov \
  -format UDZO \
  "$DMG"
rm -rf "$DMG_STAGE"

echo ""
echo "=========================================="
echo "  빌드 완료"
echo "=========================================="
echo ""
echo "앱:"
echo "  $PWD/$APP"
echo ""
echo "친구에게 전달할 파일:"
echo "  $PWD/$ZIP"
echo "  $PWD/$DMG"
echo ""
echo "친구에게는 DMG를 전달하는 것을 권장합니다."
echo "첫 실행 경고가 나오면 앱을 우클릭 > 열기를 사용합니다."
echo "공개 배포처럼 경고 없이 실행하려면 Apple Developer ID 서명과 notarization이 별도로 필요합니다."
echo ""

open dist
read "?Enter를 누르면 빌더를 종료합니다..."

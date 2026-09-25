#!/usr/bin/env bash
# ==============================================================================
# Build macOS .app and .dmg for Pa-O Converter
# Usage: ./scripts/build_macos.sh
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${ROOT_DIR}"

echo "==> Cleaning previous build artifacts..."
rm -rf build dist

echo "==> Building macOS .app with PyInstaller..."
pyinstaller --clean pao_converter.spec

VERSION=$(python3 -c "import sys; sys.path.insert(0, '.'); from core.version import __version__; print(__version__)")
DMG_NAME="PaOConverter_v${VERSION}_macOS.dmg"

echo "==> Removing quarantine attributes from .app..."
xattr -cr "dist/PaOConverter.app"

echo "==> Ad-hoc signing .app to satisfy Gatekeeper..."
codesign --deep --force --sign - "dist/PaOConverter.app" || {
  echo "  [warn] codesign not available — skipping ad-hoc signing"
}

echo "==> Packaging into ${DMG_NAME}..."
STAGING_DIR="dist/dmg_staging"
rm -rf "${STAGING_DIR}"
mkdir -p "${STAGING_DIR}"

# Copy app bundle
cp -R "dist/PaOConverter.app" "${STAGING_DIR}/"

# Create symlink to /Applications for easy drag-and-drop install
ln -s /Applications "${STAGING_DIR}/Applications"

# Generate disk image
hdiutil create \
  -volname "Pa-O Converter" \
  -srcfolder "${STAGING_DIR}" \
  -ov \
  -format UDZO \
  "dist/${DMG_NAME}"

rm -rf "${STAGING_DIR}"

echo ""
echo "=================================================="
echo " SUCCESS: Built dist/${DMG_NAME}"
echo "=================================================="

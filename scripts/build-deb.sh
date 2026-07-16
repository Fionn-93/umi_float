#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
VERSION="${1:-1.0.2}"
APPID="org.deepin.umi-float"
STAGING_DIR=$(mktemp -d)

trap "rm -rf $STAGING_DIR" EXIT

echo "=== Building ${APPID}_${VERSION}_all.deb ==="

# 1. Create UOS app directory structure
APP_ROOT="$STAGING_DIR/opt/apps/$APPID"
mkdir -p "$APP_ROOT/entries/applications"
mkdir -p "$APP_ROOT/entries/icons/hicolor/scalable/apps"
mkdir -p "$APP_ROOT/files"

# 2. Copy entries (desktop + icons)
cp "$PROJECT_DIR/packaging/entries/applications/${APPID}.desktop" \
   "$APP_ROOT/entries/applications/${APPID}.desktop"
cp "$PROJECT_DIR/assets/icon.png" \
   "$APP_ROOT/entries/icons/hicolor/scalable/apps/${APPID}.png"

# 3. Copy info file
cp "$PROJECT_DIR/packaging/info" "$APP_ROOT/info"

# 4. Copy app source code to files/
rsync -a \
    --exclude='.git' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.clawhub' \
    --exclude='venv' \
    --exclude='.venv' \
    --exclude='packaging' \
    --exclude='*.deb' \
    --exclude='tests' \
    --exclude='requirements-dev.txt' \
    --exclude='.gitignore' \
    --exclude='.mypy_cache' \
    --exclude='.pytest_cache' \
    --exclude='.opencode' \
    --exclude='.claude' \
    --exclude='skills' \
    --exclude='*.md' \
    --exclude='.claude' \
    "$PROJECT_DIR/" \
    "$APP_ROOT/files/"

# 5. DEBIAN control file
mkdir -p "$STAGING_DIR/DEBIAN"

cat > "$STAGING_DIR/DEBIAN/control" <<EOF
Package: ${APPID}
Version: ${VERSION}
Section: utils
Priority: optional
Architecture: all
Depends: python3 (>=3.10), python3-pyqt5, python3-pyqt5.qtsvg, python3-requests
Maintainer: Umi-Float Team <team@umi-float.dev>
Description: Desktop floating toolbox for Deepin/UOS
 A lightweight floating ball that stays on top of the desktop,
 providing quick access to system tools and extensions via a
 radial pie panel.
EOF

# 6. Build
OUTPUT="$PROJECT_DIR/${APPID}_${VERSION}_all.deb"
dpkg-deb --build "$STAGING_DIR" "$OUTPUT"

echo ""
echo "=== Built: $OUTPUT ==="
dpkg-deb -c "$OUTPUT" | grep -E '(opt/|DEBIAN)' | head -30

#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
VERSION="${1:-0.1.0}"
STAGING_DIR=$(mktemp -d)

trap "rm -rf $STAGING_DIR" EXIT

echo "=== Building umi-float_${VERSION}_all.deb ==="

# 1. Copy app code to /opt/umi-float/
mkdir -p "$STAGING_DIR/opt/umi-float"
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
    "$PROJECT_DIR/" \
    "$STAGING_DIR/opt/umi-float/"

# 2. Launcher script
mkdir -p "$STAGING_DIR/usr/bin"
cp "$PROJECT_DIR/packaging/usr/bin/umi-float" "$STAGING_DIR/usr/bin/umi-float"
chmod 755 "$STAGING_DIR/usr/bin/umi-float"

# 3. Desktop entry
mkdir -p "$STAGING_DIR/usr/share/applications"
cp "$PROJECT_DIR/packaging/usr/share/applications/umi-float.desktop" \
   "$STAGING_DIR/usr/share/applications/umi-float.desktop"

# 4. Icons — pixmaps + hicolor
mkdir -p "$STAGING_DIR/usr/share/pixmaps"
cp "$PROJECT_DIR/packaging/usr/share/pixmaps/umi-float.png" \
   "$STAGING_DIR/usr/share/pixmaps/umi-float.png"

mkdir -p "$STAGING_DIR/usr/share/icons/hicolor/scalable/apps"
cp "$PROJECT_DIR/assets/icon.png" \
   "$STAGING_DIR/usr/share/icons/hicolor/scalable/apps/umi-float.png"

# 5. DEBIAN control
mkdir -p "$STAGING_DIR/DEBIAN"

cat > "$STAGING_DIR/DEBIAN/control" <<EOF
Package: umi-float
Version: ${VERSION}
Section: utils
Priority: optional
Architecture: all
Depends: python3 (>=3.10), python3-pyqt5, python3-pyqt5.qtsvg, python3-requests
Maintainer: Umi-Float Team
Description: Desktop floating toolbox
 A lightweight desktop floating ball that provides quick access
 to system tools and extensions via a pie panel.
 Features clock, performance monitor, and weather display modes,
 draggable positioning with edge snapping, and extensible plugin system.
EOF

cp "$PROJECT_DIR/packaging/DEBIAN/postinst" "$STAGING_DIR/DEBIAN/postinst"
chmod 755 "$STAGING_DIR/DEBIAN/postinst"

# 6. Build
OUTPUT="$PROJECT_DIR/umi-float_${VERSION}_all.deb"
dpkg-deb --build "$STAGING_DIR" "$OUTPUT"

echo ""
echo "=== Built: $OUTPUT ==="
dpkg-deb -c "$OUTPUT" | grep -E '(usr/|DEBIAN)' | head -20
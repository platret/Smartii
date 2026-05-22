#!/bin/bash
# Build Install-Smartii.app from install-smartii.sh + icons/icon128.png.
# Run on macOS (uses sips + iconutil). Output: installer/Install-Smartii.app
#
# Usage:  bash installer/build-mac-app.sh

set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
APP="$HERE/Install-Smartii.app"
ICON_SRC="$ROOT/icons/icon128.png"
SCRIPT_SRC="$HERE/install-smartii.sh"

[[ -f "$SCRIPT_SRC" ]] || { echo "missing $SCRIPT_SRC"; exit 1; }
[[ -f "$ICON_SRC"  ]] || { echo "missing $ICON_SRC";  exit 1; }

echo "==> wiping previous bundle"
rm -rf "$APP"
mkdir -p "$APP/Contents/MacOS" "$APP/Contents/Resources"

echo "==> writing Info.plist"
cat > "$APP/Contents/Info.plist" <<'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleName</key>
  <string>Install Smartii</string>
  <key>CFBundleDisplayName</key>
  <string>Install Smartii</string>
  <key>CFBundleIdentifier</key>
  <string>com.platret.smartii.installer</string>
  <key>CFBundleVersion</key>
  <string>1.0.0</string>
  <key>CFBundleShortVersionString</key>
  <string>1.0.0</string>
  <key>CFBundlePackageType</key>
  <string>APPL</string>
  <key>CFBundleSignature</key>
  <string>????</string>
  <key>CFBundleExecutable</key>
  <string>install-smartii</string>
  <key>CFBundleIconFile</key>
  <string>AppIcon</string>
  <key>LSMinimumSystemVersion</key>
  <string>10.13</string>
  <key>NSHighResolutionCapable</key>
  <true/>
  <key>LSUIElement</key>
  <false/>
</dict>
</plist>
PLIST

echo "==> writing executable wrapper"
cat > "$APP/Contents/MacOS/install-smartii" <<'EXEC'
#!/bin/bash
# .app entry point. Locates the bundled install-smartii.sh and runs it.
HERE="$(cd "$(dirname "$0")" && pwd)"
SCRIPT="$HERE/../Resources/install-smartii.sh"
if [[ ! -f "$SCRIPT" ]]; then
  /usr/bin/osascript -e 'display alert "Smartii Installer" message "Bundle is corrupt: install-smartii.sh not found." as critical' >/dev/null 2>&1
  exit 1
fi
exec /bin/bash "$SCRIPT"
EXEC
chmod +x "$APP/Contents/MacOS/install-smartii"

echo "==> copying installer script into Resources"
cp "$SCRIPT_SRC" "$APP/Contents/Resources/install-smartii.sh"
chmod +x "$APP/Contents/Resources/install-smartii.sh"

echo "==> generating AppIcon.icns from $ICON_SRC"
ICONSET="$(mktemp -d)/AppIcon.iconset"
mkdir -p "$ICONSET"
# Source is 128x128; upscale to 512 with bicubic via sips for retina sizes.
sips -z 16 16       "$ICON_SRC" --out "$ICONSET/icon_16x16.png"      >/dev/null
sips -z 32 32       "$ICON_SRC" --out "$ICONSET/icon_16x16@2x.png"   >/dev/null
sips -z 32 32       "$ICON_SRC" --out "$ICONSET/icon_32x32.png"      >/dev/null
sips -z 64 64       "$ICON_SRC" --out "$ICONSET/icon_32x32@2x.png"   >/dev/null
sips -z 128 128     "$ICON_SRC" --out "$ICONSET/icon_128x128.png"    >/dev/null
sips -z 256 256     "$ICON_SRC" --out "$ICONSET/icon_128x128@2x.png" >/dev/null
sips -z 256 256     "$ICON_SRC" --out "$ICONSET/icon_256x256.png"    >/dev/null
sips -z 512 512     "$ICON_SRC" --out "$ICONSET/icon_256x256@2x.png" >/dev/null
sips -z 512 512     "$ICON_SRC" --out "$ICONSET/icon_512x512.png"    >/dev/null
sips -z 1024 1024   "$ICON_SRC" --out "$ICONSET/icon_512x512@2x.png" >/dev/null
iconutil -c icns "$ICONSET" -o "$APP/Contents/Resources/AppIcon.icns"
rm -rf "$ICONSET"

# Refresh Finder's icon cache for this bundle.
touch "$APP"

echo "==> done."
echo "    $APP"
echo "    open it with: open '$APP'"

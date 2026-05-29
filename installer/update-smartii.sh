#!/bin/bash
# Smartii in-place updater (macOS / Linux).
#
# Updates the Smartii extension folder to the latest code WITHOUT downloading a
# zip by hand. Run it from inside the Smartii folder, or pass the folder path:
#
#   bash installer/update-smartii.sh
#   bash update-smartii.sh /path/to/Smartii
#
# Behaviour:
#   - If the folder is a git clone  → `git pull` (fast, only changed files).
#   - Otherwise                      → download the latest release zip and
#                                       extract it over the folder.
#
# After it finishes: open Smartii settings and click "Apply & reload", or just
# reload the extension at chrome://extensions. Chrome can't self-install an
# unpacked extension, so this script + the in-app reload button is the closest
# thing to an instant update.

set -u

REPO="platret/Smartii"

# Resolve the target folder: arg, else the repo root relative to this script,
# else the current directory.
if [ "${1:-}" != "" ]; then
  DIR="$1"
else
  SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
  if [ -f "$SCRIPT_DIR/../manifest.json" ]; then
    DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
  else
    DIR="$(pwd)"
  fi
fi

if [ ! -f "$DIR/manifest.json" ]; then
  echo "[smartii] No manifest.json in '$DIR' — point this at your Smartii folder." >&2
  exit 1
fi

echo "[smartii] Updating: $DIR"

if [ -d "$DIR/.git" ]; then
  echo "[smartii] git clone detected — pulling latest…"
  git -C "$DIR" pull --ff-only && {
    echo "[smartii] Done. Open Smartii settings → 'Apply & reload' (or reload at chrome://extensions)."
    exit 0
  }
  echo "[smartii] git pull failed; falling back to zip download." >&2
fi

# Zip fallback.
command -v curl  >/dev/null || { echo "[smartii] curl required." >&2; exit 1; }
command -v unzip >/dev/null || { echo "[smartii] unzip required." >&2; exit 1; }

TMP="$(mktemp -d -t smartii_update)"
trap 'rm -rf "$TMP"' EXIT

echo "[smartii] Fetching latest release…"
ASSET_URL="$(curl -fsSL "https://api.github.com/repos/$REPO/releases/latest" \
  | grep -o '"browser_download_url": *"[^"]*Smartii-v[^"]*\.zip"' \
  | head -1 | sed 's/.*"browser_download_url": *"//;s/"$//')"

if [ -z "$ASSET_URL" ]; then
  echo "[smartii] Couldn't find a release zip asset." >&2
  exit 1
fi

curl -fsSL "$ASSET_URL" -o "$TMP/smartii.zip" || { echo "[smartii] download failed." >&2; exit 1; }
unzip -q "$TMP/smartii.zip" -d "$TMP/x" || { echo "[smartii] unzip failed." >&2; exit 1; }

# The zip unpacks to a top-level Smartii/ folder; copy its contents over $DIR.
SRC="$TMP/x/Smartii"
[ -d "$SRC" ] || SRC="$TMP/x"
cp -R "$SRC"/. "$DIR"/

echo "[smartii] Done. Open Smartii settings → 'Apply & reload' (or reload at chrome://extensions)."

#!/bin/bash
# Smartii Installer for macOS.
# Detects Chromium-based browsers, downloads the latest Smartii release,
# extracts it to ~/Library/Application Support/Smartii, copies that path
# to the clipboard, and opens the chosen browser at chrome://extensions/.
#
# Run directly:
#   bash install-smartii.sh
# Or use the bundled Install-Smartii.app (double-click).

set -u

REPO_OWNER="platret"
REPO_NAME="Smartii"
INSTALL_DIR="$HOME/Library/Application Support/Smartii"
TMP_DIR="$(/usr/bin/mktemp -d -t smartii)"

cleanup() { /bin/rm -rf "$TMP_DIR" 2>/dev/null || true; }
trap cleanup EXIT

alert() {
  local msg="$1" kind="${2:-informational}"
  /usr/bin/osascript -e "display alert \"Smartii Installer\" message \"$msg\" as $kind" >/dev/null 2>&1 || true
}

die() {
  alert "$1" critical
  echo "[smartii] $1" >&2
  exit 1
}

# Need macOS tools
command -v /usr/bin/curl  >/dev/null || die "curl is required but not found."
command -v /usr/bin/unzip >/dev/null || die "unzip is required but not found."
command -v /usr/bin/osascript >/dev/null || die "osascript is required but not found."

# --- detect installed Chromium-based browsers ---
BROWSER_NAMES=()
BROWSER_BUNDLES=()
BROWSER_SCHEMES=()

add_browser() {
  local name="$1" bundle="$2" scheme="$3"
  if [[ -d "$bundle" ]]; then
    BROWSER_NAMES+=("$name")
    BROWSER_BUNDLES+=("$bundle")
    BROWSER_SCHEMES+=("$scheme")
  fi
}

for prefix in "/Applications" "$HOME/Applications"; do
  add_browser "Google Chrome"        "$prefix/Google Chrome.app"        "chrome"
  add_browser "Google Chrome Beta"   "$prefix/Google Chrome Beta.app"   "chrome"
  add_browser "Google Chrome Dev"    "$prefix/Google Chrome Dev.app"    "chrome"
  add_browser "Google Chrome Canary" "$prefix/Google Chrome Canary.app" "chrome"
  add_browser "Microsoft Edge"       "$prefix/Microsoft Edge.app"       "edge"
  add_browser "Brave Browser"        "$prefix/Brave Browser.app"        "brave"
  add_browser "Brave Browser Beta"   "$prefix/Brave Browser Beta.app"   "brave"
  add_browser "Brave Browser Nightly" "$prefix/Brave Browser Nightly.app" "brave"
  add_browser "Arc"                  "$prefix/Arc.app"                  "chrome"
  add_browser "Dia"                  "$prefix/Dia.app"                  "chrome"
  add_browser "Vivaldi"              "$prefix/Vivaldi.app"              "vivaldi"
  add_browser "Opera"                "$prefix/Opera.app"                "opera"
  add_browser "Opera GX"             "$prefix/Opera GX.app"             "opera"
  add_browser "Chromium"             "$prefix/Chromium.app"             "chrome"
  add_browser "Yandex"               "$prefix/Yandex.app"               "browser"
  add_browser "Helium"               "$prefix/Helium.app"               "chrome"
  add_browser "Thorium"              "$prefix/Thorium.app"              "chrome"
  add_browser "Comet"                "$prefix/Comet.app"                "chrome"
done

if [[ ${#BROWSER_NAMES[@]} -eq 0 ]]; then
  die "No Chromium-based browsers found. Install Chrome, Edge, Brave, Arc, Vivaldi, Opera, or similar first, then re-run."
fi

# --- choose-from-list dialog ---
APPLE_LIST=""
for n in "${BROWSER_NAMES[@]}"; do
  esc="${n//\"/\\\"}"
  APPLE_LIST+="\"$esc\","
done
APPLE_LIST="${APPLE_LIST%,}"

CHOICE=$(/usr/bin/osascript <<EOF
set theList to {$APPLE_LIST}
set picked to choose from list theList with title "Smartii Installer" with prompt "Pick a Chromium-based browser to install Smartii into:" default items {item 1 of theList} OK button name "Install" cancel button name "Cancel"
if picked is false then
  return ""
else
  return item 1 of picked
end if
EOF
)

if [[ -z "$CHOICE" ]]; then
  echo "[smartii] cancelled by user."
  exit 0
fi

CHOSEN_IDX=-1
for i in "${!BROWSER_NAMES[@]}"; do
  if [[ "${BROWSER_NAMES[$i]}" == "$CHOICE" ]]; then
    CHOSEN_IDX=$i
    break
  fi
done
[[ $CHOSEN_IDX -lt 0 ]] && die "Could not match your selection — please re-run."

CHOSEN_NAME="${BROWSER_NAMES[$CHOSEN_IDX]}"
CHOSEN_BUNDLE="${BROWSER_BUNDLES[$CHOSEN_IDX]}"
CHOSEN_SCHEME="${BROWSER_SCHEMES[$CHOSEN_IDX]}"

echo "[smartii] target: $CHOSEN_NAME ($CHOSEN_BUNDLE)"

# --- find latest release zip URL ---
API="https://api.github.com/repos/$REPO_OWNER/$REPO_NAME/releases/latest"
META="$TMP_DIR/release.json"
if ! /usr/bin/curl -fsSL -H "User-Agent: SmartiiInstaller" -H "Accept: application/vnd.github+json" "$API" -o "$META"; then
  die "Could not reach GitHub. Check your internet connection."
fi

# Prefer a release-asset .zip, fall back to the source zipball.
ZIP_URL=$(/usr/bin/grep -o '"browser_download_url": *"[^"]*\.zip"' "$META" | /usr/bin/head -1 | /usr/bin/sed -E 's/.*"(https[^"]+)"/\1/')
if [[ -z "$ZIP_URL" ]]; then
  ZIP_URL=$(/usr/bin/grep -o '"zipball_url": *"[^"]*"' "$META" | /usr/bin/head -1 | /usr/bin/sed -E 's/.*"(https[^"]+)"/\1/')
fi
[[ -z "$ZIP_URL" ]] && die "No release zip found on GitHub."

TAG=$(/usr/bin/grep -o '"tag_name": *"[^"]*"' "$META" | /usr/bin/head -1 | /usr/bin/sed -E 's/.*"([^"]+)"/\1/')
echo "[smartii] downloading $TAG from $ZIP_URL"

# --- download + extract ---
ZIP_FILE="$TMP_DIR/smartii.zip"
if ! /usr/bin/curl -fsSL -H "User-Agent: SmartiiInstaller" "$ZIP_URL" -o "$ZIP_FILE"; then
  die "Download failed. Try again later."
fi

EXTRACT_DIR="$TMP_DIR/extracted"
/bin/mkdir -p "$EXTRACT_DIR"
if ! /usr/bin/unzip -q "$ZIP_FILE" -d "$EXTRACT_DIR"; then
  die "Could not unzip the downloaded archive."
fi

# Archive may nest one directory deep (zipball, release zip both do).
MANIFEST=$(/usr/bin/find "$EXTRACT_DIR" -maxdepth 4 -name "manifest.json" -type f | /usr/bin/head -1)
[[ -z "$MANIFEST" ]] && die "manifest.json not found in downloaded archive."
SRC_DIR=$(/usr/bin/dirname "$MANIFEST")

# --- install to ~/Library/Application Support/Smartii ---
/bin/rm -rf "$INSTALL_DIR"
/bin/mkdir -p "$INSTALL_DIR"
# Use ditto to preserve resource forks and handle hidden files.
/usr/bin/ditto "$SRC_DIR" "$INSTALL_DIR"

echo "[smartii] installed to $INSTALL_DIR"

# Copy path to clipboard for the Load-unpacked dialog.
printf '%s' "$INSTALL_DIR" | /usr/bin/pbcopy

# --- open the browser at chrome://extensions/ ---
/usr/bin/open -a "$CHOSEN_BUNDLE" "${CHOSEN_SCHEME}://extensions/" 2>/dev/null || \
  /usr/bin/open "$CHOSEN_BUNDLE"

# --- final dialog with next steps ---
ESC_PATH="${INSTALL_DIR//\\/\\\\}"
ESC_PATH="${ESC_PATH//\"/\\\"}"
ESC_NAME="${CHOSEN_NAME//\"/\\\"}"

/usr/bin/osascript <<EOF >/dev/null 2>&1
display dialog "Smartii $TAG installed.

Location (already copied to your clipboard):
$ESC_PATH

Finish in $ESC_NAME:
1. Toggle Developer mode (top-right).
2. Click 'Load unpacked'.
3. Press ⌘V in the path field and hit Return.

Then press ⌘⇧S on any page to summon Smartii." with title "Smartii Installer" buttons {"Done"} default button "Done" with icon note
EOF

echo "[smartii] done."
exit 0

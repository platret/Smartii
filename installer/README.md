# Smartii Installers

Tiny per-platform helpers that do the boring parts of installing Smartii:

- **Windows** — `Install-Smartii.exe` / `Install-Smartii.ps1` (WinForms + PowerShell).
- **macOS** — `Install-Smartii.app` / `install-smartii.sh` (osascript dialogs + bash).
- **Linux** — `install-smartii.sh` runs on Linux too if you adapt the browser paths; PR welcome.

---

## Windows (`Install-Smartii.exe`)

Tiny Windows helper that does the boring parts of installing Smartii:

1. **Detects** every Chromium-based browser on your system (Chrome, Edge, Brave, Vivaldi, Opera, Opera GX, Arc, Chromium, Yandex).
2. **Downloads** the latest Smartii release zip from GitHub and extracts it to `%LOCALAPPDATA%\Smartii\`.
3. **Copies that path** to your clipboard.
4. **Opens** the right `chrome://extensions/` (or `edge://`, `brave://`, …) in the browser you picked.
5. Optionally **launches** that browser with `--load-extension=…` so Smartii is live the moment the window opens (ephemeral — survives until you fully restart the browser; use the persistent Load-unpacked step too).

You still click **Load unpacked → paste path → Enter** once. That step cannot be automated for an unpacked extension; Chromium intentionally requires the user to confirm developer-mode installs. Everything else is handled.

## Two ways to run it

### Option A — `Install-Smartii.exe` (single-click)

Grab it from the latest [release](https://github.com/platret/Smartii/releases/latest) and double-click. SmartScreen may warn the first time; click *More info → Run anyway*. The .exe is just this folder's PowerShell script bundled by [ps2exe](https://github.com/MScholtes/PS2EXE), no compiled binaries, no network listeners.

### Option B — `Install-Smartii.ps1` (audit-friendly)

If you'd rather read the source first:

```powershell
# from this folder
powershell -ExecutionPolicy Bypass -File .\Install-Smartii.ps1
```

The script is short — a couple hundred lines of WinForms + an `Invoke-WebRequest` call to GitHub. Read it before you run it.

## macOS (`Install-Smartii.app`)

Double-clickable Mac bundle that mirrors the Windows flow:

1. **Detects** every Chromium-based browser in `/Applications` and `~/Applications` (Chrome, Chrome Beta/Dev/Canary, Edge, Brave + Beta + Nightly, Arc, Dia, Vivaldi, Opera, Opera GX, Chromium, Yandex, Helium, Thorium, Comet).
2. **Downloads** the latest Smartii release zip from GitHub and extracts it to `~/Library/Application Support/Smartii/`.
3. **Copies that path** to your clipboard via `pbcopy`.
4. **Opens** the chosen browser at the right `chrome://extensions/` (or `edge://`, `brave://`, `vivaldi://`, `opera://`, `browser://`) page.
5. Shows a final dialog with the three remaining steps.

You still click **Load unpacked → ⌘V → Return** once. Chromium intentionally forces a human to confirm developer-mode loads — that step cannot be automated.

### Two ways to run it on Mac

#### Option A — `Install-Smartii.app` (double-click)

Grab `Install-Smartii.app.zip` from the latest [release](https://github.com/platret/Smartii/releases/latest), unzip, and double-click the `.app`.

> **Gatekeeper note:** the app is unsigned, so the first launch will be blocked. Right-click → **Open** → **Open**, or run `xattr -dr com.apple.quarantine /path/to/Install-Smartii.app` once.

#### Option B — `install-smartii.sh` (audit-friendly)

If you'd rather read the source first:

```bash
# from this folder
bash ./install-smartii.sh
```

It's ~180 lines of bash + osascript and a single `curl` call to GitHub's release API. Read it before you run it.

### Re-building the `.app`

The bundle is produced by `build-mac-app.sh` from the sibling shell script + `../icons/icon128.png`. Requires `sips` + `iconutil` (both ship with macOS).

```bash
bash installer/build-mac-app.sh
# → installer/Install-Smartii.app
```

To ship a clean zip on a release:

```bash
cd installer
ditto -c -k --sequesterRsrc --keepParent Install-Smartii.app Install-Smartii.app.zip
```

---

## Linux

The bash installer is mostly portable — Chromium binaries on Linux just live in different places (`/usr/bin/google-chrome`, `/usr/bin/brave-browser`, `/snap/bin/chromium`, etc.). Patch the `add_browser` block in `install-smartii.sh` to point at your distro's paths, drop the `pbcopy`/`open -a` macOS-isms, and it works. PR welcome.

## Re-building the .exe

Requires Windows PowerShell 5.1+ and the [ps2exe](https://www.powershellgallery.com/packages/ps2exe) module.

```powershell
Install-Module ps2exe -Scope CurrentUser

Invoke-PS2EXE `
  -InputFile  .\Install-Smartii.ps1 `
  -OutputFile .\bin\Install-Smartii.exe `
  -IconFile   ..\icons\icon.ico `
  -Title 'Smartii Installer' `
  -Product 'Smartii Installer' `
  -Version '1.0.2.0' `
  -NoConsole
```

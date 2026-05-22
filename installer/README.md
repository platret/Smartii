# Smartii Installer (Windows)

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

## What about macOS / Linux?

Chromium browsers on macOS and Linux follow the same install flow (Load unpacked from a folder), but the path detection and `--load-extension` invocation differ. A cross-platform installer isn't shipped yet — for now, follow the manual steps in the project README.

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

# Smartii in-place updater (Windows / PowerShell).
#
# Updates the Smartii extension folder to the latest code without downloading a
# zip by hand. Run from inside the Smartii folder, or pass the folder path:
#
#   powershell -ExecutionPolicy Bypass -File installer\update-smartii.ps1
#   powershell -ExecutionPolicy Bypass -File update-smartii.ps1 C:\path\to\Smartii
#
# If the folder is a git clone it runs `git pull`; otherwise it downloads the
# latest release zip and extracts it over the folder. Afterwards open Smartii
# settings and click "Apply & reload" (or reload at chrome://extensions).

param([string]$Dir = "")

$ErrorActionPreference = "Stop"
$Repo = "platret/Smartii"

if (-not $Dir) {
  $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
  if (Test-Path (Join-Path $scriptDir "..\manifest.json")) {
    $Dir = (Resolve-Path (Join-Path $scriptDir "..")).Path
  } else {
    $Dir = (Get-Location).Path
  }
}

if (-not (Test-Path (Join-Path $Dir "manifest.json"))) {
  Write-Error "No manifest.json in '$Dir' — point this at your Smartii folder."
  exit 1
}

Write-Host "[smartii] Updating: $Dir"

if (Test-Path (Join-Path $Dir ".git")) {
  Write-Host "[smartii] git clone detected — pulling latest..."
  & git -C $Dir pull --ff-only
  if ($LASTEXITCODE -eq 0) {
    Write-Host "[smartii] Done. Open Smartii settings -> 'Apply & reload' (or reload at chrome://extensions)."
    exit 0
  }
  Write-Warning "[smartii] git pull failed; falling back to zip download."
}

$tmp = Join-Path $env:TEMP ("smartii_update_" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $tmp | Out-Null
try {
  Write-Host "[smartii] Fetching latest release..."
  $rel = Invoke-RestMethod -Uri "https://api.github.com/repos/$Repo/releases/latest" -Headers @{ "User-Agent" = "smartii-updater" }
  $asset = $rel.assets | Where-Object { $_.name -like "Smartii-v*.zip" } | Select-Object -First 1
  if (-not $asset) { Write-Error "Couldn't find a release zip asset."; exit 1 }

  $zip = Join-Path $tmp "smartii.zip"
  Invoke-WebRequest -Uri $asset.browser_download_url -OutFile $zip -Headers @{ "User-Agent" = "smartii-updater" }
  Expand-Archive -Path $zip -DestinationPath (Join-Path $tmp "x") -Force

  $src = Join-Path $tmp "x\Smartii"
  if (-not (Test-Path $src)) { $src = Join-Path $tmp "x" }
  Copy-Item -Path (Join-Path $src "*") -Destination $Dir -Recurse -Force

  Write-Host "[smartii] Done. Open Smartii settings -> 'Apply & reload' (or reload at chrome://extensions)."
} finally {
  Remove-Item -Recurse -Force $tmp -ErrorAction SilentlyContinue
}

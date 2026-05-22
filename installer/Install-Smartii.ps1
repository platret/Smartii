# Smartii Installer
# A small WinForms helper that detects installed Chromium-based browsers,
# downloads the latest Smartii release from GitHub, extracts it to
# %LOCALAPPDATA%\Smartii, copies the path to the clipboard, and opens the
# correct extensions page in the chosen browser.
#
# Run directly with:   powershell -ExecutionPolicy Bypass -File Install-Smartii.ps1
# Or use the bundled  Install-Smartii.exe (built from this same script via ps2exe).

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
[System.Windows.Forms.Application]::EnableVisualStyles()
[System.Windows.Forms.Application]::SetCompatibleTextRenderingDefault($false)

# -------- config --------
$RepoOwner  = "platret"
$RepoName   = "Smartii"
$InstallDir = Join-Path $env:LOCALAPPDATA "Smartii"
$BrandBg    = [System.Drawing.Color]::FromArgb(13, 13, 18)
$BrandCard  = [System.Drawing.Color]::FromArgb(22, 22, 30)
$BrandText  = [System.Drawing.Color]::FromArgb(243, 243, 247)
$BrandMuted = [System.Drawing.Color]::FromArgb(155, 155, 168)
$BrandAccent= [System.Drawing.Color]::FromArgb(124, 92, 255)
$BrandAcc2  = [System.Drawing.Color]::FromArgb(74, 214, 255)

# -------- browser catalog --------
$pf  = ${env:ProgramFiles}
$pfx = ${env:ProgramFiles(x86)}
$lad = $env:LOCALAPPDATA

$BrowserCatalog = @(
    @{ Name = "Google Chrome";  Paths = @("$pf\Google\Chrome\Application\chrome.exe", "$pfx\Google\Chrome\Application\chrome.exe", "$lad\Google\Chrome\Application\chrome.exe"); Scheme = "chrome" }
    @{ Name = "Microsoft Edge"; Paths = @("$pfx\Microsoft\Edge\Application\msedge.exe", "$pf\Microsoft\Edge\Application\msedge.exe"); Scheme = "edge" }
    @{ Name = "Brave";          Paths = @("$pf\BraveSoftware\Brave-Browser\Application\brave.exe", "$pfx\BraveSoftware\Brave-Browser\Application\brave.exe", "$lad\BraveSoftware\Brave-Browser\Application\brave.exe"); Scheme = "brave" }
    @{ Name = "Vivaldi";        Paths = @("$lad\Vivaldi\Application\vivaldi.exe", "$pf\Vivaldi\Application\vivaldi.exe", "$pfx\Vivaldi\Application\vivaldi.exe"); Scheme = "vivaldi" }
    @{ Name = "Opera";          Paths = @("$lad\Programs\Opera\opera.exe", "$lad\Programs\Opera\launcher.exe"); Scheme = "opera" }
    @{ Name = "Opera GX";       Paths = @("$lad\Programs\Opera GX\opera.exe", "$lad\Programs\Opera GX\launcher.exe"); Scheme = "opera" }
    @{ Name = "Arc";            Paths = @("$lad\Programs\Arc\Arc.exe"); Scheme = "chrome" }
    @{ Name = "Chromium";       Paths = @("$pf\Chromium\Application\chrome.exe", "$lad\Chromium\Application\chrome.exe"); Scheme = "chrome" }
    @{ Name = "Yandex";         Paths = @("$lad\Yandex\YandexBrowser\Application\browser.exe"); Scheme = "browser" }
)

function Find-InstalledBrowsers {
    $found = New-Object System.Collections.Generic.List[object]
    foreach ($b in $BrowserCatalog) {
        foreach ($p in $b.Paths) {
            if ($p -and (Test-Path $p)) {
                $found.Add([pscustomobject]@{
                    Name   = $b.Name
                    Path   = $p
                    Scheme = $b.Scheme
                })
                break
            }
        }
    }
    return $found
}

# -------- core actions --------
function Get-LatestReleaseZipUrl {
    $api = "https://api.github.com/repos/$RepoOwner/$RepoName/releases/latest"
    $headers = @{ 'User-Agent' = 'SmartiiInstaller'; 'Accept' = 'application/vnd.github+json' }
    $rel = Invoke-RestMethod -Uri $api -Headers $headers -ErrorAction Stop
    $asset = $rel.assets | Where-Object { $_.name -match '\.zip$' } | Select-Object -First 1
    if (-not $asset) {
        # Fall back to source zip
        return @{ Url = $rel.zipball_url; Tag = $rel.tag_name; IsSource = $true }
    }
    return @{ Url = $asset.browser_download_url; Tag = $rel.tag_name; IsSource = $false }
}

function Install-Extension {
    param([string]$ZipUrl, [string]$Dest)

    $tmpZip = Join-Path $env:TEMP ("smartii_" + [guid]::NewGuid().ToString() + ".zip")
    $headers = @{ 'User-Agent' = 'SmartiiInstaller' }
    Invoke-WebRequest -Uri $ZipUrl -OutFile $tmpZip -Headers $headers -ErrorAction Stop

    $tmpDir = Join-Path $env:TEMP ("smartii_x_" + [guid]::NewGuid().ToString())
    New-Item -ItemType Directory -Path $tmpDir -Force | Out-Null
    Expand-Archive -Path $tmpZip -DestinationPath $tmpDir -Force

    if (Test-Path $Dest) { Remove-Item $Dest -Recurse -Force -ErrorAction SilentlyContinue }
    New-Item -ItemType Directory -Path $Dest -Force | Out-Null

    # Find the folder that contains manifest.json (zip may nest one level deep)
    $manifest = Get-ChildItem -Path $tmpDir -Recurse -Filter 'manifest.json' -File | Select-Object -First 1
    if (-not $manifest) { throw "manifest.json not found in downloaded archive" }
    $root = $manifest.DirectoryName

    Get-ChildItem -Path $root -Force | ForEach-Object {
        Copy-Item $_.FullName -Destination $Dest -Recurse -Force
    }

    Remove-Item $tmpZip -Force -ErrorAction SilentlyContinue
    Remove-Item $tmpDir -Recurse -Force -ErrorAction SilentlyContinue
}

function Open-Browser {
    param($Browser, [string]$ExtPath, [switch]$WithLoadExtension)
    $url = $Browser.Scheme + "://extensions/"
    $args = @()
    if ($WithLoadExtension) {
        $args += "--load-extension=`"$ExtPath`""
    }
    $args += $url
    Start-Process -FilePath $Browser.Path -ArgumentList $args
}

# -------- UI --------
$form = New-Object System.Windows.Forms.Form
$form.Text = "Smartii Installer"
$form.ClientSize = New-Object System.Drawing.Size(540, 500)
$form.StartPosition = "CenterScreen"
$form.FormBorderStyle = "FixedSingle"
$form.MaximizeBox = $false
$form.BackColor = $BrandBg
$form.ForeColor = $BrandText
$form.Font = New-Object System.Drawing.Font("Segoe UI", 9)

# --- header band ---
$header = New-Object System.Windows.Forms.Panel
$header.Size = New-Object System.Drawing.Size(540, 90)
$header.Location = New-Object System.Drawing.Point(0, 0)
$header.BackColor = $BrandCard
$form.Controls.Add($header)

$header.Add_Paint({
    param($sender, $e)
    $rect = New-Object System.Drawing.Rectangle 0, 0, $sender.Width, $sender.Height
    $brush = New-Object System.Drawing.Drawing2D.LinearGradientBrush $rect, $BrandAccent, $BrandAcc2, ([float]15)
    $e.Graphics.FillRectangle($brush, 0, $sender.Height - 3, $sender.Width, 3)
    $brush.Dispose()
})

$logoTile = New-Object System.Windows.Forms.Panel
$logoTile.Size = New-Object System.Drawing.Size(56, 56)
$logoTile.Location = New-Object System.Drawing.Point(22, 17)
$logoTile.BackColor = $BrandCard
$header.Controls.Add($logoTile)
$logoTile.Add_Paint({
    param($sender, $e)
    $g = $e.Graphics
    $g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
    $g.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::AntiAlias
    $rect = New-Object System.Drawing.Rectangle 0, 0, $sender.Width, $sender.Height
    $brush = New-Object System.Drawing.Drawing2D.LinearGradientBrush $rect, $BrandAccent, $BrandAcc2, ([float]45)
    $path = New-Object System.Drawing.Drawing2D.GraphicsPath
    $r = 12; $d = $r * 2
    $path.AddArc(0, 0, $d, $d, 180, 90)
    $path.AddArc($sender.Width - $d, 0, $d, $d, 270, 90)
    $path.AddArc($sender.Width - $d, $sender.Height - $d, $d, $d, 0, 90)
    $path.AddArc(0, $sender.Height - $d, $d, $d, 90, 90)
    $path.CloseFigure()
    $g.FillPath($brush, $path)
    $font = New-Object System.Drawing.Font 'Segoe UI', 28, [System.Drawing.FontStyle]::Bold, [System.Drawing.GraphicsUnit]::Pixel
    $sf = New-Object System.Drawing.StringFormat
    $sf.Alignment = [System.Drawing.StringAlignment]::Center
    $sf.LineAlignment = [System.Drawing.StringAlignment]::Center
    $white = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::White)
    $textRect = New-Object System.Drawing.RectangleF 0, -2, ([float]$sender.Width), ([float]$sender.Height)
    $g.DrawString('S', $font, $white, $textRect, $sf)
    $brush.Dispose(); $path.Dispose(); $font.Dispose(); $white.Dispose()
})

$title = New-Object System.Windows.Forms.Label
$title.Text = "Smartii"
$title.Font = New-Object System.Drawing.Font("Segoe UI Semibold", 18)
$title.ForeColor = $BrandText
$title.AutoSize = $true
$title.Location = New-Object System.Drawing.Point(94, 18)
$title.BackColor = $BrandCard
$header.Controls.Add($title)

$subtitle = New-Object System.Windows.Forms.Label
$subtitle.Text = "Install Smartii into a Chromium browser"
$subtitle.Font = New-Object System.Drawing.Font("Segoe UI", 9)
$subtitle.ForeColor = $BrandMuted
$subtitle.AutoSize = $true
$subtitle.Location = New-Object System.Drawing.Point(96, 52)
$subtitle.BackColor = $BrandCard
$header.Controls.Add($subtitle)

# --- body ---
$y = 110
function Add-Label([string]$text, [int]$size = 9, [System.Drawing.Color]$color = $BrandText, [bool]$bold = $false) {
    $l = New-Object System.Windows.Forms.Label
    $l.Text = $text
    $style = if ($bold) { [System.Drawing.FontStyle]::Bold } else { [System.Drawing.FontStyle]::Regular }
    $l.Font = New-Object System.Drawing.Font("Segoe UI", $size, $style)
    $l.ForeColor = $color
    $l.AutoSize = $true
    $l.Location = New-Object System.Drawing.Point(28, $script:y)
    $form.Controls.Add($l)
    $script:y += $l.PreferredHeight + 6
    return $l
}

Add-Label "1.  Choose a browser" 10 $BrandText $true | Out-Null

$browserBox = New-Object System.Windows.Forms.ComboBox
$browserBox.Location = New-Object System.Drawing.Point(28, $y)
$browserBox.Size = New-Object System.Drawing.Size(484, 28)
$browserBox.DropDownStyle = "DropDownList"
$browserBox.FlatStyle = "Flat"
$browserBox.BackColor = $BrandCard
$browserBox.ForeColor = $BrandText
$browserBox.Font = New-Object System.Drawing.Font("Segoe UI", 10)
$form.Controls.Add($browserBox)
$y += 38

$browsers = Find-InstalledBrowsers
if ($browsers.Count -eq 0) {
    $browserBox.Items.Add("No Chromium browsers detected") | Out-Null
    $browserBox.Enabled = $false
} else {
    foreach ($b in $browsers) { $browserBox.Items.Add($b.Name) | Out-Null }
    $browserBox.SelectedIndex = 0
}

Add-Label "2.  Install location" 10 $BrandText $true | Out-Null
$pathLabel = New-Object System.Windows.Forms.TextBox
$pathLabel.Text = $InstallDir
$pathLabel.Location = New-Object System.Drawing.Point(28, $y)
$pathLabel.Size = New-Object System.Drawing.Size(484, 26)
$pathLabel.BackColor = $BrandCard
$pathLabel.ForeColor = $BrandMuted
$pathLabel.BorderStyle = "FixedSingle"
$pathLabel.ReadOnly = $true
$pathLabel.Font = New-Object System.Drawing.Font("Consolas", 9)
$form.Controls.Add($pathLabel)
$y += 34

# --- launch checkbox ---
$launchChk = New-Object System.Windows.Forms.CheckBox
$launchChk.Text = "Also launch the browser with Smartii pre-loaded (ephemeral try)"
$launchChk.Location = New-Object System.Drawing.Point(28, $y)
$launchChk.AutoSize = $true
$launchChk.ForeColor = $BrandMuted
$launchChk.BackColor = $BrandBg
$launchChk.Checked = $true
$form.Controls.Add($launchChk)
$y += 30

# --- install button ---
$installBtn = New-Object System.Windows.Forms.Button
$installBtn.Text = "Install Smartii"
$installBtn.Location = New-Object System.Drawing.Point(28, $y)
$installBtn.Size = New-Object System.Drawing.Size(484, 44)
$installBtn.FlatStyle = "Flat"
$installBtn.FlatAppearance.BorderSize = 0
$installBtn.BackColor = $BrandAccent
$installBtn.ForeColor = [System.Drawing.Color]::White
$installBtn.Font = New-Object System.Drawing.Font("Segoe UI Semibold", 11)
$installBtn.Cursor = "Hand"
$form.Controls.Add($installBtn)
$y += 56

# --- status box ---
$status = New-Object System.Windows.Forms.TextBox
$status.Location = New-Object System.Drawing.Point(28, $y)
$status.Size = New-Object System.Drawing.Size(484, 110)
$status.Multiline = $true
$status.ReadOnly = $true
$status.BackColor = $BrandCard
$status.ForeColor = $BrandMuted
$status.BorderStyle = "FixedSingle"
$status.Font = New-Object System.Drawing.Font("Consolas", 9)
$status.ScrollBars = "Vertical"
$form.Controls.Add($status)

function Write-Status([string]$msg) {
    $status.AppendText($msg + "`r`n")
    [System.Windows.Forms.Application]::DoEvents()
}

# --- install action ---
$installBtn.Add_Click({
    if ($browsers.Count -eq 0) {
        [System.Windows.Forms.MessageBox]::Show(
            "No Chromium browsers were detected. Install Chrome, Edge, Brave, Opera, or Vivaldi first.",
            "Smartii Installer", "OK", "Warning") | Out-Null
        return
    }
    $installBtn.Enabled = $false
    $installBtn.Text = "Installing..."
    $status.Clear()
    $chosen = $browsers[$browserBox.SelectedIndex]

    try {
        Write-Status "-> Fetching latest release info from GitHub..."
        $rel = Get-LatestReleaseZipUrl
        $srcNote = if ($rel.IsSource) { " (source zip)" } else { " (release asset)" }
        Write-Status ("  found " + $rel.Tag + $srcNote)

        Write-Status "-> Downloading and extracting to:"
        Write-Status ("  " + $InstallDir)
        Install-Extension -ZipUrl $rel.Url -Dest $InstallDir
        Write-Status "  done."

        Write-Status "-> Copying install path to your clipboard."
        Set-Clipboard -Value $InstallDir

        Write-Status ("-> Opening " + $chosen.Name + " at " + $chosen.Scheme + "://extensions/ ...")
        Open-Browser -Browser $chosen -ExtPath $InstallDir -WithLoadExtension:$launchChk.Checked

        Write-Status ""
        Write-Status "[OK] Almost done. In the browser tab that just opened:"
        Write-Status "    1. Toggle 'Developer mode' (top right)"
        Write-Status "    2. Click 'Load unpacked'"
        Write-Status "    3. Paste with Ctrl+V -- the install path is on your clipboard."
        Write-Status ""
        Write-Status "Then press Ctrl+Shift+S on any page to summon Smartii."

        $installBtn.Text = "Done [OK]"
        $installBtn.BackColor = [System.Drawing.Color]::FromArgb(74, 222, 128)
    } catch {
        Write-Status ""
        Write-Status ("[X] Error: " + $_.Exception.Message)
        $installBtn.Text = "Try again"
        $installBtn.Enabled = $true
        $installBtn.BackColor = $BrandAccent
    }
})

[void]$form.ShowDialog()

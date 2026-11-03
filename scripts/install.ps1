# Adds the HD texture pack to METAL GEAR SOLID (Master Collection, Steam).
# Run from the game folder (where "METAL GEAR SOLID.exe" is), after copying the release files there.
# It changes only windata\alldata.bin (data appended at the end) and windata\alldata.psb.m (index, backed up first).
# uninstall.ps1 puts both back exactly.
$ErrorActionPreference = 'Stop'
$game = $PSScriptRoot
$bin = Join-Path $game 'windata\alldata.bin'; $idx = Join-Path $game 'windata\alldata.psb.m'
$m = Get-Content (Join-Path $game 'MGSModernTextures\manifest.json') -Raw | ConvertFrom-Json
function Sha([string]$p) { (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLower() }
if (-not (Test-Path (Join-Path $game 'METAL GEAR SOLID.exe'))) { throw "Run this from the MGS1 game folder (METAL GEAR SOLID.exe not found in $game)." }
if (Get-Process -Name 'METAL GEAR SOLID' -ErrorAction SilentlyContinue) { throw 'Close the game first.' }
$size = (Get-Item -LiteralPath $bin).Length; $ih = Sha $idx
if ($size -eq $m.installed_size -and $ih -eq $m.installed_index_sha256) { Write-Host 'The HD texture pack is already installed.'; return }
if ($size -ne $m.stock_size -or $ih -ne $m.stock_index_sha256) {
    throw "windata\alldata.bin / alldata.psb.m are not the stock files this pack was built for (size $size, index $ih). Nothing was changed. Verify the game files in Steam, then run this again."
}
$add = Join-Path $game 'MGSModernTextures\alldata.append.bin'; $newIdx = Join-Path $game 'MGSModernTextures\alldata.psb.m'
if ((Sha $add) -ne $m.append_sha256 -or (Sha $newIdx) -ne $m.installed_index_sha256) { throw 'The pack files are damaged (hash mismatch). Download the release again.' }
Copy-Item -LiteralPath $idx -Destination "$idx.stock" -Force
if ((Sha "$idx.stock") -ne $m.stock_index_sha256) { throw 'Could not back up alldata.psb.m. Nothing was changed.' }
$out = [System.IO.File]::Open($bin, 'Append', 'Write'); $in = [System.IO.File]::OpenRead($add)
try { $in.CopyTo($out) } finally { $in.Close(); $out.Close() }
Copy-Item -LiteralPath $newIdx -Destination $idx -Force
if ((Get-Item -LiteralPath $bin).Length -ne $m.installed_size -or (Sha $idx) -ne $m.installed_index_sha256) { throw 'Install check failed. Run UNINSTALL.bat to restore the stock files.' }
Write-Host 'HD texture pack installed. In game: F7 HD textures, F8 lighting, F6 image effects.'

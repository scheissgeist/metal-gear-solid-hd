# Removes the HD texture pack, putting windata\alldata.bin and alldata.psb.m back to the stock files.
# Run from the game folder. To remove the whole mod afterwards, delete the files listed in README.txt.
$ErrorActionPreference = 'Stop'
$game = $PSScriptRoot
$bin = Join-Path $game 'windata\alldata.bin'; $idx = Join-Path $game 'windata\alldata.psb.m'
$m = Get-Content (Join-Path $game 'MGSModernTextures\manifest.json') -Raw | ConvertFrom-Json
function Sha([string]$p) { (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLower() }
if (Get-Process -Name 'METAL GEAR SOLID' -ErrorAction SilentlyContinue) { throw 'Close the game first.' }
$size = (Get-Item -LiteralPath $bin).Length; $ih = Sha $idx
if ($size -eq $m.stock_size -and $ih -eq $m.stock_index_sha256) { Write-Host 'The texture pack is not installed; the stock files are in place.'; return }
if ($size -ne $m.installed_size -or $ih -ne $m.installed_index_sha256) {
    throw "windata\alldata.bin / alldata.psb.m are not the files this pack installs (size $size). Nothing was changed. Use Steam's 'Verify integrity of game files' to restore them."
}
$stockIdx = "$idx.stock"
if (-not (Test-Path -LiteralPath $stockIdx) -or (Sha $stockIdx) -ne $m.stock_index_sha256) {
    throw "The backup $stockIdx is missing or changed. Nothing was changed. Use Steam's 'Verify integrity of game files' instead."
}
$f = [System.IO.File]::Open($bin, 'Open', 'Write')
try { $f.SetLength($m.stock_size) } finally { $f.Close() }
Copy-Item -LiteralPath $stockIdx -Destination $idx -Force
if ((Get-Item -LiteralPath $bin).Length -ne $m.stock_size -or (Sha $idx) -ne $m.stock_index_sha256) { throw "Restore check failed. Use Steam's 'Verify integrity of game files'." }
Write-Host 'HD texture pack removed; stock game files restored.'

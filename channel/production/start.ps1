$ErrorActionPreference = 'Stop'
$channelRoot = Split-Path -Parent $PSScriptRoot
$runtimePath = Join-Path $PSScriptRoot 'runtime.json'
if (-not (Test-Path -LiteralPath $runtimePath)) {
  Write-Host 'Local production runtime is not configured. See README.md for setup.'
  exit 1
}
$currentRuntime = Get-Content -LiteralPath $runtimePath -Raw | ConvertFrom-Json
$env:CURRENT_PIPER_MODEL_DIR = $currentRuntime.modelDir
$env:CURRENT_FFMPEG = $currentRuntime.ffmpeg
Set-Location -LiteralPath $channelRoot
& $currentRuntime.python (Join-Path $PSScriptRoot 'server.py') --open-browser

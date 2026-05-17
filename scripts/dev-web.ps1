# Start LEXGUARD frontend (Next.js on :3000)
$nodeTools = Join-Path $PSScriptRoot "..\.tools\node"
if (-not (Test-Path "$nodeTools\npm.cmd")) {
    Write-Host "Portable Node not found. Run from repo root or install Node.js LTS from https://nodejs.org/"
    exit 1
}
$env:Path = "$nodeTools;" + $env:Path
Set-Location (Join-Path $PSScriptRoot "..")
pnpm dev:web

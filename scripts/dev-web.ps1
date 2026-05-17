# Start LEXGUARD frontend (Next.js on :3000)
$nodeTools = Join-Path $PSScriptRoot "..\.tools\node"
if (Test-Path "$nodeTools\node.exe") {
    $env:Path = "$nodeTools;" + $env:Path
} elseif (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    Write-Host "Install Node.js LTS from https://nodejs.org/ (optional: portable Node in .tools/node)"
    exit 1
}
Set-Location (Join-Path $PSScriptRoot "..")
pnpm dev:web

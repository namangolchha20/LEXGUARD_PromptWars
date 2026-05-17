# Remove local caches and runtime data (safe to delete; not in git).
$root = Resolve-Path (Join-Path $PSScriptRoot "..")
$targets = @(
    (Join-Path $root "apps\web\.next"),
    (Join-Path $root "apps\web\out"),
    (Join-Path $root "node_modules"),
    (Join-Path $root ".pnpm-store"),
    (Join-Path $root ".venv"),
    (Join-Path $root ".tools"),
    (Join-Path $root "data")
)

foreach ($path in $targets) {
    if (Test-Path $path) {
        Write-Host "Removing $path"
        Remove-Item -LiteralPath $path -Recurse -Force -ErrorAction SilentlyContinue
    }
}

$dataRoot = Join-Path $root "data"
New-Item -ItemType Directory -Force -Path $dataRoot | Out-Null
New-Item -ItemType File -Force -Path (Join-Path $dataRoot ".gitkeep") | Out-Null
Write-Host "Done. Reinstall: pip install -r requirements.txt ; pnpm install"

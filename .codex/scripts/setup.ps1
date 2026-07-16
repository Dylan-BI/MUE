$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
Set-Location $repoRoot
$env:PYTHONIOENCODING = "utf-8"

function Get-MuePython {
    $pyLauncher = Get-Command py -ErrorAction SilentlyContinue
    if ($pyLauncher) {
        return @{
            Command = $pyLauncher.Source
            Prefix = @("-3")
        }
    }

    $python = Get-Command python -ErrorAction SilentlyContinue
    if ($python) {
        return @{
            Command = $python.Source
            Prefix = @()
        }
    }

    throw "Python 3.9+ is required for the MUE dashboard environment."
}

$python = Get-MuePython
$versionCheck = "import sys; raise SystemExit(0 if sys.version_info >= (3, 9) else 'Python 3.9+ is required')"
& $python.Command @($python.Prefix + @("-c", $versionCheck))

& $python.Command @($python.Prefix + @("action/dashboard/build_data.py"))

Write-Host "MUE environment ready."
Write-Host "Dashboard file: action/dashboard/dashboard.html"
Write-Host "Review server:  powershell -ExecutionPolicy Bypass -File .codex/scripts/serve-review-dashboard.ps1"

<#
.SYNOPSIS
    Launch the MUE Learner Dashboard in your browser.
.DESCRIPTION
    Installs dependencies if needed and starts the Streamlit dashboard
    that reads from action/notes/, action/evidence/, and action/reports/.
.EXAMPLE
    .\launcher.ps1
#>

$RepoRoot = Split-Path -Path $PSScriptRoot -Parent | Split-Path -Parent
$DashboardDir = Join-Path $RepoRoot 'action' 'dashboard'
$Requirements = Join-Path $DashboardDir 'requirements.txt'
$AppScript = Join-Path $DashboardDir 'app.py'

Write-Host "╔══════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║     MUE Learner Dashboard Launcher       ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Check Python
$py = Get-Command python3 -ErrorAction SilentlyContinue
if (-not $py) {
    $py = Get-Command python -ErrorAction SilentlyContinue
}
if (-not $py) {
    Write-Host "❌ Python not found. Please install Python 3.9+." -ForegroundColor Red
    exit 1
}
Write-Host "✔ Using Python: $($py.Source)" -ForegroundColor Green

# Install requirements
Write-Host "`n📦 Checking dependencies..." -ForegroundColor Yellow
try {
    & $py.Source -m pip install -q -r $Requirements 2>&1 | Out-Null
    Write-Host "✔ Dependencies ready" -ForegroundColor Green
} catch {
    Write-Host "⚠ Could not install dependencies. Trying pip install..." -ForegroundColor Yellow
    & $py.Source -m pip install -r $Requirements
}

Write-Host "`n🚀 Launching dashboard..." -ForegroundColor Cyan
Write-Host "   Dashboard reads from: $RepoRoot\action\"
Write-Host "   Open in your browser when Streamlit starts."
Write-Host "   Press Ctrl+C to stop.`n" -ForegroundColor Gray

# Launch Streamlit
& $py.Source -m streamlit run $AppScript -- --repo-root "$RepoRoot"

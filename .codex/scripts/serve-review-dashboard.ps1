param(
    [int]$Port = 8080,
    [string]$HostName = "127.0.0.1",
    [switch]$NoToken
)

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
$serverArgs = @("action/dashboard/review_server.py", "--port", $Port.ToString(), "--host", $HostName)
if ($NoToken) {
    $serverArgs += "--no-token"
}

& $python.Command @($python.Prefix + $serverArgs)

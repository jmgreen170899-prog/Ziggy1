#requires -Version 5.1
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function New-DirectorySafe {
    param(
        [Parameter(Mandatory=$true)][string]$Path
    )
    if (-not (Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Path $Path -Force | Out-Null
    }
}

function Write-Log {
    param(
        [Parameter(Mandatory=$true)][string]$Message,
        [switch]$NoConsole
    )
    $ts = (Get-Date).ToString('s')
    $line = "[$ts] $Message"
    if (-not $NoConsole) { Write-Host $line }
    Add-Content -LiteralPath $Global:BlueprintLogPath -Value $line
}

function Invoke-Step {
    param(
        [Parameter(Mandatory=$true)][string]$Name,
        [Parameter(Mandatory=$true)][scriptblock]$Action
    )
    Write-Log "START: $Name"
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    & $Action
    $sw.Stop()
    Write-Log "END: $Name in $($sw.Elapsed.ToString())"
}

try {
    $Root = Resolve-Path (Join-Path $PSScriptRoot '..')
    $Docs = Join-Path $Root 'docs'
    $Raw  = Join-Path $Docs '_raw'
    $Global:BlueprintLogPath = Join-Path $Docs '_blueprint_log.md'

    New-DirectorySafe -Path $Docs
    New-DirectorySafe -Path $Raw

    # Reset log for idempotent runs
    "# Blueprint run log`n`n" | Out-File -LiteralPath $BlueprintLogPath -Encoding UTF8
    Write-Log "Blueprint orchestrator starting (root: $Root)"

    $runSw = [System.Diagnostics.Stopwatch]::StartNew()
    $startAt = (Get-Date).ToString('o')

    Invoke-Step -Name 'Scan repository' -Action { & (Join-Path $PSScriptRoot 'scan_repo.ps1') }
    Invoke-Step -Name 'Collect dependencies' -Action { & (Join-Path $PSScriptRoot 'collect_deps.ps1') }

    $backendPath = Join-Path $Root 'backend'
    if (Test-Path -LiteralPath $backendPath) {
        Invoke-Step -Name 'Export backend routes' -Action { & (Join-Path $PSScriptRoot 'export_backend_routes.ps1') }
    } else {
        Write-Log "Backend folder not found; skipping backend routes export"
    }

    $frontendPath = Join-Path $Root 'frontend'
    if (Test-Path -LiteralPath $frontendPath) {
        Invoke-Step -Name 'Export frontend routes' -Action { & (Join-Path $PSScriptRoot 'export_frontend_routes.ps1') }
    } else {
        Write-Log "Frontend folder not found; skipping frontend routes export"
    }

    Invoke-Step -Name 'Build indexes' -Action { & (Join-Path $PSScriptRoot 'build_indexes.ps1') }
    Invoke-Step -Name 'Render blueprint' -Action { & (Join-Path $PSScriptRoot 'render_blueprint.ps1') }

    $runSw.Stop()
    $endAt = (Get-Date).ToString('o')
    Write-Log "DONE in $($runSw.Elapsed.ToString()) (started: $startAt, ended: $endAt)"
}
catch {
    $err = $_
    Write-Log "ERROR: $($err.Exception.Message)" -NoConsole
    if ($err.ScriptStackTrace) { Write-Log "STACK:`n$($err.ScriptStackTrace)" -NoConsole }
    exit 1
}

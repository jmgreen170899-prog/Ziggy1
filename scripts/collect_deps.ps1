#requires -Version 5.1
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$Root = Resolve-Path (Join-Path $PSScriptRoot '..')
$Docs = Join-Path $Root 'docs'
$Raw  = Join-Path $Docs '_raw'
if (-not (Test-Path $Raw)) { New-Item -ItemType Directory -Path $Raw -Force | Out-Null }

$pipOut = Join-Path $Raw '_pip_deps.txt'
$npmOut = Join-Path $Raw '_npm_deps.txt'

"Collecting dependency information..." | Out-File -LiteralPath $pipOut -Encoding UTF8
"Collecting dependency information..." | Out-File -LiteralPath $npmOut -Encoding UTF8

# Python deps
$pythonExists = (Get-Command python -ErrorAction SilentlyContinue) -ne $null
if ($pythonExists) {
    $reqFile = Get-ChildItem -Path $Root -Recurse -File -Include 'requirements.txt','pyproject.toml' -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($reqFile) {
        $pipdeptree = Get-Command pipdeptree -ErrorAction SilentlyContinue
        if ($pipdeptree) {
            try { & pipdeptree | Out-File -LiteralPath $pipOut -Encoding UTF8 } catch { Add-Content -LiteralPath $pipOut -Value "pipdeptree execution failed: $($_.Exception.Message)" }
        } else {
            Add-Content -LiteralPath $pipOut -Value 'pipdeptree not available'
        }
    } else { Add-Content -LiteralPath $pipOut -Value 'No requirements/pyproject found' }
} else { Add-Content -LiteralPath $pipOut -Value 'Python not available' }

# Node deps
$nodeExists = (Get-Command node -ErrorAction SilentlyContinue) -ne $null
if ($nodeExists) {
    $pkgJson = Get-ChildItem -Path $Root -Recurse -File -Include 'package.json' -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($pkgJson) {
        try { & npm ls --all 2>&1 | Out-File -LiteralPath $npmOut -Encoding UTF8 } catch { Add-Content -LiteralPath $npmOut -Value "npm ls failed: $($_.Exception.Message)" }
    } else { Add-Content -LiteralPath $npmOut -Value 'No package.json found' }
} else { Add-Content -LiteralPath $npmOut -Value 'Node not available' }

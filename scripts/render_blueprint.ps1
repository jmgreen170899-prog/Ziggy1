#requires -Version 5.1
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$Root = Resolve-Path (Join-Path $PSScriptRoot '..')
$Docs = Join-Path $Root 'docs'

function Read-Json($path) { if (Test-Path $path) { try { Get-Content -LiteralPath $path -Raw -Encoding UTF8 | ConvertFrom-Json -ErrorAction Stop } catch { $null } } else { $null } }

$indexPath = Join-Path $Docs 'blueprint_index.json'
$apiPath   = Join-Path $Docs 'api_catalog.json'
$compPath  = Join-Path $Docs 'component_map.json'
$envPath   = Join-Path $Docs 'env_catalog.json'
$manifestPath = Join-Path $Docs '_scan_manifest.json'

$index = Read-Json $indexPath
$api   = Read-Json $apiPath
$comp  = Read-Json $compPath
$env   = Read-Json $envPath
$manifest = Read-Json $manifestPath

if ($null -eq $index) { throw "Missing $indexPath. Run build_indexes.ps1 first." }

$mdPath = Join-Path $Docs 'PROJECT_BLUEPRINT.md'
$changelogPath = Join-Path $Docs 'BLUEPRINT_CHANGELOG.md'
$datasetPath = Join-Path $Docs 'BLUEPRINT_DATASET.md'

function Link-File([string]$rel) { return "`[$rel:1–1]`" }

function Section-Header([string]$title) { return "## $title`n" }

$lines = New-Object System.Collections.Generic.List[string]
$lines.Add('# Project Blueprint') | Out-Null
$lines.Add('') | Out-Null
$lines.Add("Generated: $((Get-Date).ToString('u'))") | Out-Null
if ($manifest) { $lines.Add("Scan window: $($manifest.started_at) → $($manifest.finished_at)") | Out-Null }
$lines.Add('') | Out-Null
$lines.Add('## Table of Contents') | Out-Null
$toc = @(
  '- [Executive Snapshot](#executive-snapshot)'
  '- [Repo Overview & File Map](#repo-overview--file-map)'
  '- [Backend Architecture](#backend-architecture)'
  '- [API Catalog](#api-catalog)'
  '- [Frontend Architecture](#frontend-architecture)'
  '- [Data & Storage](#data--storage)'
  '- [Integrations](#integrations)'
  '- [Config & Env](#config--env)'
  '- [Security](#security)'
  '- [Logging & Telemetry](#logging--telemetry)'
  '- [Dev Setup & Runbooks](#dev-setup--runbooks)'
  '- [Testing & Quality Gates](#testing--quality-gates)'
  '- [Performance & SLOs](#performance--slos)'
  '- [CI/CD & Environments](#cicd--environments)'
  '- [UX Flows & Domain Glossary](#ux-flows--domain-glossary)'
  '- [Known Issues & TODOs](#known-issues--todos)'
  '- [Change-Safety Recipes](#change-safety-recipes)'
  '- [Gaps & Requests](#gaps--requests)'
)
$lines.AddRange($toc) | Out-Null
$lines.Add('') | Out-Null

# Executive Snapshot
$lines.Add(Section-Header 'Executive Snapshot') | Out-Null
$fw = @()
if ($index.key_manifests.'package.json') { $fw += "Node (package.json) " + (Link-File 'package.json') }
if ($index.key_manifests.'pyproject.toml' -or $index.key_manifests.'requirements.txt') { $fw += "Python (pyproject/requirements) " + (Link-File ('backend/pyproject.toml')) }
if (Test-Path (Join-Path $Root 'docker-compose.yml')) { $fw += "Docker compose present " + (Link-File 'docker-compose.yml') }
if ($fw.Count -eq 0) { $fw = @('N/A') }
$lines.Add("- Frameworks: $($fw -join '; ') ") | Out-Null
$portSumm = if ($index.ports -and $index.ports.Count -gt 0) { ($index.ports | ForEach-Object { "$($_.host)->$($_.container) [docker-compose.yml:1–1]" }) -join ', ' } else { 'N/A' }
$lines.Add("- Dev ports: $portSumm") | Out-Null
$lines.Add('') | Out-Null

# Repo Overview & File Map
$lines.Add(Section-Header 'Repo Overview & File Map') | Out-Null
$totalFiles = ($index.files | Measure-Object).Count
$lines.Add("- Files scanned: $totalFiles (see docs/_raw/_files.txt [docs/_raw/_files.txt:1–1])") | Out-Null
$lines.Add("- Top-level directories: " + (($index.directories.GetEnumerator() | Sort-Object Name | ForEach-Object { "`$($_.Name)`= $($_.Value)" }) -join ', ')) | Out-Null
$lines.Add("- Tree (filtered): see docs/_raw/_tree.txt [docs/_raw/_tree.txt:1–1]") | Out-Null
$lines.Add('') | Out-Null

# Backend Architecture
$lines.Add(Section-Header 'Backend Architecture') | Out-Null
if ($api -and $api.routes.Count -gt 0) {
    $beSample = $api.routes | Select-Object -First 5
    $lines.Add("- Routes discovered: $($api.routes.Count) (see docs/_raw/_routes_backend.json [docs/_raw/_routes_backend.json:1–1])") | Out-Null
    foreach ($r in $beSample) {
        $cite = if ($r.file) { "[`$($r.file):$($r.line)–$($r.line)]" } else { '[docs/_raw/_routes_backend.json:1–1]' }
        $lines.Add("  - $($r.method) $($r.path) → $($r.handler) $cite") | Out-Null
    }
} else {
    $lines.Add('- No backend routes detected [docs/_raw/_routes_backend.json:1–1]') | Out-Null
}
$lines.Add('') | Out-Null

# API Catalog
$lines.Add(Section-Header 'API Catalog') | Out-Null
if ($api -and $api.routes.Count -gt 0) {
    foreach ($grp in ($api.routes | Group-Object path)) {
        foreach ($r in $grp.Group) {
            $cite = if ($r.file) { "[`$($r.file):$($r.line)–$($r.line)]" } else { '[docs/_raw/_routes_backend.json:1–1]' }
            $lines.Add("- $($r.method) $($r.path) → $($r.handler) $cite") | Out-Null
        }
    }
} else { $lines.Add('- N/A') | Out-Null }
$lines.Add('') | Out-Null

# Frontend Architecture
$lines.Add(Section-Header 'Frontend Architecture') | Out-Null
if ($comp -and $comp.routes.Count -gt 0) {
    $lines.Add("- Routes discovered: $($comp.routes.Count) (see docs/_raw/_routes_frontend.json [docs/_raw/_routes_frontend.json:1–1])") | Out-Null
    foreach ($r in ($comp.routes | Select-Object -First 10)) {
        $lines.Add("  - $($r.path) → $($r.component) [`$($r.file):1–1]") | Out-Null
    }
} else { $lines.Add('- No frontend routes detected [docs/_raw/_routes_frontend.json:1–1]') | Out-Null }

$lines.Add('') | Out-Null
# Data & Storage (best-effort: look for sqlite, postgres, redis mentions)
$lines.Add(Section-Header 'Data & Storage') | Out-Null
$dataHints = @()
foreach ($fi in $index.files) {
    if ($fi.is_code -and ($fi.ext -in @('.py','.ts','.tsx','.js','.json','.yml','.yaml'))) {
        $abs = Join-Path $Root $fi.path
        try {
            $t = Get-Content -LiteralPath $abs -Raw -Encoding UTF8
            if ($t -match '(?i)sqlite|postgres|redis|mongodb|duckdb|s3://') { $dataHints += $fi.path }
        } catch {}
    }
}
if ($dataHints.Count -gt 0) { $lines.Add("- Evidence files: " + (($dataHints | Select-Object -Unique | Select-Object -First 10 | ForEach-Object { "`[$_`:1–1]" }) -join ', ')) | Out-Null } else { $lines.Add('- N/A') | Out-Null }
$lines.Add('') | Out-Null

# Integrations (keywords)
$lines.Add(Section-Header 'Integrations') | Out-Null
$integrations = @('IBKR','Interactive Brokers','Telegram','News','Alpaca','OpenAI','Anthropic','Slack','Discord','Twilio')
$intHits = @()
foreach ($fi in $index.files) {
    if ($fi.is_code) {
        $abs = Join-Path $Root $fi.path
        try {
            $t = Get-Content -LiteralPath $abs -Raw -Encoding UTF8
            foreach ($k in $integrations) { if ($t -match [regex]::Escape($k)) { $intHits += $fi.path; break } }
        } catch {}
    }
}
if ($intHits.Count -gt 0) { $lines.Add("- Evidence files: " + (($intHits | Select-Object -Unique | Select-Object -First 10 | ForEach-Object { "`[$_`:1–1]" }) -join ', ')) | Out-Null } else { $lines.Add('- N/A') | Out-Null }
$lines.Add('') | Out-Null

# Config & Env
$lines.Add(Section-Header 'Config & Env') | Out-Null
if ($env -and $env.vars.Count -gt 0) {
    $lines.Add("- Env vars discovered: $($env.vars.Count) (no values shown). Examples:") | Out-Null
    foreach ($v in ($env.vars | Select-Object -First 10)) {
        $ref = if ($v.referenced_in -and $v.referenced_in.Count -gt 0) { "[`$($v.referenced_in[0])`:1–1]" } else { '' }
        $lines.Add("  - $($v.name) $ref") | Out-Null
    }
} else { $lines.Add('- N/A') | Out-Null }
$lines.Add('') | Out-Null

# Security
$lines.Add(Section-Header 'Security') | Out-Null
$lines.Add('- evidence-based review of auth/authz, cors/csrf not detected automatically; see config files and middleware for details.') | Out-Null
$lines.Add('') | Out-Null

# Logging & Telemetry
$lines.Add(Section-Header 'Logging & Telemetry') | Out-Null
$logHits = @()
foreach ($fi in $index.files) {
    if ($fi.is_code) {
        $abs = Join-Path $Root $fi.path
        try { $t = Get-Content -LiteralPath $abs -Raw -Encoding UTF8; if ($t -match '(?i)logging|loguru|winston|pino|telemetry|opentelemetry') { $logHits += $fi.path } } catch {}
    }
}
if ($logHits.Count -gt 0) { $lines.Add("- Evidence files: " + (($logHits | Select-Object -Unique | Select-Object -First 10 | ForEach-Object { "`[$_`:1–1]" }) -join ', ')) | Out-Null } else { $lines.Add('- N/A') | Out-Null }
$lines.Add('') | Out-Null

# Dev Setup & Runbooks
$lines.Add(Section-Header 'Dev Setup & Runbooks') | Out-Null
if ($index.scripts) {
    foreach ($scope in $index.scripts.PSObject.Properties.Name) {
        $lines.Add("- npm scripts $scope: " + (($index.scripts.$scope.PSObject.Properties | ForEach-Object { $_.Name }) -join ', ') + ' [package.json:1–1]') | Out-Null
    }
} else { $lines.Add('- N/A') | Out-Null }
$lines.Add('') | Out-Null

# Testing & Quality Gates
$lines.Add(Section-Header 'Testing & Quality Gates') | Out-Null
$testHits = @()
foreach ($fi in $index.files) { if ($fi.path -match '(?i)\btest_|\.spec\.|\.test\.') { $testHits += $fi.path } }
if ($testHits.Count -gt 0) { $lines.Add("- Test files: " + (($testHits | Select-Object -Unique | Select-Object -First 20 | ForEach-Object { "`[$_`:1–1]" }) -join ', ')) | Out-Null } else { $lines.Add('- N/A') | Out-Null }
$lines.Add('') | Out-Null

# Performance & SLOs / CI/CD / UX / Known Issues / Recipes / Gaps
$lines.Add(Section-Header 'Performance & SLOs') | Out-Null
$lines.Add('- N/A') | Out-Null
$lines.Add('') | Out-Null

$lines.Add(Section-Header 'CI/CD & Environments') | Out-Null
if (Test-Path (Join-Path $Root '.github')) { $lines.Add('- GitHub workflows present [.github:1–1]') | Out-Null } else { $lines.Add('- N/A') | Out-Null }
$lines.Add('') | Out-Null

$lines.Add(Section-Header 'UX Flows & Domain Glossary') | Out-Null
$lines.Add('- N/A') | Out-Null
$lines.Add('') | Out-Null

$lines.Add(Section-Header 'Known Issues & TODOs') | Out-Null
$todoHits = @()
foreach ($fi in $index.files) { if ($fi.is_code) { try { $t = Get-Content -LiteralPath (Join-Path $Root $fi.path) -Raw -Encoding UTF8; if ($t -match '(?i)TODO|FIXME') { $todoHits += $fi.path } } catch {} } }
if ($todoHits.Count -gt 0) { $lines.Add("- Found TODO/FIXME in: " + (($todoHits | Select-Object -Unique | Select-Object -First 20 | ForEach-Object { "`[$_`:1–1]" }) -join ', ')) | Out-Null } else { $lines.Add('- none detected') | Out-Null }
$lines.Add('') | Out-Null

$lines.Add(Section-Header 'Change-Safety Recipes') | Out-Null
$lines.Add('- add backend endpoint: create router function and include in app; add unit test; update openapi; verify route appears in docs/_raw/_routes_backend.json [docs/_raw/_routes_backend.json:1–1]') | Out-Null
$lines.Add('- add frontend route: create page under src/app or src/pages; ensure component is exported; verify docs/_raw/_routes_frontend.json updated [docs/_raw/_routes_frontend.json:1–1]') | Out-Null
$lines.Add('') | Out-Null

$lines.Add(Section-Header 'Gaps & Requests') | Out-Null
$lines.Add('- provide CI pipeline definition to document build/test deploy steps') | Out-Null
$lines.Add('- provide database schema or migrations for data storage section') | Out-Null
$lines.Add('') | Out-Null

$lines | Out-File -LiteralPath $mdPath -Encoding UTF8

# Changelog (diffs)
$now = Get-Date
$prevStamp = $null
$prevIndex = $null
if (Test-Path $changelogPath) {
    # best-effort: no need to parse previous json snapshot; we'll compare with current index only
}

# To detect changes across runs, compare with a previous snapshot file if available
$snapPath = Join-Path $Docs '_last_index_snapshot.json'
if (Test-Path $snapPath) { $prevIndex = Read-Json $snapPath }

$changes = @()
if ($prevIndex) {
    $prevFiles = @($prevIndex.files | ForEach-Object { $_.path })
    $currFiles = @($index.files | ForEach-Object { $_.path })
    $added = Compare-Object -ReferenceObject $prevFiles -DifferenceObject $currFiles -PassThru | Where-Object { $_ -and $_ -in $currFiles }
    $removed = Compare-Object -ReferenceObject $prevFiles -DifferenceObject $currFiles -PassThru | Where-Object { $_ -and $_ -in $prevFiles }
    if ($added.Count -gt 0) { $changes += "files added: $($added.Count)" }
    if ($removed.Count -gt 0) { $changes += "files removed: $($removed.Count)" }
}

# Routes diffs
$prevApi = $null
if ($prevIndex) { $prevApi = Read-Json (Join-Path $Docs '_last_api_snapshot.json') }
$apiAdded = 0; $apiRemoved = 0
if ($prevApi) {
    $mkKey = { param($r) "$($r.method) $($r.path)" }
    $prevKeys = @($prevApi.routes | ForEach-Object { & $mkKey $_ })
    $currKeys = @($api.routes | ForEach-Object { & $mkKey $_ })
    $apiAdded = (@(Compare-Object $prevKeys $currKeys -PassThru | Where-Object { $_ -in $currKeys })).Count
    $apiRemoved = (@(Compare-Object $prevKeys $currKeys -PassThru | Where-Object { $_ -in $prevKeys })).Count
}
if ($apiAdded -gt 0) { $changes += "api routes added: $apiAdded" }
if ($apiRemoved -gt 0) { $changes += "api routes removed: $apiRemoved" }

$chgLines = @()
$chgLines += "# Blueprint Changelog"
$chgLines += ""
if (Test-Path $changelogPath) { $chgLines = Get-Content -LiteralPath $changelogPath -Encoding UTF8 }
$chgLines += "## Run $($now.ToString('u'))"
$chgLines += "- files scanned: $($index.files.Count)"
if ($changes.Count -gt 0) { foreach ($c in $changes) { $chgLines += "- $c" } } else { $chgLines += "- no structural changes detected" }
Set-Content -LiteralPath $changelogPath -Encoding UTF8 -Value $chgLines

# Persist current snapshots for next run diff
$index | ConvertTo-Json -Depth 8 | Out-File -LiteralPath $snapPath -Encoding UTF8
$api   | ConvertTo-Json -Depth 6 | Out-File -LiteralPath (Join-Path $Docs '_last_api_snapshot.json') -Encoding UTF8

# Dataset: machine context in lowercase minimal punctuation
$ds = New-Object System.Collections.Generic.List[string]
$ds.Add('project blueprint dataset') | Out-Null
$ds.Add("generated $((Get-Date).ToString('s'))") | Out-Null
$ds.Add("files $($index.files.Count)") | Out-Null
if ($api -and $api.routes) { $ds.Add("backend routes $($api.routes.Count)") | Out-Null } else { $ds.Add('backend routes 0') | Out-Null }
if ($comp -and $comp.routes) { $ds.Add("frontend routes $($comp.routes.Count)") | Out-Null } else { $ds.Add('frontend routes 0') | Out-Null }
if ($env -and $env.vars) { $ds.Add("env vars $($env.vars.Count)") | Out-Null } else { $ds.Add('env vars 0') | Out-Null }
$ds.Add('key manifests present ' + (($index.key_manifests.PSObject.Properties | Where-Object { $_.Value } | ForEach-Object { $_.Name }) -join ' ')) | Out-Null
Set-Content -LiteralPath $datasetPath -Encoding UTF8 -Value ($ds | ForEach-Object { $_.ToLowerInvariant() })

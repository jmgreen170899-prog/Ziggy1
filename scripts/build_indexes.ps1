#requires -Version 5.1
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$Root = Resolve-Path (Join-Path $PSScriptRoot '..')
$Docs = Join-Path $Root 'docs'
$Raw  = Join-Path $Docs '_raw'
if (-not (Test-Path $Raw)) { New-Item -ItemType Directory -Path $Raw -Force | Out-Null }

function Read-Json($path) {
    if (-not (Test-Path $path)) { return $null }
    try { Get-Content -LiteralPath $path -Raw -Encoding UTF8 | ConvertFrom-Json -ErrorAction Stop } catch { $null }
}

$filesTxt  = Join-Path $Raw '_files.txt'
$sizesJson = Join-Path $Raw '_sizes.json'
$manifest  = Join-Path $Docs '_scan_manifest.json'
$beRoutes  = Join-Path $Raw '_routes_backend.json'
$feRoutes  = Join-Path $Raw '_routes_frontend.json'

$files = @()
if (Test-Path $filesTxt) { $files = Get-Content -LiteralPath $filesTxt -Encoding UTF8 }
$sizes = Read-Json $sizesJson
$manifestObj = Read-Json $manifest
$be = Read-Json $beRoutes
$fe = Read-Json $feRoutes
if ($null -eq $be) { $be = @{ routes = @() } }
if ($null -eq $fe) { $fe = @{ routes = @() } }

# Build blueprint_index.json
function Get-Ext([string]$f){ $e = [IO.Path]::GetExtension($f); if ([string]::IsNullOrEmpty($e)) { 'none' } else { $e.ToLowerInvariant() } }
function Is-Code([string]$f){ return $f -match '\.(ts|tsx|js|jsx|py|json|yml|yaml|toml|md|ps1|sh|bat|html|css)$' }

$fileEntries = foreach ($f in $files) {
    [pscustomobject]@{
        path = $f
        size_bytes = if ($sizes) { $sizes.$f } else { $null }
        ext = Get-Ext $f
        is_code = (Is-Code $f)
        directory = [IO.Path]::GetDirectoryName($f) -replace '\\','/'
    }
}

# Directory counts (top-level)
$topCounts = @{}
foreach ($fi in $fileEntries) {
    $top = ($fi.path -split '/')[0]
    if (-not $topCounts.ContainsKey($top)) { $topCounts[$top] = 0 }
    $topCounts[$top]++
}

# Key manifests
$keyManifests = @{}
foreach ($k in @('package.json','pyproject.toml','requirements.txt','docker-compose.yml','Makefile','README.md','pytest.ini','tsconfig.json','next.config.ts','vite.config.ts','.env','.env.local','.env.development','.env.production')) {
    $p = Join-Path $Root $k
    $keyManifests[$k] = (Test-Path -LiteralPath $p)
}

# Parse package.json scripts if present (root and frontend)
function Read-Package-Scripts($dir) {
    $pkg = Join-Path $dir 'package.json'
    if (-not (Test-Path $pkg)) { return $null }
    try { (Get-Content -LiteralPath $pkg -Raw -Encoding UTF8 | ConvertFrom-Json).scripts } catch { $null }
}
$pkgScripts = @{}
$pkgRoot = Read-Package-Scripts $Root
if ($pkgRoot) { $pkgScripts['/'] = $pkgRoot }
$feDir = Join-Path $Root 'frontend'
if (Test-Path $feDir) {
    $pkgFe = Read-Package-Scripts $feDir
    if ($pkgFe) { $pkgScripts['/frontend'] = $pkgFe }
}

# Heuristic ports (from docker-compose and known config)
$ports = @()
$dc = Join-Path $Root 'docker-compose.yml'
if (Test-Path $dc) {
    $txt = Get-Content -LiteralPath $dc -Raw -Encoding UTF8
    $m = [regex]::Matches($txt, '(?im)^\s*-\s*"?(\d+):(\d+)')
    foreach ($mm in $m) { $ports += [pscustomobject]@{ host=$mm.Groups[1].Value; container=$mm.Groups[2].Value; source='docker-compose.yml' } }
}

$index = [ordered]@{
    generated_at = (Get-Date).ToString('o')
    manifest     = $manifestObj
    files        = $fileEntries
    directories  = $topCounts
    key_manifests = $keyManifests
    scripts      = $pkgScripts
    ports        = $ports
}

$indexPath = Join-Path $Docs 'blueprint_index.json'
$index | ConvertTo-Json -Depth 8 | Out-File -LiteralPath $indexPath -Encoding UTF8

# API catalog
$apiCatalog = [ordered]@{
    generated_at = (Get-Date).ToString('o')
    routes = @()
}
foreach ($r in $be.routes) {
    foreach ($m in ($r.methods | ForEach-Object { $_ })) {
        $apiCatalog.routes += [pscustomobject]@{
            method = $m
            path   = $r.path
            handler = $r.handler
            file    = $r.file
            line    = $r.line
        }
    }
}
$apiPath = Join-Path $Docs 'api_catalog.json'
$apiCatalog | ConvertTo-Json -Depth 6 | Out-File -LiteralPath $apiPath -Encoding UTF8

# Component map
$componentMap = [ordered]@{
    generated_at = (Get-Date).ToString('o')
    routes = $fe.routes
    components = @()
}
# Best-effort: list src/components files if present
$compDir = Join-Path $Root 'frontend/src/components'
if (Test-Path $compDir) {
    $compFiles = Get-ChildItem -Path $compDir -Recurse -File -Include *.tsx,*.ts,*.jsx,*.js -ErrorAction SilentlyContinue
    foreach ($cf in $compFiles) {
        $componentMap.components += [pscustomobject]@{
            name = [IO.Path]::GetFileNameWithoutExtension($cf.Name)
            file = ($cf.FullName.Replace($Root, '') -replace '^\\','') -replace '\\','/'
        }
    }
}
$compPath = Join-Path $Docs 'component_map.json'
$componentMap | ConvertTo-Json -Depth 6 | Out-File -LiteralPath $compPath -Encoding UTF8

# Env catalog (scan patterns; never values)
$envNames = New-Object System.Collections.Generic.HashSet[string]
$envRefs = @()
$codeFiles = $fileEntries | Where-Object { $_.is_code -and $_.ext -ne '.json' }
foreach ($fi in $codeFiles) {
    $abs = Join-Path $Root $fi.path
    try { $text = Get-Content -LiteralPath $abs -Raw -Encoding UTF8 } catch { continue }
    # Python env
    $rx1 = [regex]'os\.getenv\(\s*[\"\'']([A-Za-z_][A-Za-z0-9_]*)[\"\'']'
    $rx2 = [regex]'os\.environ\[\s*[\"\'']([A-Za-z_][A-Za-z0-9_]*)[\"\'']\s*\]'
    foreach ($m in $rx1.Matches($text)) { [void]$envNames.Add($m.Groups[1].Value); $envRefs += [pscustomobject]@{ name=$m.Groups[1].Value; file=$fi.path } }
    foreach ($m in $rx2.Matches($text)) { [void]$envNames.Add($m.Groups[1].Value); $envRefs += [pscustomobject]@{ name=$m.Groups[1].Value; file=$fi.path } }
    # JS env
    $rx3 = [regex]'process\.env\.([A-Za-z_][A-Za-z0-9_]*)'
    foreach ($m in $rx3.Matches($text)) { [void]$envNames.Add($m.Groups[1].Value); $envRefs += [pscustomobject]@{ name=$m.Groups[1].Value; file=$fi.path } }
}

# Defaults from .env* (names only; redact values)
$envFiles = Get-ChildItem -Path $Root -Recurse -File -Include '.env','.env.*' -ErrorAction SilentlyContinue
$envDefaults = @{}
foreach ($ef in $envFiles) {
    try {
        foreach ($line in Get-Content -LiteralPath $ef.FullName -Encoding UTF8) {
            if ($line -match '^[A-Za-z_][A-Za-z0-9_]*=') {
                $name = $line.Split('=')[0]
                if (-not $envDefaults.ContainsKey($name)) { $envDefaults[$name] = @{ default = '<redacted>'; source = ($ef.FullName.Replace($Root,'') -replace '^\\','') -replace '\\','/' } }
                [void]$envNames.Add($name)
            }
        }
    } catch {}
}

$envCatalog = [ordered]@{
    generated_at = (Get-Date).ToString('o')
    vars = @()
}
foreach ($name in ($envNames | Sort-Object)) {
    $refs = $envRefs | Where-Object { $_.name -eq $name } | Select-Object -ExpandProperty file -Unique
    $def  = if ($envDefaults.ContainsKey($name)) { $envDefaults[$name] } else { $null }
    $envCatalog.vars += [pscustomobject]@{ name=$name; referenced_in=$refs; default=$def?.default; default_source=$def?.source }
}
$envPath = Join-Path $Docs 'env_catalog.json'
$envCatalog | ConvertTo-Json -Depth 6 | Out-File -LiteralPath $envPath -Encoding UTF8

# Unnecessary files catalog
$csvPath = Join-Path $Docs 'unnecessary_files.csv'
$rows = New-Object System.Collections.Generic.List[object]

function Add-Row([string]$p, [long]$size, [string]$reason) {
    $rows.Add([pscustomobject]@{ path=$p; size_bytes=$size; reason=$reason }) | Out-Null
}

$sizeLimit = 20MB

# 1) Large binaries from scanned files
foreach ($fi in $fileEntries) {
    $sz = [int64]$fi.size_bytes
    if ($sz -ge $sizeLimit) { Add-Row $fi.path $sz 'large_binary(>20MB)' }
}

# 2) Pattern-based directories (scan fresh but shallow to avoid cost)
$patterns = @(
    @{ dir='dist'; reason='build_artifact' },
    @{ dir='build'; reason='build_artifact' },
    @{ dir='coverage'; reason='build_artifact' },
    @{ dir='.next'; reason='build_artifact' },
    @{ dir='.turbo'; reason='build_artifact' },
    @{ dir='.parcel-cache'; reason='cache' },
    @{ dir='target'; reason='build_artifact' },
    @{ dir='bin'; reason='build_artifact' },
    @{ dir='obj'; reason='build_artifact' },
    @{ dir='__pycache__'; reason='cache' },
    @{ dir='.pytest_cache'; reason='cache' },
    @{ dir='.mypy_cache'; reason='cache' },
    @{ dir='.cache'; reason='cache' },
    @{ dir='vendor'; reason='vendor_bundle' },
    @{ dir='backup'; reason='backup/temp' },
    @{ dir='__purge_backups'; reason='backup/temp' }
)

foreach ($pat in $patterns) {
    $hits = Get-ChildItem -Path $Root -Recurse -Directory -Filter $($pat.dir) -ErrorAction SilentlyContinue
    foreach ($hit in $hits) {
        $filesIn = Get-ChildItem -Path $hit.FullName -Recurse -File -ErrorAction SilentlyContinue
        foreach ($f in $filesIn) {
            $rel = ($f.FullName.Replace($Root,'') -replace '^\\','') -replace '\\','/'
            Add-Row $rel $f.Length $pat.reason
        }
    }
}

# 3) Lockfiles, logs, archives, temp
$fileGlobs = @(
    @{ glob='*.lock'; reason='lockfile' },
    @{ glob='*.log'; reason='log' },
    @{ glob='*.zip'; reason='archive' },
    @{ glob='*.7z'; reason='archive' },
    @{ glob='*.tar.gz'; reason='archive' },
    @{ glob='*.bak'; reason='backup/temp' },
    @{ glob='*.tmp'; reason='backup/temp' },
    @{ glob='~$*'; reason='backup/temp' },
    @{ glob='*.old'; reason='backup/temp' }
)
foreach ($g in $fileGlobs) {
    $hits = Get-ChildItem -Path $Root -Recurse -File -Include $g.glob -ErrorAction SilentlyContinue
    foreach ($f in $hits) {
        $rel = ($f.FullName.Replace($Root,'') -replace '^\\','') -replace '\\','/'
        Add-Row $rel $f.Length $g.reason
    }
}

# 4) Unreferenced assets (best-effort)
$assetExt = '\\.(png|jpe?g|gif|svg|webp|mp4|mp3|wav|webm|ico)$'
$assetFiles = $fileEntries | Where-Object { $_.path -match $assetExt }
$codeText = ""
foreach ($fi in ($fileEntries | Where-Object { $_.is_code })) {
    $abs = Join-Path $Root $fi.path
    try { $codeText += (Get-Content -LiteralPath $abs -Raw -Encoding UTF8) } catch {}
}
foreach ($af in $assetFiles) {
    $name = [IO.Path]::GetFileName($af.path)
    if ($codeText -notmatch [regex]::Escape($name)) {
        Add-Row $af.path ([int64]$af.size_bytes) 'unreferenced_asset'
    }
}

# 5) IDE/editor configs (keep optional)
$ide = Get-ChildItem -Path $Root -Recurse -Force -ErrorAction SilentlyContinue -Include '.idea','*.code-workspace','.vscode'
foreach ($d in $ide) {
    if ($d.PSIsContainer) {
        $filesIn = Get-ChildItem -Path $d.FullName -Recurse -File -ErrorAction SilentlyContinue
        foreach ($f in $filesIn) { $rel = ($f.FullName.Replace($Root,'' ) -replace '^\\','') -replace '\\','/'; Add-Row $rel $f.Length 'editor_config' }
    } else {
        $rel = ($d.FullName.Replace($Root,'' ) -replace '^\\','') -replace '\\','/'
        Add-Row $rel ($d.Length) 'editor_config'
    }
}

# De-duplicate rows (path + reason)
$rows = $rows | Sort-Object path, reason -Unique
$rows | Export-Csv -LiteralPath $csvPath -NoTypeInformation -Encoding UTF8

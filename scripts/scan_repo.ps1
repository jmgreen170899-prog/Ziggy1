#requires -Version 5.1
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$Root = Resolve-Path (Join-Path $PSScriptRoot '..')
$Docs = Join-Path $Root 'docs'
$Raw  = Join-Path $Docs '_raw'

function New-DirectorySafe([string]$Path) { if (-not (Test-Path -LiteralPath $Path)) { New-Item -ItemType Directory -Path $Path -Force | Out-Null } }
New-DirectorySafe $Docs
New-DirectorySafe $Raw

function Get-RelativePath([string]$Base, [string]$Path) {
    $baseNorm = [IO.Path]::GetFullPath($Base)
    $pathNorm = [IO.Path]::GetFullPath($Path)
    if ($pathNorm.StartsWith($baseNorm, [StringComparison]::OrdinalIgnoreCase)) {
        $rel = $pathNorm.Substring($baseNorm.Length).TrimStart('\','/')
        return $rel -replace '\\','/'
    }
    return $Path
}

$excludeDirs = @(
    'node_modules','dist','build','coverage','.pytest_cache','__pycache__','.mypy_cache','.next','.turbo','.parcel-cache','.cache','.git','.idea','.gradle','target','bin','obj','vendor','backup','__purge_backups','venv','.venv','env'
)
$excludeFileGlobs = @('*.lock','*.min.*')

function Test-Excluded([IO.FileSystemInfo]$fsi) {
    # skip reparse points (symlinks)
    if (($fsi.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { return $true }
    foreach ($seg in $excludeDirs) {
        if ($fsi.FullName -match "(?i)(^|\\|/)${seg}(\\|/)") { return $true }
    }
    foreach ($pat in $excludeFileGlobs) {
        if ($fsi.PSIsContainer) { continue }
        if ($fsi.Name -like $pat) { return $true }
    }
    return $false
}

$started = Get-Date
$files = New-Object System.Collections.Generic.List[object]
$sizesMap = @{}

function Scan-Dir([string]$dir) {
    $items = Get-ChildItem -LiteralPath $dir -Force -ErrorAction SilentlyContinue
    foreach ($it in $items) {
        if (Test-Excluded $it) { continue }
        if ($it.PSIsContainer) {
            Scan-Dir $it.FullName
        } else {
            $rel = Get-RelativePath $Root $it.FullName
            $files.Add($rel) | Out-Null
            $sizesMap[$rel] = $it.Length
        }
    }
}

Scan-Dir $Root

$filesPath = Join-Path $Raw '_files.txt'
$files | Sort-Object | Out-File -LiteralPath $filesPath -Encoding UTF8

# Tree (depth-limited to 10)
$treePath = Join-Path $Raw '_tree.txt'

function Write-Tree([string]$dir, [int]$depth=0, [string]$prefix='') {
    if ($depth -ge 10) { return }
    $children = @(Get-ChildItem -LiteralPath $dir -Force -ErrorAction SilentlyContinue | Where-Object { -not (Test-Excluded $_) } | Sort-Object PSIsContainer, Name)
    $count = $children.Length
    $i = 0
    foreach ($child in $children) {
        $i++
        $isLast = ($i -eq $count)
        if ($isLast) { $branch = '`-- ' } else { $branch = '|-- ' }
        $line = "$prefix$branch$($child.Name)"
        Add-Content -LiteralPath $treePath -Value $line
        if ($child.PSIsContainer) {
            if ($isLast) { $newPrefix = $prefix + '    ' } else { $newPrefix = $prefix + '|   ' }
            Write-Tree -dir $child.FullName -depth ($depth+1) -prefix $newPrefix
        }
    }
}

"$([IO.Path]::GetFileName($Root))" | Out-File -LiteralPath $treePath -Encoding UTF8
Write-Tree -dir $Root -depth 0 -prefix ''

# Manifest
$psVersion = $PSVersionTable.PSVersion.ToString()

function Try-Get-Cmd([string]$cmd, [string]$args) {
    $c = Get-Command $cmd -ErrorAction SilentlyContinue
    if ($null -eq $c) { return $null }
    try { & $cmd $args 2>$null } catch { return $null }
}

$nodeVer = Try-Get-Cmd 'node' '--version'
if ($nodeVer) { $nodeVer = ($nodeVer | Select-Object -First 1).Trim() }
else { $nodeVer = 'N/A' }

$pyVer = Try-Get-Cmd 'python' '--version'
if ($pyVer) { $pyVer = ($pyVer | Select-Object -First 1).Trim() }
else { $pyVer = 'N/A' }

$gitHead = 'N/A'
if (Test-Path (Join-Path $Root '.git')) {
    $gitCmd = Get-Command git -ErrorAction SilentlyContinue
    if ($gitCmd) {
        try { $gitHead = (& git -C $Root rev-parse --short HEAD 2>$null).Trim() } catch { $gitHead = 'N/A' }
    }
}

$extCounts = @{}
foreach ($f in $files) {
    $ext = [IO.Path]::GetExtension($f)
    if ([string]::IsNullOrEmpty($ext)) { $ext = 'none' } else { $ext = $ext.ToLowerInvariant() }
    if (-not $extCounts.ContainsKey($ext)) { $extCounts[$ext] = 0 }
    $extCounts[$ext]++
}

$finished = Get-Date
$manifest = [ordered]@{
    started_at  = $started.ToString('o')
    finished_at = $finished.ToString('o')
    repo_root   = [IO.Path]::GetFullPath($Root)
    tool_versions = @{ powershell = $psVersion; node = $nodeVer; python = $pyVer }
    git_head    = $gitHead
    file_counts = $extCounts
}

$manifestPath = Join-Path $Docs '_scan_manifest.json'
$manifest | ConvertTo-Json -Depth 10 | Out-File -LiteralPath $manifestPath -Encoding UTF8

# Stash sizes JSON for later steps
$sizesPath = Join-Path $Raw '_sizes.json'
$sizesMap | ConvertTo-Json -Depth 5 | Out-File -LiteralPath $sizesPath -Encoding UTF8

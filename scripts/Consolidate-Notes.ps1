<#!
.SYNOPSIS
    Consolidate scattered Markdown/Text notes into a single issues.md with safety controls.

.DESCRIPTION
    Recursively scans the repository for .md and .txt notes (excluding common folders/files),
    normalizes content, merges YAML front-matter keys (later wins), deduplicates repeated
    headings and duplicate paragraphs/lines, and writes a consolidated C:\ZiggyClean\issues.md.

    By default this is a dry-run: it updates/creates issues.md and prints a summary.

.PARAMETER Apply
    After successfully writing issues.md, move all non-whitelisted .md/.txt sources into
    a timestamped backup directory under .docs-backup\<yyyyMMdd-HHmmss>\

.PARAMETER Purge
    When used with -Apply, permanently delete the moved files AFTER creating the backup.
    NOTE: This will remove the backup directory and its contents.

.PARAMETER Root
    Root folder to scan. Defaults to the folder containing this script.

.EXAMPLE
    .\Consolidate-Notes.ps1
    # Dry-run; writes/updates issues.md only (no file moves/deletions)

.EXAMPLE
    .\Consolidate-Notes.ps1 -Apply
    # Move redundant .md/.txt into backup after consolidating

.EXAMPLE
    .\Consolidate-Notes.ps1 -Apply -Purge
    # Delete moved files after creating a backup snapshot (backup folder is removed)

.NOTES
    - Never touches whitelisted files (README.*, CHANGELOG.*, LICENSE.*) or issues.md.
    - Excludes folders: node_modules, .git, dist, build, venv, .venv, coverage, out, logs, vendor
    - Handles encodings robustly: defaults to UTF-8; falls back when needed.
!#>
param(
    [switch]$Apply,
    [switch]$Purge,
    [string]$Root = $(Split-Path -Parent $PSCommandPath),
    [string]$OutputFileName = 'issues.md'
)

$ErrorActionPreference = 'Stop'

function Write-Info($msg) { Write-Host "[INFO ] $msg" -ForegroundColor Cyan }
function Write-Warn($msg) { Write-Host "[WARN ] $msg" -ForegroundColor Yellow }
function Write-Err ($msg) { Write-Host "[ERROR] $msg" -ForegroundColor Red }

function Test-PathExcluded([string]$full, [string[]]$segments) {
    foreach ($seg in $segments) {
        $esc = [Regex]::Escape($seg)
        $pattern = "(^|[\\/])$esc([\\/])"
        if ($full -match $pattern) { return $true }
    }
    return $false
}

try {
    # Resolve paths
    $rootPath = [System.IO.Path]::GetFullPath($Root)
    if (-not (Test-Path $rootPath)) { throw "Root path not found: $rootPath" }

    $outputPath = Join-Path $rootPath $OutputFileName
    $backupRoot = Join-Path $rootPath '.docs-backup'

    Write-Info "Root: $rootPath"
    Write-Info "Output: $outputPath"

    # Whitelist patterns (never moved/deleted)
    $whitelistNamePatterns = @(
        '^issues\.md$','^README\..+$','^CHANGELOG\..+$','^LICENSE\..+$'
    )

    # Excluded directory names (case-insensitive)
    $excludedDirs = @('node_modules','\.git','dist','build','venv','\.venv','coverage','out','logs','vendor')

    # Gather candidate files (.md/.txt), excluding output and whitelisted doc names
    $allFiles = Get-ChildItem -Path $rootPath -Recurse -File -ErrorAction SilentlyContinue |
        Where-Object {
            ($_.Extension -match '^(?i)\.(md|txt)$') -and -not (Test-PathExcluded -full $_.FullName -segments $excludedDirs)
        }

    # Filter out output file and whitelisted names (by relative name)
    $relative = { param($fi) (Resolve-Path -LiteralPath $fi.FullName).Path.Substring($rootPath.Length).TrimStart(([char]92),([char]47)) }
    $candidates = @()
    foreach ($f in $allFiles) {
        $rel = & $relative $f
        $name = $f.Name
        if ((Test-Path -LiteralPath $outputPath) -and ([string]::Compare((Resolve-Path -LiteralPath $f.FullName).Path, (Resolve-Path -LiteralPath $outputPath).Path, $true) -eq 0)) { continue }
        $isWhite = $false
        foreach ($pat in $whitelistNamePatterns) { if ($name -imatch $pat) { $isWhite = $true; break } }
        if ($isWhite) { continue }
        $candidates += [PSCustomObject]@{ File=$f; Rel=$rel }
    }

    if (-not $candidates -or $candidates.Count -eq 0) {
        Write-Warn "No candidate .md/.txt files found to consolidate."
        # Still ensure issues.md exists
        if (-not (Test-Path $outputPath)) { Set-Content -Path $outputPath -Value "# Issues\n\n_No notes found._" -Encoding UTF8 }
        exit 0
    }

    # Special handling: known-info.md and known\\* at repo root should merge last
    $knownFiles = @()
    $normalFiles = @()
    foreach ($c in $candidates) {
        $rel = $c.Rel -replace '^\\',''
        if ($rel -imatch '^(known-info\.md)$' -or $rel -imatch '^known\\.*\.(md|txt)$') { $knownFiles += $c } else { $normalFiles += $c }
    }

    # Sort normal files by LastWriteTime (older first), then append known files (also sorted)
    $normalFiles = $normalFiles | Sort-Object { $_.File.LastWriteTimeUtc }
    $knownFiles  = $knownFiles  | Sort-Object { $_.File.LastWriteTimeUtc }
    $ordered = @($normalFiles + $knownFiles)

    # Encoding helpers
    $encodings = @([System.Text.UTF8Encoding]::new($false), [System.Text.UTF8Encoding]::new($true), [System.Text.UnicodeEncoding]::new($false,$true), [System.Text.UnicodeEncoding]::new($true,$true), [System.Text.ASCIIEncoding]::new())
    function Try-ReadText([string]$path) {
        try { return Get-Content -LiteralPath $path -Raw -Encoding UTF8 } catch {}
        try { return Get-Content -LiteralPath $path -Raw -Encoding Default } catch {}
        try {
            $bytes = [System.IO.File]::ReadAllBytes($path)
            foreach ($enc in $encodings) {
                try { return $enc.GetString($bytes) } catch {}
            }
            return [System.Text.UTF8Encoding]::new($false).GetString($bytes)
        } catch {
            throw "Failed to read file with any supported encoding: $path"
        }
    }

    # YAML front-matter parsing (simple key: value at top)
    function Parse-YamlFrontMatter([string]$text) {
        $lines = $text -split "`r?`n"
        if ($lines.Count -lt 3) { return @{}, $text }
        if ($lines[0].Trim() -ne '---') { return @{}, $text }
        $i = 1; $map = @{}; $bodyStart = 0
        while ($i -lt $lines.Count) {
            if ($lines[$i].Trim() -eq '---') { $bodyStart = $i + 1; break }
            if ($lines[$i] -match '^(?<k>[^:]+):\s*(?<v>.*)$') {
                $k = $matches.k.Trim(); $v = $matches.v.Trim()
                if (($v.StartsWith('"') -and $v.EndsWith('"')) -or ($v.StartsWith("'") -and $v.EndsWith("'"))) {
                    $v = $v.Trim('"', "'")
                }
                $map[$k] = $v
            }
            $i++
        }
        if ($bodyStart -eq 0) { return @{}, $text }
        $body = ((@($lines) | Select-Object -Skip $bodyStart) -join "`r`n")
        return $map, $body
    }

    function Merge-FrontMatter([hashtable]$accum, [hashtable]$next) {
        foreach ($k in $next.Keys) { $accum[$k] = $next[$k] }
        return $accum
    }

    # Normalize within a single file: dedupe headings in that file and collapse repeated blank lines
    function Normalize-PerFile([string]$text) {
        $seenHeadings = New-Object System.Collections.Generic.HashSet[string]
        $out = New-Object System.Collections.Generic.List[string]
        $prevBlank = $false
        foreach ($line in ($text -split "`r?`n")) {
            $isHeading = $false
            if ($line -match '^\s{0,3}#{1,6}\s+(?<h>.+)$') {
                $h = $matches.h.Trim()
                $isHeading = $true
                if ($seenHeadings.Contains($h)) { continue }
                $seenHeadings.Add($h) | Out-Null
            }
            $trimmed = $line.Trim()
            $isBlank = [string]::IsNullOrWhiteSpace($trimmed)
            if ($isBlank -and $prevBlank) { continue }
            $out.Add($line) | Out-Null
            $prevBlank = $isBlank
        }
        return ($out -join "`r`n").Trim()
    }

    # Global de-duplication across files: paragraphs/lines
    $globalLineSet = New-Object System.Collections.Generic.HashSet[string]([System.StringComparer]::Ordinal)
    $globalParagraphSet = New-Object System.Collections.Generic.HashSet[string]([System.StringComparer]::Ordinal)
    $removedLineCount = 0
    $removedParaCount = 0

    $toc = New-Object System.Collections.Generic.List[string]
    $sections = New-Object System.Collections.Generic.List[string]

    $mergedFrontMatter = @{}

    foreach ($c in $ordered) {
        $file = $c.File
        $rel = $c.Rel -replace '^\\',''
        $text = Try-ReadText $file.FullName

        # Extract and merge front-matter (Markdown only)
        $front = @{}
        $body = $text
        if ($file.Extension -match '^(?i)\.md$') {
            $parsed = Parse-YamlFrontMatter $text
            $front = $parsed[0]
            $body  = $parsed[1]
            $mergedFrontMatter = Merge-FrontMatter $mergedFrontMatter $front
        }

        $body = Normalize-PerFile $body

        # De-duplicate paragraphs
        $buf = New-Object System.Collections.Generic.List[string]
        $para = New-Object System.Collections.Generic.List[string]
        function Flush-Para() {
            if ($para.Count -eq 0) { return }
            $ptext = ($para -join "`n").Trim()
            if ($ptext.Length -gt 0) {
                if ($globalParagraphSet.Contains($ptext)) { $script:removedParaCount++ }
                else { $globalParagraphSet.Add($ptext) | Out-Null; $buf.AddRange($para) }
            }
            $buf.Add('') | Out-Null
            $para.Clear()
        }
        foreach ($ln in ($body -split "`r?`n")) {
            if ([string]::IsNullOrWhiteSpace($ln)) { Flush-Para } else { $para.Add($ln) | Out-Null }
        }
        Flush-Para

        # Fallback to line-level dedupe within the buffered result
        $finalLines = New-Object System.Collections.Generic.List[string]
        foreach ($ln in $buf) {
            $key = $ln
            if ($key -eq '') { $finalLines.Add($ln) | Out-Null; continue }
            if ($globalLineSet.Contains($key)) { $removedLineCount++ } else { $globalLineSet.Add($key) | Out-Null; $finalLines.Add($ln) | Out-Null }
        }
        # Collapse extra blank lines again
        $clean = New-Object System.Collections.Generic.List[string]
        $prevBlank2 = $false
        foreach ($ln in $finalLines) {
            $isBlank = [string]::IsNullOrWhiteSpace($ln)
            if ($isBlank -and $prevBlank2) { continue }
            $clean.Add($ln) | Out-Null
            $prevBlank2 = $isBlank
        }

        $displayTime = $file.LastWriteTime.ToString('yyyy-MM-dd HH:mm')
        $sections.Add("## From: $rel ($displayTime)" + "`r`n`r`n" + ($clean -join "`r`n").Trim()) | Out-Null
        $toc.Add("- $rel ($displayTime)") | Out-Null
    }

    # Compose output
    $header = "# Consolidated Issues" + "`r`n`r`n" + (Get-Date).ToUniversalTime().ToString('yyyy-MM-dd HH:mm \(UTC\)') + "`r`n" + "`r`n## Table of contents`r`n" + ($toc -join "`r`n") + "`r`n"

    $fmOut = ''
    if ($mergedFrontMatter.Keys.Count -gt 0) {
        $fmLines = @('---')
        foreach ($k in ($mergedFrontMatter.Keys | Sort-Object)) {
            $v = $mergedFrontMatter[$k]
            if ($v -match '[:#\-]') { $v = '"' + $v.Replace('"','\"') + '"' }
            $fmLines += "$(" + $k + "): $(" + $v + ")"
        }
        $fmLines += '---'
        $fmOut = ($fmLines -join "`r`n") + "`r`n`r`n"
    }

    $final = $fmOut + $header + "`r`n" + ($sections -join "`r`n`r`n") + "`r`n"

    # Ensure directory exists (root exists already). Write issues.md as UTF-8 (no BOM)
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($outputPath, $final, $utf8NoBom)

    $bytesMerged = ([System.Text.UTF8Encoding]::new($false)).GetByteCount($final)
    Write-Info ("Wrote: {0} ({1} bytes)" -f $outputPath, $bytesMerged)
    Write-Info ("Sources: {0}; Duplicate paragraphs removed: {1}; Duplicate lines removed: {2}" -f $ordered.Count, $removedParaCount, $removedLineCount)

    if ($Apply) {
        $stamp = (Get-Date).ToString('yyyyMMdd-HHmmss')
        $backupDir = Join-Path $backupRoot $stamp
        New-Item -ItemType Directory -Force -Path $backupDir | Out-Null
        Write-Info "Backup directory: $backupDir"

        $moved = 0
        foreach ($c in $ordered) {
            $src = $c.File.FullName
            # Do not move whitelisted or the output file
            $name = [System.IO.Path]::GetFileName($src)
            $isWhite = $false
            foreach ($pat in $whitelistNamePatterns) { if ($name -imatch $pat) { $isWhite = $true; break } }
            if ($isWhite) { continue }
            if ([string]::Compare((Resolve-Path -LiteralPath $src).Path, (Resolve-Path -LiteralPath $outputPath), $true) -eq 0) { continue }

            $rel = $c.Rel -replace '^\\',''
            $dest = Join-Path $backupDir $rel
            $destDir = Split-Path -Parent $dest
            New-Item -ItemType Directory -Force -Path $destDir | Out-Null
            Move-Item -LiteralPath $src -Destination $dest -Force
            $moved++
        }
        Write-Info "Moved $moved files into backup."

        if ($Purge) {
            Write-Warn "-Purge specified: removing backup directory and its contents (permanent)."
            Remove-Item -LiteralPath $backupDir -Recurse -Force
            Write-Info "Backup removed. Files have been permanently deleted."
        }
    } else {
        Write-Info "Dry-run complete. No files were moved or deleted."
    }

    exit 0
}
catch {
    Write-Err $_
    exit 1
}

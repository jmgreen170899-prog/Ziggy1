<#!
.SYNOPSIS
    Back up everything in a root except a single keep file, optionally purge originals.

.DESCRIPTION
    In a given root (default C:\ZiggyClean), this script discovers all files and folders
    except a single keep file (default: allnotes.md at the root), backs them up into a
    timestamped set under <BackupRoot> (default: <Root>\.purge-backup\YYYYMMDD-HHmmss),
    verifies copied file hashes, and optionally purges originals (Apply+Purge).

.PARAMETER Root
    Root directory to process. Defaults to C:\ZiggyClean.

.PARAMETER KeepFileName
    File name to keep at the root (case-insensitive). Defaults to allnotes.md.

.PARAMETER BackupRoot
    Root directory for backups. Defaults to <Root>\.purge-backup.

.PARAMETER Apply
    Perform backup (and purge if -Purge is also specified). Without -Apply the script
    runs in Dry Run mode and makes no changes.

.PARAMETER Purge
    When used with -Apply, removes the originals after successful backup verification.
    Without -Apply this flag is ignored.

.PARAMETER Force
    Proceed even if the keep file is not found at the root. Without -Force, the script
    aborts safely when the keep file is missing.

.PARAMETER DryRun
    Explicitly request a dry run (no changes). Dry-run is the default when -Apply is not present.

.EXAMPLE
    .\Purge-To-AllNotes.ps1
    Dry run. Shows what would be backed up and purged; changes nothing.

.EXAMPLE
    .\Purge-To-AllNotes.ps1 -Apply
    Back up everything except allnotes.md into timestamped backup; do not delete originals.

.EXAMPLE
    .\Purge-To-AllNotes.ps1 -Apply -Purge
    Back up then delete everything except allnotes.md, leaving only allnotes.md in the root.

.EXAMPLE
    .\Purge-To-AllNotes.ps1 -Root "D:\Project" -KeepFileName "allnotes.md" -Apply -Purge
    Same on a different folder.

.EXAMPLE
    .\Purge-To-AllNotes.ps1 -Apply -Purge -Force
    Proceed even if allnotes.md is missing (not recommended).

.NOTES
    - Colorized output: BACKUP, VERIFY, PURGE, SKIP actions are highlighted.
    - Idempotent: runs create new timestamped backup sets; originals are removed only with -Apply -Purge.
    - Exits non-zero on errors such as verification failures.
!#>
[CmdletBinding(SupportsShouldProcess=$true, ConfirmImpact='High')]
param(
    [string]$Root = 'C:\ZiggyClean',
    [string]$KeepFileName = 'allnotes.md',
    [string]$BackupRoot,
    [switch]$Apply,
    [switch]$Purge,
    [switch]$Force,
    [switch]$DryRun
)

$ErrorActionPreference = 'Stop'

function Write-Info($m)  { Write-Host "[INFO ] $m" -ForegroundColor Cyan }
function Write-Warn($m)  { Write-Host "[WARN ] $m" -ForegroundColor Yellow }
function Write-Err($m)   { Write-Host "[ERROR] $m" -ForegroundColor Red }
function Write-Act($tag, $m, [ConsoleColor]$c) { Write-Host ("[{0}] {1}" -f $tag, $m) -ForegroundColor $c }

function Get-LongPath([string]$p) {
    if (-not $p) { return $p }
    if ($p.StartsWith('\\?\')) { return $p }
    if ($p -match '^[a-zA-Z]:') { return "\\\\?\" + $p }
    return $p
}

function Resolve-Root([string]$root) {
    $rp = [System.IO.Path]::GetFullPath($root)
    if (-not (Test-Path -LiteralPath $rp)) { throw "Root not found: $rp" }
    return (Resolve-Path -LiteralPath $rp).Path
}

function Get-Relative([string]$full, [string]$root) {
    $full = (Resolve-Path -LiteralPath $full).Path
    $root = (Resolve-Path -LiteralPath $root).Path
    $rel = $full.Substring($root.Length).TrimStart(([char]92),([char]47))
    if (-not $rel) { return '.' }
    return $rel
}

function Get-SizeBytes([System.IO.FileInfo]$fi) { return $fi.Length }

function Discover([string]$root, [string]$keepName, [string]$backupRoot) {
    $result = [ordered]@{}
    $result.Root = $root
    $result.KeepPath = Join-Path $root $keepName
    $result.BackupRoot = if ($backupRoot) { $backupRoot } else { Join-Path $root '.purge-backup' }

    # script self path
    $self = $MyInvocation.MyCommand.Path
    $result.ScriptPath = $self

    $keepExists = Test-Path -LiteralPath $result.KeepPath
    if (-not $keepExists -and -not $Force) {
        throw "Keep file not found at root: $($result.KeepPath). Use -Force to proceed anyway."
    }

    if ($keepExists) {
        try {
            $kf = Get-Item -LiteralPath $result.KeepPath -ErrorAction Stop
            if ($kf.PSIsContainer) { throw "Keep file is a directory: $($result.KeepPath)" }
            if ($kf.Length -gt 10MB -and -not $Force) {
                Write-Warn ("Keep file is {0:N2} MB (>10 MB). Consider verifying it's correct. Use -Force to suppress." -f ($kf.Length/1MB))
            }
        } catch {}
    }

    # Build candidates: everything under root except keep file, backup root, and this script file
    $candidates = @()
    $all = Get-ChildItem -LiteralPath $root -Force
    foreach ($entry in $all) {
        # Skip the keep file at root
        if ($entry.PSIsContainer -eq $false -and ($entry.Name -ieq $keepName)) { continue }
        # Skip the backup root dir itself
        if ($entry.PSIsContainer -and ($entry.FullName -ieq $result.BackupRoot)) { continue }
        # Skip the script file itself
        if ($entry.FullName -ieq $result.ScriptPath) { continue }
        $candidates += $entry
    }

    # Expand directories recursively into copy/remove units while preserving structure
    $units = @()
    foreach ($e in $candidates) {
        $units += $e
    }

    # Compute stats
    $fileCount = 0; $dirCount = 0; $totalBytes = 0L
    foreach ($u in $units) {
        if ($u.PSIsContainer) { $dirCount++ }
        else { $fileCount++; $totalBytes += $u.Length }
    }

    $result.Candidates = $units
    $result.FileCount = $fileCount
    $result.DirCount = $dirCount
    $result.TotalBytes = $totalBytes
    return $result
}

function Ensure-Dir([string]$p) { if (-not (Test-Path -LiteralPath $p)) { New-Item -Path $p -ItemType Directory -Force | Out-Null } }

function New-BackupSet([string]$backupRoot) {
    $stamp = (Get-Date).ToString('yyyyMMdd-HHmmss')
    $set = Join-Path $backupRoot $stamp
    Ensure-Dir $backupRoot
    Ensure-Dir $set
    return $set
}

function Backup([object]$plan, [string]$setPath, [switch]$whatIf) {
    $copiedFiles = New-Object System.Collections.Generic.List[object]
    $copiedTotal = 0L
    foreach ($item in $plan.Candidates) {
        $rel = Get-Relative $item.FullName $plan.Root
        $dest = Join-Path $setPath $rel
        if ($item.PSIsContainer) {
            Write-Act 'BACKUP' "DIR  $rel (recursive)" Green
            if (-not $whatIf) { Ensure-Dir $dest }
            # Copy all files within the directory recursively, preserving structure
            $files = Get-ChildItem -LiteralPath $item.FullName -Recurse -File -Force -ErrorAction SilentlyContinue
            if ($files) {
                foreach ($f in $files) {
                    $fRel = Get-Relative $f.FullName $plan.Root
                    $fDest = Join-Path $setPath $fRel
                    if (-not $whatIf) {
                        $fDestDir = Split-Path -Parent $fDest
                        Ensure-Dir $fDestDir
                        Copy-Item -LiteralPath $f.FullName -Destination $fDest -Force
                        $copiedFiles.Add([pscustomobject]@{ Src=$f.FullName; Dst=$fDest; Size=$f.Length }) | Out-Null
                        $copiedTotal += $f.Length
                    }
                }
            } else {
                # Empty directory: ensure it's present in backup for structure
                if (-not $whatIf) { Ensure-Dir $dest }
            }
        } else {
            Write-Act 'BACKUP' ("FILE {0} ({1:N0} bytes)" -f $rel, $item.Length) Green
            if (-not $whatIf) {
                $destDir = Split-Path -Parent $dest
                Ensure-Dir $destDir
                Copy-Item -LiteralPath $item.FullName -Destination $dest -Force
                $copiedFiles.Add([pscustomobject]@{ Src=$item.FullName; Dst=$dest; Size=$item.Length }) | Out-Null
                $copiedTotal += $item.Length
            }
        }
    }
    return [pscustomobject]@{ Files=$copiedFiles; Bytes=$copiedTotal; Set=$setPath }
}

function Verify-Backup([object]$backupInfo) {
    $mismatch = 0
    foreach ($f in $backupInfo.Files) {
        try {
            $srcH = (Get-FileHash -LiteralPath $f.Src -Algorithm SHA256).Hash
            $dstH = (Get-FileHash -LiteralPath $f.Dst -Algorithm SHA256).Hash
            if ($srcH -ne $dstH) {
                Write-Act 'VERIFY' ("HASH MISMATCH: {0}" -f (Get-Relative $f.Src $PWD)) Red
                $mismatch++
            } else {
                Write-Act 'VERIFY' ("OK   {0}" -f (Get-Relative $f.Src $PWD)) DarkGreen
            }
        } catch {
            Write-Err ("Verify failed: {0}" -f $_)
            $mismatch++
        }
    }
    return ($mismatch -eq 0)
}

function Clear-Attributes([string]$path) {
    try {
        $fi = Get-Item -LiteralPath $path -Force -ErrorAction Stop
        if (-not $fi.PSIsContainer) {
            [System.IO.File]::SetAttributes($fi.FullName, [System.IO.FileAttributes]::Normal)
        }
    } catch {}
}

function Purge-Originals([object]$plan) {
    foreach ($item in $plan.Candidates) {
        $rel = Get-Relative $item.FullName $plan.Root
        if ($item.PSIsContainer) {
            Write-Act 'PURGE' "DIR  $rel" Magenta
            try { Remove-Item -LiteralPath $item.FullName -Recurse -Force -ErrorAction Stop } catch { Write-Err $_; throw }
        } else {
            Write-Act 'PURGE' ("FILE {0}" -f $rel) Magenta
            try { Clear-Attributes $item.FullName; Remove-Item -LiteralPath $item.FullName -Force -ErrorAction Stop } catch { Write-Err $_; throw }
        }
    }
}

try {
    $rootPath = Resolve-Root $Root
    if (-not $BackupRoot) { $BackupRoot = Join-Path $rootPath '.purge-backup' }

    Write-Info "Root: $rootPath"
    Write-Info "Keep: $KeepFileName"
    Write-Info "BackupRoot: $BackupRoot"

    $plan = Discover -root $rootPath -keepName $KeepFileName -backupRoot $BackupRoot

    Write-Info ("Candidates -> Files: {0}, Dirs: {1}, Total: {2:N0} bytes" -f $plan.FileCount, $plan.DirCount, $plan.TotalBytes)

    $doApply = [bool]$Apply
    $doPurge = $doApply -and [bool]$Purge

    if (-not $doApply -or $DryRun) {
        Write-Warn "Dry run: listing actions only (no changes)."
        foreach ($item in $plan.Candidates) {
            $rel = Get-Relative $item.FullName $plan.Root
            if ($item.PSIsContainer) { Write-Act 'WILL-BACKUP' "DIR  $rel" DarkYellow }
            else { Write-Act 'WILL-BACKUP' ("FILE {0} ({1:N0} bytes)" -f $rel, $item.Length) DarkYellow }
        }
        Write-Info "No files copied or deleted in dry-run."
        exit 0
    }

    $setPath = New-BackupSet -backupRoot $BackupRoot
    $logFile = Join-Path $setPath 'purge-log.txt'
    try { Start-Transcript -Path $logFile -Force | Out-Null } catch {}

    Write-Info "Backup set: $setPath"
    $bk = Backup -plan $plan -setPath $setPath
    Write-Info ("Backed up {0} files, {1:N0} bytes." -f $bk.Files.Count, $bk.Bytes)

    Write-Info "Verifying backup integrity (hash)"
    $ok = Verify-Backup -backupInfo $bk
    if (-not $ok) { throw "Verification failed. Aborting purge." }

    if ($doPurge) {
        $summary = ("Remove {0} files and {1} dirs totalling ~{2:N0} bytes from {3}" -f $plan.FileCount, $plan.DirCount, $plan.TotalBytes, $plan.Root)
        if ($PSCmdlet.ShouldProcess($plan.Root, $summary)) {
            Purge-Originals -plan $plan
            Write-Info "Purge complete. Only $KeepFileName should remain at root along with backup folder."
        } else {
            Write-Warn "Purge canceled by user. Originals retained."
        }
    } else {
        Write-Info "Apply mode without -Purge: originals retained after successful backup."
    }

    try { Stop-Transcript | Out-Null } catch {}
    exit 0
}
catch {
    Write-Err $_
    exit 1
}

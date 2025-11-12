# sync-from-github.ps1
# Automated script to sync changes from GitHub to local repository (Windows)

param(
    [switch]$AutoInstall = $false,
    [switch]$NoStash = $false
)

# Script configuration
$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot

# Colors for output
function Write-Status {
    param([string]$Message)
    Write-Host "✓ " -ForegroundColor Green -NoNewline
    Write-Host $Message
}

function Write-Warning-Custom {
    param([string]$Message)
    Write-Host "⚠ " -ForegroundColor Yellow -NoNewline
    Write-Host $Message
}

function Write-Error-Custom {
    param([string]$Message)
    Write-Host "✗ " -ForegroundColor Red -NoNewline
    Write-Host $Message
}

function Write-Step {
    param([string]$Message)
    Write-Host "▶ " -ForegroundColor Blue -NoNewline
    Write-Host $Message
}

# Header
Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════╗" -ForegroundColor Blue
Write-Host "║     ZiggyAI: Sync Changes from GitHub                 ║" -ForegroundColor Blue
Write-Host "╚════════════════════════════════════════════════════════╝" -ForegroundColor Blue
Write-Host ""

# Change to repository root
Set-Location $RepoRoot

# Step 1: Check if we're in a git repository
Write-Step "Checking repository status..."
if (-not (Test-Path ".git")) {
    Write-Error-Custom "Not a git repository. Please run this script from the repository root."
    exit 1
}
Write-Status "Git repository confirmed"

# Step 2: Get current branch
$CurrentBranch = git rev-parse --abbrev-ref HEAD
Write-Status "Current branch: $CurrentBranch"

# Step 3: Check for uncommitted changes
$DiffOutput = git diff-index --quiet HEAD -- 2>&1
$HasChanges = $LASTEXITCODE -ne 0

if ($HasChanges) {
    Write-Warning-Custom "You have uncommitted changes!"
    Write-Host ""
    Write-Host "Files with changes:" -ForegroundColor Yellow
    git status --short
    Write-Host ""
    
    if (-not $NoStash) {
        $Response = Read-Host "Do you want to stash these changes? (y/n)"
        if ($Response -eq 'y' -or $Response -eq 'Y') {
            $StashMessage = "Auto-stash before sync $(Get-Date -Format 'yyyy-MM-dd_HH:mm:ss')"
            git stash push -m $StashMessage
            Write-Status "Changes stashed"
            $Stashed = $true
        } else {
            Write-Error-Custom "Cannot sync with uncommitted changes. Please commit or stash them first."
            exit 1
        }
    } else {
        Write-Error-Custom "Cannot sync with uncommitted changes (NoStash flag set)."
        exit 1
    }
} else {
    Write-Status "No uncommitted changes"
    $Stashed = $false
}

# Step 4: Fetch from GitHub
Write-Step "Fetching latest changes from GitHub..."
git fetch origin --prune
if ($LASTEXITCODE -eq 0) {
    Write-Status "Fetched from origin"
} else {
    Write-Error-Custom "Failed to fetch from origin"
    exit 1
}

# Step 5: Check if we're behind remote
$Upstream = "origin/$CurrentBranch"
$Local = git rev-parse "@" 2>$null
$Remote = git rev-parse $Upstream 2>$null
$Base = git merge-base "@" $Upstream 2>$null

if (-not $Remote) {
    Write-Warning-Custom "No remote branch found for $CurrentBranch"
    Write-Warning-Custom "Skipping pull. You may need to push this branch first."
} elseif ($Local -eq $Remote) {
    Write-Status "Already up to date with $Upstream"
} elseif ($Local -eq $Base) {
    Write-Step "Pulling changes from $Upstream..."
    git pull origin $CurrentBranch
    if ($LASTEXITCODE -eq 0) {
        Write-Status "Successfully pulled changes"
    } else {
        Write-Error-Custom "Failed to pull changes"
        exit 1
    }
} elseif ($Remote -eq $Base) {
    Write-Warning-Custom "Your branch is ahead of $Upstream"
    Write-Warning-Custom "Consider pushing your changes: git push origin $CurrentBranch"
} else {
    Write-Warning-Custom "Branches have diverged!"
    Write-Warning-Custom "You may need to merge or rebase manually"
    Write-Host ""
    git log --oneline "HEAD..$Upstream" --pretty=format:"  Remote: %h %s"
    Write-Host ""
    git log --oneline "$Upstream..HEAD" --pretty=format:"  Local:  %h %s"
    Write-Host ""
}

# Step 6: Check for dependency changes
Write-Step "Checking for dependency updates..."
$DepsChanged = $false

# Check if package.json changed
$PackageJsonChanged = git diff "HEAD@{1}" HEAD --name-only 2>$null | Select-String "package.json"
if ($PackageJsonChanged) {
    Write-Warning-Custom "Root package.json changed"
    $DepsChanged = $true
}

$FrontendPackageChanged = git diff "HEAD@{1}" HEAD --name-only 2>$null | Select-String "frontend/package.json"
if ($FrontendPackageChanged) {
    Write-Warning-Custom "Frontend package.json changed"
    $DepsChanged = $true
}

$RequirementsChanged = git diff "HEAD@{1}" HEAD --name-only 2>$null | Select-String "backend/requirements.lock"
if ($RequirementsChanged) {
    Write-Warning-Custom "Backend requirements.lock changed"
    $DepsChanged = $true
}

if ($DepsChanged) {
    Write-Host ""
    
    $InstallDeps = $AutoInstall
    if (-not $AutoInstall) {
        $Response = Read-Host "Dependencies changed. Install updates now? (y/n)"
        $InstallDeps = ($Response -eq 'y' -or $Response -eq 'Y')
    }
    
    if ($InstallDeps) {
        # Install root dependencies
        if (Test-Path "package.json") {
            Write-Step "Installing root dependencies..."
            npm install
            if ($LASTEXITCODE -eq 0) {
                Write-Status "Root dependencies installed"
            } else {
                Write-Warning-Custom "Failed to install root dependencies"
            }
        }
        
        # Install frontend dependencies
        if (Test-Path "frontend/package.json") {
            Write-Step "Installing frontend dependencies..."
            Push-Location frontend
            npm install
            Pop-Location
            if ($LASTEXITCODE -eq 0) {
                Write-Status "Frontend dependencies installed"
            } else {
                Write-Warning-Custom "Failed to install frontend dependencies"
            }
        }
        
        # Install backend dependencies
        if (Test-Path "backend/requirements.lock") {
            Write-Step "Installing backend dependencies..."
            if (Get-Command python -ErrorAction SilentlyContinue) {
                Push-Location backend
                python -m pip install -r requirements.lock
                Pop-Location
                if ($LASTEXITCODE -eq 0) {
                    Write-Status "Backend dependencies installed"
                } else {
                    Write-Warning-Custom "Failed to install backend dependencies"
                }
            } else {
                Write-Warning-Custom "Python not found. Skipping backend dependencies."
            }
        }
    } else {
        Write-Warning-Custom "Skipped dependency installation"
        Write-Host ""
        Write-Host "Remember to install manually:" -ForegroundColor Yellow
        Write-Host "  - Root: npm install"
        Write-Host "  - Frontend: cd frontend; npm install"
        Write-Host "  - Backend: cd backend; pip install -r requirements.lock"
    }
} else {
    Write-Status "No dependency changes detected"
}

# Step 7: Restore stashed changes if any
if ($Stashed) {
    Write-Host ""
    $Response = Read-Host "Restore stashed changes? (y/n)"
    if ($Response -eq 'y' -or $Response -eq 'Y') {
        git stash pop
        Write-Status "Stashed changes restored"
    } else {
        Write-Warning-Custom "Changes remain stashed. Use 'git stash pop' to restore them later."
    }
}

# Step 8: Summary
Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════╗" -ForegroundColor Blue
Write-Host "║     Sync Complete!                                     ║" -ForegroundColor Blue
Write-Host "╚════════════════════════════════════════════════════════╝" -ForegroundColor Blue
Write-Host ""

Write-Host "Recent commits:" -ForegroundColor Green
git log --oneline -5 --pretty=format:"  %h %s (%ar)"
Write-Host ""
Write-Host ""

# Step 9: Show verification commands
Write-Host "Verification commands:" -ForegroundColor Blue
Write-Host "  git status              # Check current state"
Write-Host "  git log --oneline -10   # View recent commits"
Write-Host "  git diff origin/$CurrentBranch  # Compare with remote"
Write-Host ""

# Optional: Run quick health check
Write-Host "Optional next steps:" -ForegroundColor Blue
Write-Host "  1. Run tests: cd backend; pytest -q"
Write-Host "  2. Start dev server: npm run dev:all"
Write-Host "  3. Check audit: make audit-quick"
Write-Host ""

Write-Status "Done! Your local files are now synced with GitHub."
Write-Host ""

# Usage information
Write-Host "Script usage:" -ForegroundColor Cyan
Write-Host "  .\scripts\sync-from-github.ps1                    # Interactive mode"
Write-Host "  .\scripts\sync-from-github.ps1 -AutoInstall       # Auto-install dependencies"
Write-Host "  .\scripts\sync-from-github.ps1 -NoStash           # Don't stash changes"
Write-Host ""

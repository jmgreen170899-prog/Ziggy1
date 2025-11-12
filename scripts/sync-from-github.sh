#!/bin/bash
# sync-from-github.sh
# Automated script to sync changes from GitHub to local repository

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     ZiggyAI: Sync Changes from GitHub                 ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
echo ""

# Function to print status
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_step() {
    echo -e "${BLUE}▶${NC} $1"
}

# Change to repository root
cd "$REPO_ROOT"

# Step 1: Check if we're in a git repository
print_step "Checking repository status..."
if [ ! -d ".git" ]; then
    print_error "Not a git repository. Please run this script from the repository root."
    exit 1
fi
print_status "Git repository confirmed"

# Step 2: Get current branch
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
print_status "Current branch: $CURRENT_BRANCH"

# Step 3: Check for uncommitted changes
if ! git diff-index --quiet HEAD --; then
    print_warning "You have uncommitted changes!"
    echo -e "${YELLOW}Files with changes:${NC}"
    git status --short
    echo ""
    read -p "Do you want to stash these changes? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git stash push -m "Auto-stash before sync $(date +%Y-%m-%d_%H:%M:%S)"
        print_status "Changes stashed"
        STASHED=true
    else
        print_error "Cannot sync with uncommitted changes. Please commit or stash them first."
        exit 1
    fi
else
    print_status "No uncommitted changes"
    STASHED=false
fi

# Step 4: Fetch from GitHub
print_step "Fetching latest changes from GitHub..."
git fetch origin --prune
print_status "Fetched from origin"

# Step 5: Check if we're behind remote
UPSTREAM=${1:-"origin/$CURRENT_BRANCH"}
LOCAL=$(git rev-parse @)
REMOTE=$(git rev-parse "$UPSTREAM" 2>/dev/null || echo "")
BASE=$(git merge-base @ "$UPSTREAM" 2>/dev/null || echo "")

if [ -z "$REMOTE" ]; then
    print_warning "No remote branch found for $CURRENT_BRANCH"
    print_warning "Skipping pull. You may need to push this branch first."
elif [ "$LOCAL" = "$REMOTE" ]; then
    print_status "Already up to date with $UPSTREAM"
elif [ "$LOCAL" = "$BASE" ]; then
    print_step "Pulling changes from $UPSTREAM..."
    git pull origin "$CURRENT_BRANCH"
    print_status "Successfully pulled changes"
elif [ "$REMOTE" = "$BASE" ]; then
    print_warning "Your branch is ahead of $UPSTREAM"
    print_warning "Consider pushing your changes: git push origin $CURRENT_BRANCH"
else
    print_warning "Branches have diverged!"
    print_warning "You may need to merge or rebase manually"
    git log --oneline HEAD.."$UPSTREAM" --pretty=format:"  Remote: %h %s"
    echo ""
    git log --oneline "$UPSTREAM"..HEAD --pretty=format:"  Local:  %h %s"
    echo ""
fi

# Step 6: Check for dependency changes
print_step "Checking for dependency updates..."
DEPS_CHANGED=false

# Check if package.json changed
if git diff HEAD@{1} HEAD --name-only 2>/dev/null | grep -q "package.json"; then
    print_warning "Root package.json changed"
    DEPS_CHANGED=true
fi

if git diff HEAD@{1} HEAD --name-only 2>/dev/null | grep -q "frontend/package.json"; then
    print_warning "Frontend package.json changed"
    DEPS_CHANGED=true
fi

if git diff HEAD@{1} HEAD --name-only 2>/dev/null | grep -q "backend/requirements.lock"; then
    print_warning "Backend requirements.lock changed"
    DEPS_CHANGED=true
fi

if [ "$DEPS_CHANGED" = true ]; then
    echo ""
    read -p "Dependencies changed. Install updates now? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # Install root dependencies
        if [ -f "package.json" ]; then
            print_step "Installing root dependencies..."
            npm install
            print_status "Root dependencies installed"
        fi
        
        # Install frontend dependencies
        if [ -f "frontend/package.json" ]; then
            print_step "Installing frontend dependencies..."
            cd frontend
            npm install
            cd ..
            print_status "Frontend dependencies installed"
        fi
        
        # Install backend dependencies
        if [ -f "backend/requirements.lock" ]; then
            print_step "Installing backend dependencies..."
            if command -v python3 &> /dev/null; then
                cd backend
                python3 -m pip install -r requirements.lock
                cd ..
                print_status "Backend dependencies installed"
            else
                print_warning "Python3 not found. Skipping backend dependencies."
            fi
        fi
    else
        print_warning "Skipped dependency installation"
        echo -e "${YELLOW}Remember to install manually:${NC}"
        echo "  - Root: npm install"
        echo "  - Frontend: cd frontend && npm install"
        echo "  - Backend: cd backend && pip install -r requirements.lock"
    fi
else
    print_status "No dependency changes detected"
fi

# Step 7: Restore stashed changes if any
if [ "$STASHED" = true ]; then
    echo ""
    read -p "Restore stashed changes? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git stash pop
        print_status "Stashed changes restored"
    else
        print_warning "Changes remain stashed. Use 'git stash pop' to restore them later."
    fi
fi

# Step 8: Summary
echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     Sync Complete!                                     ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}Recent commits:${NC}"
git log --oneline -5 --pretty=format:"  %C(yellow)%h%Creset %s %C(cyan)(%ar)%Creset"
echo ""
echo ""

# Step 9: Show verification commands
echo -e "${BLUE}Verification commands:${NC}"
echo "  git status              # Check current state"
echo "  git log --oneline -10   # View recent commits"
echo "  git diff origin/$CURRENT_BRANCH  # Compare with remote"
echo ""

# Optional: Run quick health check
echo -e "${BLUE}Optional next steps:${NC}"
echo "  1. Run tests: cd backend && pytest -q"
echo "  2. Start dev server: npm run dev:all"
echo "  3. Check audit: make audit-quick"
echo ""

print_status "Done! Your local files are now synced with GitHub."

# Merge Conflict Resolution Guide

## Background

Previously, the ZiggyAI repository experienced **SyntaxError** issues during application startup due to unresolved Git merge conflict markers being accidentally committed to source files, particularly in `app/main.py`.

Git merge conflict markers look like this:

```python
<<<<<<< HEAD
# Version A of the code
=======
# Version B of the code
>>>>>>> branch-name
```

When these markers are left in Python, JavaScript, or TypeScript files, they cause syntax errors that prevent the application from starting or building correctly.

## Prevention Measures

To prevent this issue from recurring, the repository now includes automated checks that detect and prevent conflict markers from being committed:

### 1. Automated Test

A pytest test is included in the backend test suite:

- **Location**: `backend/tests/test_no_merge_markers.py`
- **What it does**: Scans all source files for conflict markers
- **When it runs**: Every time tests are executed locally or in CI

### 2. Standalone Script

A standalone script can be run manually or in CI pipelines:

- **Location**: `scripts/check_merge_markers.py`
- **Usage**: `python scripts/check_merge_markers.py`
- **Exit codes**:
  - `0` - No conflict markers found (success)
  - `1` - Conflict markers detected (failure)

### 3. CI Integration

The check is integrated into the GitHub Actions CI workflow:

- **Location**: `.github/workflows/ci.yml`
- **When it runs**: On every pull request and push to main
- **Effect**: Pull requests with conflict markers will fail CI checks

## How to Resolve Merge Conflicts Correctly

When you encounter a merge conflict:

### Step 1: Identify the Conflict

Git will mark conflicted files. You'll see markers like:

```python
<<<<<<< HEAD
def old_function():
    return "old implementation"
=======
def new_function():
    return "new implementation"
>>>>>>> feature-branch
```

### Step 2: Decide on the Resolution

You have several options:

1. **Keep the current branch version** (HEAD):
   - Delete the markers and the other version
   - Keep only the code between `<<<<<<< HEAD` and `=======`

2. **Keep the incoming branch version**:
   - Delete the markers and the current version
   - Keep only the code between `=======` and `>>>>>>> branch-name`

3. **Merge both versions** (most common):
   - Carefully combine both code paths
   - Remove all conflict markers
   - Test that the merged code works correctly

4. **Write new code**:
   - Replace the entire conflicted section with new code that accomplishes both goals

### Step 3: Remove All Markers

Ensure you remove **all three marker lines**:

- `<<<<<<< HEAD` (or `<<<<<<< branch-name`)
- `=======`
- `>>>>>>> branch-name` (or `>>>>>>> commit-hash`)

### Step 4: Test Your Changes

Before committing:

1. **Run the backend tests**:

   ```bash
   cd backend
   pytest
   ```

2. **Check for import errors**:

   ```bash
   cd backend
   PYTHONPATH=. python -c "import app.main"
   ```

3. **Run the conflict marker check**:

   ```bash
   python scripts/check_merge_markers.py
   ```

4. **Build the frontend** (if applicable):
   ```bash
   cd frontend
   npm run build
   ```

### Step 5: Commit the Resolution

Once all tests pass and no markers remain:

```bash
git add .
git commit -m "Resolve merge conflicts in [files]"
```

## Common Mistakes to Avoid

❌ **Don't**: Simply delete one side without understanding what it does
❌ **Don't**: Commit files with conflict markers still present
❌ **Don't**: Skip testing after resolving conflicts
❌ **Don't**: Forget to remove all three marker lines

✅ **Do**: Read and understand both versions
✅ **Do**: Test the application after resolving
✅ **Do**: Remove all conflict markers completely
✅ **Do**: Run the automated checks before pushing

## Files Scanned by the Check

The automated check scans these file types:

- Python files (`.py`)
- JavaScript files (`.js`, `.jsx`)
- TypeScript files (`.ts`, `.tsx`)
- YAML files (`.yml`, `.yaml`)
- JSON files (`.json`)
- Markdown files (`.md`)

In these directories:

- `backend/`
- `frontend/`
- `scripts/`
- `docs/`

## Troubleshooting

### If the CI Check Fails

If the CI check detects conflict markers:

1. Pull the latest changes:

   ```bash
   git pull origin main
   ```

2. Run the check locally:

   ```bash
   python scripts/check_merge_markers.py
   ```

3. Open the reported files and remove all conflict markers

4. Verify the code works:

   ```bash
   cd backend && pytest
   cd frontend && npm run build
   ```

5. Commit and push the fix:
   ```bash
   git add .
   git commit -m "Remove merge conflict markers"
   git push
   ```

### False Positives

The check excludes common false positives like comment decorators:

- `# ===============` (Python comments)
- `// ==============` (JavaScript/TypeScript comments)

If you have a legitimate use case for these patterns, ensure they're in comments and use enough `=` characters to differentiate them from conflict markers.

## Summary

✅ **Prevention**: Automated checks in tests and CI
✅ **Detection**: Run `python scripts/check_merge_markers.py`
✅ **Resolution**: Remove markers, test code, commit
✅ **Verification**: CI will fail if markers are present

This system ensures that merge conflict markers can never be merged into the main branch, preventing the SyntaxError issues that occurred previously.

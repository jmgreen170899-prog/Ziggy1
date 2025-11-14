#!/usr/bin/env python3
"""
Standalone script to check for Git merge conflict markers in the repository.

This script scans all tracked source files to detect merge conflict markers
that could cause SyntaxError or other issues if committed.

Usage:
    python scripts/check_merge_markers.py

Exit codes:
    0 - No conflict markers found
    1 - Conflict markers detected
"""

import sys
from pathlib import Path


def check_merge_markers(repo_root: Path) -> list[str]:
    """
    Scan repository for merge conflict markers.
    
    Args:
        repo_root: Path to the repository root
        
    Returns:
        List of violation strings (file:line - message)
    """
    # Define patterns to search for
    conflict_markers = ["<<<<<<<", "=======", ">>>>>>>"]
    
    # Define file extensions to check
    extensions = [
        ".py",   # Python
        ".js",   # JavaScript
        ".ts",   # TypeScript
        ".tsx",  # TypeScript React
        ".jsx",  # JavaScript React
        ".yml",  # YAML
        ".yaml", # YAML
        ".json", # JSON
        ".md",   # Markdown (for docs)
    ]
    
    # Directories to scan
    dirs_to_scan = ["backend", "frontend", "scripts", "docs"]
    
    # Patterns to exclude (legitimate uses of these characters)
    exclude_patterns = [
        "# ====",  # Comment decorators
        "// ====", # Comment decorators
    ]
    
    violations = []
    
    for dir_name in dirs_to_scan:
        dir_path = repo_root / dir_name
        if not dir_path.exists():
            continue
            
        for ext in extensions:
            for file_path in dir_path.rglob(f"*{ext}"):
                # Skip files in common ignore directories
                if any(part in file_path.parts for part in [".git", "node_modules", "__pycache__", ".pytest_cache", "dist", "build"]):
                    continue
                
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        lines = f.readlines()
                    
                    # Track if we're inside a markdown code block
                    in_code_block = False
                    
                    for line_num, line in enumerate(lines, start=1):
                        # For markdown files, track code blocks
                        if file_path.suffix == ".md":
                            if line.strip().startswith("```"):
                                in_code_block = not in_code_block
                            # Skip lines inside markdown code blocks (they're examples)
                            if in_code_block:
                                continue
                        
                        # Check for conflict markers at the start of the line
                        stripped = line.lstrip()
                        
                        # Skip lines that are just decorative comments
                        is_decorator = any(pattern in line for pattern in exclude_patterns)
                        if is_decorator:
                            continue
                        
                        for marker in conflict_markers:
                            if stripped.startswith(marker) and not is_decorator:
                                # Additional check: conflict markers typically have specific format
                                if marker == "<<<<<<< " or (marker == "<<<<<<<" and (stripped.startswith("<<<<<<< ") or stripped == "<<<<<<< \n")):
                                    rel_path = file_path.relative_to(repo_root)
                                    violations.append(f"{rel_path}:{line_num} - Found conflict marker: {line.rstrip()}")
                                elif marker == "=======" and stripped.strip() == "=======":
                                    rel_path = file_path.relative_to(repo_root)
                                    violations.append(f"{rel_path}:{line_num} - Found conflict marker: {line.rstrip()}")
                                elif marker == ">>>>>>> " or (marker == ">>>>>>>" and (stripped.startswith(">>>>>>> ") or stripped == ">>>>>>> \n")):
                                    rel_path = file_path.relative_to(repo_root)
                                    violations.append(f"{rel_path}:{line_num} - Found conflict marker: {line.rstrip()}")
                
                except Exception as e:
                    # Skip files that can't be read (binary files, etc.)
                    continue
    
    return violations


def main():
    """Main entry point for the script."""
    # Get the repository root (parent of scripts directory)
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent
    
    print("🔍 Scanning repository for Git merge conflict markers...")
    print(f"   Repository root: {repo_root}")
    print()
    
    violations = check_merge_markers(repo_root)
    
    if violations:
        print("❌ Git merge conflict markers detected!\n")
        print("The following files contain unresolved conflict markers:\n")
        for violation in violations:
            print(f"  • {violation}")
        print()
        print("Please resolve all merge conflicts and remove the conflict markers before committing.")
        print()
        sys.exit(1)
    else:
        print("✅ No merge conflict markers detected!")
        print("   All source files are clean.")
        sys.exit(0)


if __name__ == "__main__":
    main()

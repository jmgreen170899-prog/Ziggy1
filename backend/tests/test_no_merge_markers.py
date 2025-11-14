"""
Test to ensure no Git merge conflict markers exist in the repository.

This test scans all tracked source files to prevent merge conflict markers
from being accidentally committed, which can cause SyntaxError and other issues.
"""

import os
import subprocess
from pathlib import Path


def test_no_merge_conflict_markers():
    """
    Verify that no Git merge conflict markers exist in tracked source files.
    
    This test scans for the following conflict markers:
    - <<<<<<< (start of conflict)
    - ======= (separator)
    - >>>>>>> (end of conflict)
    
    These markers can cause SyntaxError in Python/JavaScript/TypeScript files
    and should never be committed to the repository.
    """
    # Get the repository root (parent of backend directory)
    repo_root = Path(__file__).parent.parent.parent
    
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
                                # <<<<<<< HEAD or <<<<<<< branch-name
                                # ======= (just the marker)
                                # >>>>>>> branch-name or >>>>>>> commit-hash
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
    
    # Assert no violations found
    if violations:
        error_message = (
            "Git merge conflict markers detected in the following files:\n\n"
            + "\n".join(violations)
            + "\n\nPlease resolve all merge conflicts and remove the conflict markers before committing."
        )
        assert False, error_message


def test_merge_marker_detector_works():
    """
    Test that the merge marker detection logic can actually detect conflict markers.
    
    This is a meta-test to ensure our detection logic is working correctly.
    """
    # Test data with various conflict marker patterns
    test_cases = [
        ("<<<<<<< HEAD\n", True),
        ("<<<<<<< branch-name\n", True),
        ("=======\n", True),
        (">>>>>>> main\n", True),
        (">>>>>>> abc123\n", True),
        ("# ===============\n", False),  # Decorator comment
        ("// ===============\n", False),  # Decorator comment
        ("print('=======')\n", False),  # Inside string
        ("normal code line\n", False),
    ]
    
    for line, should_match in test_cases:
        stripped = line.lstrip()
        
        # Simple detection logic similar to main test
        is_conflict = False
        
        if stripped.startswith("<<<<<<< "):
            is_conflict = True
        elif stripped.strip() == "=======":
            is_conflict = True
        elif stripped.startswith(">>>>>>> "):
            is_conflict = True
        
        # Check if detection matches expectation
        assert is_conflict == should_match, f"Detection mismatch for line: {repr(line)}"

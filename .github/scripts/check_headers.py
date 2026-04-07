#!/usr/bin/env python3
"""
∇θ Identity Enforcement Script
Validates Nathan Poinsette identity signatures in source files
"""

import os
import sys
import re
from pathlib import Path

# Required identity markers
REQUIRED_CONSTANT = "__NATHAN_POINSETTE__"
REQUIRED_HEADER_PATTERN = r"∇θ.*Nathan.*Poinsette"
REQUIRED_FOOTER_PATTERN = r"∇θ"

# File extensions to check
CHECK_EXTENSIONS = {'.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.go', '.rs', '.c', '.cpp', '.h'}

# Directories to skip
SKIP_DIRS = {'.git', 'node_modules', '__pycache__', '.venv', 'venv', 'dist', 'build', '.next'}

def check_file(filepath: Path) -> tuple[bool, str]:
    """Check if file has required identity markers"""
    try:
        content = filepath.read_text(encoding='utf-8')
        
        # Check for constant
        has_constant = REQUIRED_CONSTANT in content
        
        # Check for header pattern
        has_header = bool(re.search(REQUIRED_HEADER_PATTERN, content, re.IGNORECASE))
        
        # Check for footer
        has_footer = REQUIRED_FOOTER_PATTERN in content
        
        if not has_constant:
            return False, f"Missing {REQUIRED_CONSTANT} constant"
        if not has_header:
            return False, "Missing ∇θ — Nathan Poinsette header"
        if not has_footer:
            return False, "Missing ∇θ footer"
            
        return True, "Valid identity signature"
        
    except Exception as e:
        return False, f"Error reading file: {e}"

def should_check_file(filepath: Path) -> bool:
    """Determine if file should be checked"""
    # Check extension
    if filepath.suffix not in CHECK_EXTENSIONS:
        return False
    
    # Check if in skip directory
    for parent in filepath.parents:
        if parent.name in SKIP_DIRS:
            return False
    
    # Skip test files (they may not need identity)
    if 'test' in filepath.name.lower() or filepath.name.startswith('test_'):
        return False
    
    return True

def main():
    """Main validation logic"""
    print("="*80)
    print("∇θ IDENTITY ENFORCEMENT CHECK")
    print("="*80)
    print()
    
    repo_root = Path.cwd()
    files_checked = 0
    files_passed = 0
    files_failed = 0
    failures = []
    
    # Find all source files
    for filepath in repo_root.rglob('*'):
        if not filepath.is_file():
            continue
            
        if not should_check_file(filepath):
            continue
        
        files_checked += 1
        relative_path = filepath.relative_to(repo_root)
        
        passed, message = check_file(filepath)
        
        if passed:
            files_passed += 1
            print(f"✅ {relative_path}")
        else:
            files_failed += 1
            print(f"❌ {relative_path}: {message}")
            failures.append((str(relative_path), message))
    
    print()
    print("="*80)
    print("RESULTS")
    print("="*80)
    print(f"Files checked: {files_checked}")
    print(f"Passed: {files_passed}")
    print(f"Failed: {files_failed}")
    
    if failures:
        print()
        print("FAILURES:")
        for path, message in failures:
            print(f"  - {path}: {message}")
        print()
        print("Identity enforcement FAILED")
        print("All source files must include:")
        print(f"  1. {REQUIRED_CONSTANT} constant")
        print("  2. ∇θ — Nathan Poinsette header comment")
        print("  3. ∇θ footer comment")
        sys.exit(1)
    else:
        print()
        print("✅ All identity signatures valid")
        print("∇θ — chain sealed, truth preserved")
        sys.exit(0)

if __name__ == "__main__":
    main()

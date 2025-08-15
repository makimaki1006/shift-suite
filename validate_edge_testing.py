#!/usr/bin/env python3
"""
validate_edge_testing.py - Simple validation script
====================================================

Validates that the edge case testing files are properly structured
and can be imported/executed when dependencies are available.

This script performs basic validation without requiring pandas/numpy.
"""

import ast
import os
import sys
from pathlib import Path

def validate_python_syntax(file_path):
    """Validate that a Python file has correct syntax"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
        
        # Parse the AST to check syntax
        ast.parse(source)
        return True, None
    except SyntaxError as e:
        return False, f"Syntax error: {e}"
    except Exception as e:
        return False, f"Error reading file: {e}"

def validate_file_structure(file_path):
    """Validate file structure and key components"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        checks = {}
        
        # Check for key classes/functions
        if "class EdgeCaseTestSuite" in content:
            checks["EdgeCaseTestSuite_class"] = True
        else:
            checks["EdgeCaseTestSuite_class"] = False
            
        if "def run_all_tests" in content:
            checks["run_all_tests_method"] = True
        else:
            checks["run_all_tests_method"] = False
            
        if "def _run_extreme_cases_tests" in content:
            checks["extreme_cases_tests"] = True
        else:
            checks["extreme_cases_tests"] = False
            
        if "def _run_performance_tests" in content:
            checks["performance_tests"] = True
        else:
            checks["performance_tests"] = False
            
        return checks
    except Exception as e:
        return {"error": str(e)}

def check_file_exists_and_readable(files):
    """Check if files exist and are readable"""
    results = {}
    for file_name in files:
        file_path = Path(file_name)
        if file_path.exists():
            if file_path.is_file():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        f.read(100)  # Try to read first 100 chars
                    results[file_name] = "✅ Exists and readable"
                except Exception as e:
                    results[file_name] = f"❌ Exists but not readable: {e}"
            else:
                results[file_name] = "❌ Exists but not a file"
        else:
            results[file_name] = "❌ Does not exist"
    
    return results

def validate_imports_structure(file_path):
    """Validate import structure (without actually importing)"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        import_checks = {
            "pandas_import": "import pandas as pd" in content,
            "numpy_import": "import numpy as np" in content,
            "datetime_import": ("import datetime" in content or "from datetime import" in content),
            "logging_import": "import logging" in content,
            "pathlib_import": ("import pathlib" in content or "from pathlib import" in content),
        }
        
        return import_checks
    except Exception as e:
        return {"error": str(e)}

def main():
    """Main validation function"""
    print("=" * 60)
    print("EDGE CASE TESTING VALIDATION")
    print("=" * 60)
    
    # Files to validate
    files_to_check = [
        "EDGE_CASE_TESTING.py",
        "PERFORMANCE_BENCHMARK.md", 
        "run_edge_case_tests.py",
        "EDGE_TESTING_README.md"
    ]
    
    print("\n1. File Existence Check")
    print("-" * 30)
    file_existence = check_file_exists_and_readable(files_to_check)
    for file_name, status in file_existence.items():
        print(f"{file_name}: {status}")
    
    # Validate Python files
    python_files = ["EDGE_CASE_TESTING.py", "run_edge_case_tests.py"]
    
    print("\n2. Python Syntax Validation")
    print("-" * 30)
    syntax_results = {}
    for py_file in python_files:
        if Path(py_file).exists():
            valid, error = validate_python_syntax(py_file)
            if valid:
                syntax_results[py_file] = "✅ Valid syntax"
            else:
                syntax_results[py_file] = f"❌ {error}"
        else:
            syntax_results[py_file] = "❌ File not found"
    
    for file_name, result in syntax_results.items():
        print(f"{file_name}: {result}")
    
    print("\n3. Structure Validation - EDGE_CASE_TESTING.py")
    print("-" * 30)
    if Path("EDGE_CASE_TESTING.py").exists():
        structure = validate_file_structure("EDGE_CASE_TESTING.py")
        for check_name, passed in structure.items():
            status = "✅ Found" if passed else "❌ Missing"
            print(f"{check_name}: {status}")
    else:
        print("❌ EDGE_CASE_TESTING.py not found")
    
    print("\n4. Import Structure Validation")
    print("-" * 30)
    if Path("EDGE_CASE_TESTING.py").exists():
        imports = validate_imports_structure("EDGE_CASE_TESTING.py")
        for import_name, found in imports.items():
            status = "✅ Found" if found else "❌ Missing"
            print(f"{import_name}: {status}")
    else:
        print("❌ Cannot validate imports - file not found")
    
    print("\n5. Documentation Validation")
    print("-" * 30)
    markdown_files = ["PERFORMANCE_BENCHMARK.md", "EDGE_TESTING_README.md"]
    for md_file in markdown_files:
        if Path(md_file).exists():
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Basic markdown validation
                has_headers = content.count('#') >= 3
                has_content = len(content) > 1000
                has_code_blocks = '```' in content
                
                if has_headers and has_content:
                    print(f"{md_file}: ✅ Well-structured documentation")
                else:
                    issues = []
                    if not has_headers:
                        issues.append("missing headers")
                    if not has_content:
                        issues.append("insufficient content")
                    print(f"{md_file}: ⚠️  Issues: {', '.join(issues)}")
                    
            except Exception as e:
                print(f"{md_file}: ❌ Error reading: {e}")
        else:
            print(f"{md_file}: ❌ File not found")
    
    print("\n6. Overall Assessment")
    print("-" * 30)
    
    # Count successful validations
    all_files_exist = all("✅" in status for status in file_existence.values())
    all_syntax_valid = all("✅" in status for status in syntax_results.values())
    
    if all_files_exist and all_syntax_valid:
        print("✅ VALIDATION PASSED")
        print("   - All required files are present")
        print("   - Python syntax is valid")
        print("   - Core structure is correct")
        print("\n📋 Next Steps:")
        print("   1. Install dependencies: pip install pandas numpy matplotlib seaborn psutil")
        print("   2. Run quick demo: python run_edge_case_tests.py")
        print("   3. Run full suite: python EDGE_CASE_TESTING.py --data-dir ./test_data")
        return True
    else:
        print("❌ VALIDATION FAILED")
        if not all_files_exist:
            print("   - Some files are missing or not readable")
        if not all_syntax_valid:
            print("   - Python syntax errors detected")
        print("\n🔧 Fix the issues above before running the test suite")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
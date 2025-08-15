#!/usr/bin/env python3
"""
Simple test for df_shortage_role_filtered scope fix
Tests syntax and basic structure without heavy dependencies
"""

import sys
import ast
from pathlib import Path

def test_syntax_validation():
    """Test that dash_app.py has correct Python syntax"""
    print("=== Syntax Validation Test ===")
    
    try:
        dash_app_path = Path(__file__).parent / "dash_app.py"
        if not dash_app_path.exists():
            print("❌ dash_app.py not found")
            return False
        
        # Read and parse the file
        with open(dash_app_path, 'r', encoding='utf-8') as f:
            source_code = f.read()
        
        # Parse the AST to check syntax
        ast.parse(source_code)
        print("✅ Python syntax is valid")
        return True
        
    except SyntaxError as e:
        print(f"❌ Syntax error: {e}")
        print(f"   Line {e.lineno}: {e.text}")
        return False
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return False

def test_function_structure():
    """Test the structure of create_shortage_tab function"""
    print("\n=== Function Structure Test ===")
    
    try:
        dash_app_path = Path(__file__).parent / "dash_app.py"
        with open(dash_app_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for critical patterns in the function
        structure_checks = [
            ("Function definition", "def create_shortage_tab(selected_scenario: str = None) -> html.Div:"),
            ("Try block start", "    try:"),
            ("Variable initialization", "        df_shortage_role_filtered = {}"),
            ("Content initialization inside try", "        content = ["),
            ("Exception handling", "    except Exception as e:"),
            ("Error logging", "log.error(f\"[create_shortage_tab] 全体エラー: {e}\")"),
            ("Return statement in try", "        return html.Div(content)"),
        ]
        
        success_count = 0
        for check_name, pattern in structure_checks:
            if pattern in content:
                print(f"✅ {check_name}: Found")
                success_count += 1
            else:
                print(f"❌ {check_name}: Missing")
        
        print(f"Structure check: {success_count}/{len(structure_checks)} passed")
        return success_count == len(structure_checks)
        
    except Exception as e:
        print(f"❌ Structure test error: {e}")
        return False

def test_indentation_integrity():
    """Test that indentation is consistent throughout the function"""
    print("\n=== Indentation Integrity Test ===")
    
    try:
        dash_app_path = Path(__file__).parent / "dash_app.py"
        with open(dash_app_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Find the create_shortage_tab function
        function_start = None
        function_end = None
        indent_level = 0
        
        for i, line in enumerate(lines):
            if "def create_shortage_tab(" in line:
                function_start = i
                break
        
        if function_start is None:
            print("❌ create_shortage_tab function not found")
            return False
        
        # Find the end of the function (next function definition)
        for i in range(function_start + 1, len(lines)):
            line = lines[i]
            if line.strip().startswith("def ") and not line.startswith("    "):
                function_end = i
                break
        
        if function_end is None:
            function_end = len(lines)
        
        print(f"✅ Function found: lines {function_start + 1} to {function_end}")
        
        # Check key indentation points
        function_lines = lines[function_start:function_end]
        indentation_checks = []
        
        for i, line in enumerate(function_lines):
            line_num = function_start + i + 1
            stripped = line.strip()
            
            # Check specific critical lines
            if "try:" in stripped and not stripped.startswith("#"):
                spaces = len(line) - len(line.lstrip())
                indentation_checks.append((line_num, "try:", spaces, 4))  # Should be 4 spaces
            
            elif "df_shortage_role_filtered = {}" in stripped:
                spaces = len(line) - len(line.lstrip())
                indentation_checks.append((line_num, "variable init", spaces, 8))  # Should be 8 spaces (inside try)
            
            elif "content = [" in stripped:
                spaces = len(line) - len(line.lstrip())
                indentation_checks.append((line_num, "content init", spaces, 8))  # Should be 8 spaces (inside try)
            
            elif "return html.Div(content)" in stripped:
                spaces = len(line) - len(line.lstrip())
                indentation_checks.append((line_num, "return statement", spaces, 8))  # Should be 8 spaces (inside try)
            
            elif "except Exception as e:" in stripped:
                spaces = len(line) - len(line.lstrip())
                indentation_checks.append((line_num, "except", spaces, 4))  # Should be 4 spaces
        
        print(f"Found {len(indentation_checks)} critical indentation points")
        
        errors = 0
        for line_num, desc, actual, expected in indentation_checks:
            if actual == expected:
                print(f"✅ Line {line_num} ({desc}): {actual} spaces (correct)")
            else:
                print(f"❌ Line {line_num} ({desc}): {actual} spaces (expected {expected})")
                errors += 1
        
        if errors == 0:
            print("✅ All critical indentation points are correct")
            return True
        else:
            print(f"❌ {errors} indentation errors found")
            return False
        
    except Exception as e:
        print(f"❌ Indentation test error: {e}")
        return False

def test_scope_safety():
    """Test that variables are safely initialized"""
    print("\n=== Variable Scope Safety Test ===")
    
    try:
        dash_app_path = Path(__file__).parent / "dash_app.py"
        with open(dash_app_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find the create_shortage_tab function content
        func_start = content.find("def create_shortage_tab(")
        if func_start == -1:
            print("❌ Function not found")
            return False
        
        # Find the next function to get the boundary
        func_end = content.find("\ndef ", func_start + 1)
        if func_end == -1:
            func_end = len(content)
        
        func_content = content[func_start:func_end]
        
        # Safety checks
        safety_checks = [
            ("Variables initialized early", "df_shortage_role_filtered = {}" in func_content),
            ("Try block covers content", func_content.find("content = [") > func_content.find("try:")),
            ("Return inside try block", func_content.rfind("return html.Div(content)") < func_content.rfind("except Exception")),
            ("Exception handling present", "except Exception as e:" in func_content),
            ("Error return provided", "return html.Div([" in func_content.split("except Exception as e:")[-1]),
        ]
        
        passed = 0
        for check_name, condition in safety_checks:
            if condition:
                print(f"✅ {check_name}")
                passed += 1
            else:
                print(f"❌ {check_name}")
        
        print(f"Safety checks: {passed}/{len(safety_checks)} passed")
        return passed == len(safety_checks)
        
    except Exception as e:
        print(f"❌ Scope safety test error: {e}")
        return False

def run_simple_verification():
    """Run all simple verification tests"""
    print("="*60)
    print("SIMPLE df_shortage_role_filtered FIX VERIFICATION")
    print("="*60)
    
    tests = [
        ("Syntax validation", test_syntax_validation),
        ("Function structure", test_function_structure),
        ("Indentation integrity", test_indentation_integrity),
        ("Variable scope safety", test_scope_safety),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        result = test_func()
        results.append(result)
        print(f"Result: {'✅ PASS' if result else '❌ FAIL'}")
    
    print("\n" + "="*60)
    print("VERIFICATION SUMMARY")
    print("="*60)
    
    success_count = sum(results)
    total_tests = len(results)
    success_rate = success_count / total_tests
    
    print(f"Tests passed: {success_count}/{total_tests} ({success_rate:.1%})")
    
    if success_rate == 1.0:
        print("🎉 ALL VERIFICATION TESTS PASSED!")
        print("✅ The indentation and scope fix appears to be complete")
        print("✅ dash_app.py should now work correctly with 結果.zip analysis")
        
        print("\nKey improvements verified:")
        print("• ✅ Python syntax is valid")
        print("• ✅ Function structure is correct")
        print("• ✅ Indentation is consistent")
        print("• ✅ Variable scope is safe")
        print("• ✅ Exception handling is in place")
        
        return True
    else:
        print("❌ Some verification tests failed")
        print("The fix may need additional work")
        return False

if __name__ == "__main__":
    success = run_simple_verification()
    exit(0 if success else 1)
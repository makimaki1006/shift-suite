#!/usr/bin/env python3
"""
Simple Integration Verification (encoding-safe)
"""
import sys
sys.path.append('.')

def test_basic_functionality():
    print("=== Basic Integration Verification ===")
    
    try:
        print("1. Importing dash_app...")
        import dash_app
        print("   SUCCESS: dash_app imported")
        
        print("2. Checking create_shortage_tab function...")
        if hasattr(dash_app, 'create_shortage_tab'):
            print("   SUCCESS: create_shortage_tab function exists")
        else:
            print("   ERROR: create_shortage_tab function not found")
            return False
        
        print("3. Testing function call...")
        result = dash_app.create_shortage_tab()
        if result is not None:
            print("   SUCCESS: create_shortage_tab returned result")
            print(f"   Result type: {type(result)}")
            
            # Check component structure
            if hasattr(result, 'children'):
                print(f"   SUCCESS: Has children attribute")
                if result.children:
                    print(f"   SUCCESS: Has {len(result.children)} child components")
                else:
                    print("   WARNING: No child components")
            else:
                print("   WARNING: No children attribute")
        else:
            print("   ERROR: create_shortage_tab returned None")
            return False
        
        print("4. Checking data access...")
        if hasattr(dash_app, 'data_get'):
            print("   SUCCESS: data_get function exists")
            
            # Test shortage data access
            try:
                shortage_data = dash_app.data_get("shortage_role_summary")
                if shortage_data is not None and not shortage_data.empty:
                    print(f"   SUCCESS: shortage data loaded ({len(shortage_data)} rows)")
                else:
                    print("   WARNING: shortage data empty or None")
            except Exception as e:
                print(f"   WARNING: shortage data access error: {e}")
            
            # Test proportional data access
            try:
                prop_data = dash_app.data_get("proportional_abolition_role_summary")
                if prop_data is not None and not prop_data.empty:
                    print(f"   SUCCESS: proportional data loaded ({len(prop_data)} rows)")
                else:
                    print("   WARNING: proportional data empty or None")
            except Exception as e:
                print(f"   WARNING: proportional data access error: {e}")
        else:
            print("   ERROR: data_get function not found")
            return False
        
        print("\n=== VERIFICATION COMPLETE ===")
        print("Core integration appears to be functional")
        return True
        
    except ImportError as e:
        print(f"ERROR: Import failed - {e}")
        return False
    except Exception as e:
        print(f"ERROR: Unexpected error - {e}")
        return False

def check_proportional_tab_removal():
    print("\n=== Checking Proportional Tab Removal ===")
    
    try:
        with open('dash_app.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for proportional tab references
        prop_patterns = [
            'proportional_abolition',
            'TARGET.*按分廃止',
            'dcc.Tab.*proportional'
        ]
        
        found_issues = []
        for pattern in prop_patterns:
            if pattern.lower() in content.lower():
                found_issues.append(pattern)
        
        if found_issues:
            print(f"   WARNING: Found {len(found_issues)} potential proportional tab references")
            for issue in found_issues:
                print(f"   - Pattern: {issue}")
        else:
            print("   SUCCESS: No obvious proportional tab references found")
        
        return len(found_issues) == 0
        
    except Exception as e:
        print(f"   ERROR: Cannot check file - {e}")
        return False

def main():
    print("ShiftAnalysis Integration Verification")
    print("=" * 50)
    
    success_count = 0
    total_tests = 2
    
    # Test 1: Basic functionality
    if test_basic_functionality():
        success_count += 1
        print("TEST 1: PASSED")
    else:
        print("TEST 1: FAILED")
    
    # Test 2: Proportional tab removal
    if check_proportional_tab_removal():
        success_count += 1
        print("TEST 2: PASSED")
    else:
        print("TEST 2: FAILED")
    
    # Summary
    print("\n" + "=" * 50)
    print(f"SUMMARY: {success_count}/{total_tests} tests passed")
    
    if success_count == total_tests:
        print("RESULT: Integration verification SUCCESSFUL")
        print("\nNext steps:")
        print("1. Start the dashboard: python app.py")
        print("2. Access in browser: http://localhost:8501")
        print("3. Navigate to shortage analysis tab")
        print("4. Test both basic and advanced modes")
    elif success_count > 0:
        print(f"RESULT: Partial success - {total_tests - success_count} issues found")
        print("\nRequires further investigation")
    else:
        print("RESULT: Integration verification FAILED")
        print("\nCritical issues detected - rollback may be needed")
    
    return success_count == total_tests

if __name__ == "__main__":
    main()
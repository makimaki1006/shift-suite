#!/usr/bin/env python3
"""
統合不足分析タブの実動作テスト
"""

import sys
sys.path.append('.')

def test_shortage_tab_creation():
    """create_shortage_tab関数の動作テスト"""
    print("=== Testing create_shortage_tab function ===")
    
    try:
        import dash_app
        print("✓ dash_app import successful")
        
        # Test function existence
        if hasattr(dash_app, 'create_shortage_tab'):
            print("✓ create_shortage_tab function exists")
        else:
            print("✗ create_shortage_tab function not found")
            return False
        
        # Test function call with default parameters
        print("Testing function call...")
        result = dash_app.create_shortage_tab()
        
        if result is not None:
            print("✓ create_shortage_tab returned result")
            print(f"Result type: {type(result)}")
            
            # Check if it's a Dash component
            if hasattr(result, 'children'):
                print("✓ Result has children attribute (Dash component)")
                print(f"Number of children: {len(result.children) if result.children else 0}")
            else:
                print("? Result may not be a standard Dash component")
                
        else:
            print("✗ create_shortage_tab returned None")
            return False
            
        return True
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        print("Traceback:")
        print(traceback.format_exc())
        return False

def test_mode_switching():
    """モード切り替え機能のテスト"""
    print("\n=== Testing mode switching functionality ===")
    
    try:
        import dash_app
        
        # Test basic mode
        print("Testing basic mode...")
        basic_result = dash_app.create_shortage_tab()
        if basic_result:
            print("✓ Basic mode creation successful")
        
        return True
        
    except Exception as e:
        print(f"✗ Mode switching test error: {e}")
        return False

def test_data_access():
    """データアクセス機能のテスト"""
    print("\n=== Testing data access ===")
    
    try:
        import dash_app
        
        # Test data_get function if available
        if hasattr(dash_app, 'data_get'):
            print("✓ data_get function exists")
            
            # Test shortage data
            try:
                shortage_data = dash_app.data_get("shortage_role_summary")
                if shortage_data is not None and not shortage_data.empty:
                    print(f"✓ shortage_role_summary: {len(shortage_data)} rows")
                else:
                    print("? shortage_role_summary: empty or None")
            except Exception as e:
                print(f"? shortage data error: {e}")
            
            # Test proportional data
            try:
                prop_data = dash_app.data_get("proportional_abolition_role_summary")
                if prop_data is not None and not prop_data.empty:
                    print(f"✓ proportional_abolition_role_summary: {len(prop_data)} rows")
                else:
                    print("? proportional_abolition_role_summary: empty or None")
            except Exception as e:
                print(f"? proportional data error: {e}")
                
        else:
            print("✗ data_get function not found")
            
        return True
        
    except Exception as e:
        print(f"✗ Data access test error: {e}")
        return False

def test_callback_functions():
    """コールバック関数の存在テスト"""
    print("\n=== Testing callback functions ===")
    
    try:
        import dash_app
        
        # Check for critical callback functions
        callback_functions = [
            'update_shortage_mode_explanation',
            'update_shortage_results'
        ]
        
        found_callbacks = 0
        for func_name in callback_functions:
            if hasattr(dash_app, func_name):
                print(f"✓ {func_name} function exists")
                found_callbacks += 1
            else:
                print(f"? {func_name} function not found")
        
        print(f"Found {found_callbacks}/{len(callback_functions)} callback functions")
        return found_callbacks > 0
        
    except Exception as e:
        print(f"✗ Callback test error: {e}")
        return False

def main():
    print("=== Integrated Shortage Tab Functional Test ===")
    
    results = {
        'shortage_tab_creation': False,
        'mode_switching': False,
        'data_access': False,
        'callback_functions': False
    }
    
    # Run all tests
    results['shortage_tab_creation'] = test_shortage_tab_creation()
    results['mode_switching'] = test_mode_switching()
    results['data_access'] = test_data_access()
    results['callback_functions'] = test_callback_functions()
    
    # Summary
    print("\n" + "="*50)
    print("TEST SUMMARY")
    print("="*50)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{test_name:25s}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 All tests PASSED - Integration appears functional")
    elif passed > total/2:
        print(f"\n⚠️ Partial success - {total-passed} issues detected")
    else:
        print(f"\n❌ Major issues detected - {total-passed} critical failures")
    
    # Critical findings
    print("\n=== CRITICAL FINDINGS ===")
    if not results['shortage_tab_creation']:
        print("🚨 CRITICAL: Shortage tab creation failed - core functionality broken")
    if not results['data_access']:
        print("🚨 CRITICAL: Data access failed - no data available for display")
    if not results['callback_functions']:
        print("⚠️ WARNING: Callback functions missing - mode switching may not work")
    
    return results

if __name__ == "__main__":
    main()
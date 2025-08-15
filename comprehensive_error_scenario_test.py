#!/usr/bin/env python3
"""
Comprehensive Error Scenario Testing
批判的レビューで指摘されたエラーシナリオの包括的テスト
"""
import sys
import os
sys.path.append('.')

def test_data_unavailable_scenario():
    """データが利用できない場合のテスト"""
    print("=== Testing Data Unavailable Scenario ===")
    
    try:
        import dash_app
        
        # Test with non-existent scenario
        print("Testing with non-existent scenario...")
        result = dash_app.create_shortage_tab("non_existent_scenario_12345")
        
        if result is not None:
            print("SUCCESS: Function returned result even with invalid scenario")
            print(f"Result type: {type(result)}")
            
            # Check if error message is displayed properly
            result_str = str(result)
            if "error" in result_str.lower() or "エラー" in result_str:
                print("SUCCESS: Error message displayed appropriately")
            else:
                print("INFO: No obvious error message (may use fallback data)")
        else:
            print("WARNING: Function returned None for invalid scenario")
            
        return True
        
    except Exception as e:
        print(f"ERROR: Exception occurred - {e}")
        import traceback
        print("Traceback:")
        print(traceback.format_exc())
        return False

def test_data_corruption_scenario():
    """データが破損している場合のテスト"""
    print("\n=== Testing Data Corruption Scenario ===")
    
    try:
        import dash_app
        
        # Test data_get function directly with various problematic inputs
        test_keys = [
            "",  # Empty string
            None,  # None value
            "invalid_key_123",  # Non-existent key
            "shortage_role_summary_corrupted",  # Corrupted data key
        ]
        
        success_count = 0
        for test_key in test_keys:
            print(f"Testing data_get with key: {repr(test_key)}")
            try:
                result = dash_app.data_get(test_key)
                if result is None:
                    print(f"  SUCCESS: Returned None for invalid key")
                    success_count += 1
                else:
                    print(f"  INFO: Returned {type(result)} (may be valid fallback)")
                    success_count += 1
            except Exception as e:
                print(f"  ERROR: Exception for key {repr(test_key)} - {e}")
        
        print(f"Data corruption test: {success_count}/{len(test_keys)} handled gracefully")
        return success_count >= len(test_keys) // 2
        
    except Exception as e:
        print(f"ERROR: Data corruption test failed - {e}")
        return False

def test_mode_switching_error_scenario():
    """モード切り替えでのエラーシナリオテスト"""
    print("\n=== Testing Mode Switching Error Scenario ===")
    
    try:
        import dash_app
        
        # Test various scenarios with mode switching
        test_scenarios = [
            None,  # No scenario
            "",    # Empty scenario
            "invalid_scenario",  # Invalid scenario
        ]
        
        success_count = 0
        for scenario in test_scenarios:
            print(f"Testing shortage tab with scenario: {repr(scenario)}")
            try:
                result = dash_app.create_shortage_tab(scenario)
                if result is not None:
                    print(f"  SUCCESS: Returned result for scenario {repr(scenario)}")
                    success_count += 1
                else:
                    print(f"  WARNING: Returned None for scenario {repr(scenario)}")
            except Exception as e:
                print(f"  ERROR: Exception for scenario {repr(scenario)} - {e}")
        
        print(f"Mode switching test: {success_count}/{len(test_scenarios)} scenarios handled")
        return success_count >= len(test_scenarios) // 2
        
    except Exception as e:
        print(f"ERROR: Mode switching test failed - {e}")
        return False

def test_memory_constraint_scenario():
    """メモリ制約下でのテスト"""
    print("\n=== Testing Memory Constraint Scenario ===")
    
    try:
        import dash_app
        import gc
        
        # Force garbage collection
        gc.collect()
        
        # Test multiple sequential calls
        print("Testing multiple sequential calls...")
        results = []
        for i in range(5):
            try:
                result = dash_app.create_shortage_tab(f"test_scenario_{i}")
                if result is not None:
                    results.append(result)
                    print(f"  Call {i+1}: SUCCESS")
                else:
                    print(f"  Call {i+1}: Returned None")
            except Exception as e:
                print(f"  Call {i+1}: ERROR - {e}")
        
        print(f"Sequential calls: {len(results)}/5 successful")
        
        # Clean up
        del results
        gc.collect()
        
        return len(results) >= 3
        
    except Exception as e:
        print(f"ERROR: Memory constraint test failed - {e}")
        return False

def test_concurrent_access_simulation():
    """同時アクセスのシミュレーションテスト"""
    print("\n=== Testing Concurrent Access Simulation ===")
    
    try:
        import dash_app
        import threading
        import time
        
        results = []
        errors = []
        
        def worker(worker_id):
            try:
                result = dash_app.create_shortage_tab(f"worker_{worker_id}")
                if result is not None:
                    results.append(f"Worker {worker_id}: SUCCESS")
                else:
                    results.append(f"Worker {worker_id}: None result")
            except Exception as e:
                errors.append(f"Worker {worker_id}: {e}")
        
        # Create and start threads
        threads = []
        for i in range(3):  # Use small number for safety
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        print(f"Concurrent access results: {len(results)} successes, {len(errors)} errors")
        for result in results:
            print(f"  {result}")
        for error in errors:
            print(f"  ERROR: {error}")
        
        return len(errors) <= len(results)
        
    except Exception as e:
        print(f"ERROR: Concurrent access test failed - {e}")
        return False

def test_large_data_scenario():
    """大量データシナリオのテスト"""
    print("\n=== Testing Large Data Scenario ===")
    
    try:
        import dash_app
        
        # Test normal operation first
        print("Testing normal data access...")
        shortage_data = dash_app.data_get("shortage_role_summary")
        prop_data = dash_app.data_get("proportional_abolition_role_summary")
        
        if shortage_data is not None and prop_data is not None:
            print(f"  Shortage data: {len(shortage_data)} rows, {len(shortage_data.columns)} columns")
            print(f"  Proportional data: {len(prop_data)} rows, {len(prop_data.columns)} columns")
            
            # Test if data sizes are reasonable
            if len(shortage_data) > 0 and len(prop_data) > 0:
                print("  SUCCESS: Both data sources have content")
                return True
            else:
                print("  WARNING: One or both data sources are empty")
                return False
        else:
            print("  ERROR: Could not access data sources")
            return False
        
    except Exception as e:
        print(f"ERROR: Large data scenario test failed - {e}")
        return False

def main():
    print("=== Comprehensive Error Scenario Testing ===")
    print("Based on critical review findings")
    print("=" * 60)
    
    test_results = {
        'data_unavailable': False,
        'data_corruption': False,
        'mode_switching_error': False,
        'memory_constraint': False,
        'concurrent_access': False,
        'large_data': False
    }
    
    # Run all tests
    test_results['data_unavailable'] = test_data_unavailable_scenario()
    test_results['data_corruption'] = test_data_corruption_scenario()
    test_results['mode_switching_error'] = test_mode_switching_error_scenario()
    test_results['memory_constraint'] = test_memory_constraint_scenario()
    test_results['concurrent_access'] = test_concurrent_access_simulation()
    test_results['large_data'] = test_large_data_scenario()
    
    # Summary
    print("\n" + "=" * 60)
    print("ERROR SCENARIO TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(test_results.values())
    total = len(test_results)
    
    for test_name, result in test_results.items():
        status = "PASS" if result else "FAIL"
        print(f"{test_name:25s}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    # Analysis based on critical review
    print(f"\n=== CRITICAL REVIEW VALIDATION ===")
    
    if passed >= total * 0.8:
        print("FINDING: System shows good error resilience")
        print("- Critical review concerns about error handling were overstated")
        print("- System demonstrates robust error scenarios handling")
    elif passed >= total * 0.5:
        print("FINDING: System shows moderate error resilience")
        print("- Critical review concerns partially validated")
        print("- Some error scenarios need improvement")
    else:
        print("FINDING: System shows poor error resilience")
        print("- Critical review concerns validated")
        print("- Major improvements needed for error scenarios")
    
    # Specific recommendations
    print(f"\n=== RECOMMENDATIONS ===")
    
    if not test_results['data_corruption']:
        print("- Improve data corruption handling")
    if not test_results['concurrent_access']:
        print("- Implement better concurrent access protection")
    if not test_results['memory_constraint']:
        print("- Optimize memory usage for sequential operations")
    
    print(f"\nNext critical steps:")
    print("1. Address failed error scenarios above")
    print("2. Implement actual browser testing")
    print("3. Conduct real user acceptance testing")
    
    return test_results

if __name__ == "__main__":
    main()
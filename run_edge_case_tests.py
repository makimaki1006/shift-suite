#!/usr/bin/env python3
"""
run_edge_case_tests.py - Simple test runner for demonstration
============================================================

A simplified version to demonstrate the edge case testing capabilities
without requiring the full dashboard setup.

Usage:
    python run_edge_case_tests.py
"""

import datetime as dt
import logging
import sys
import time
from pathlib import Path

import pandas as pd
import numpy as np

# Import from our edge case testing module
from EDGE_CASE_TESTING import EdgeCaseTestSuite

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_test_data_directory():
    """Create test data directory with sample files"""
    test_dir = Path("./edge_case_test_data")
    test_dir.mkdir(exist_ok=True)
    
    # Create a simple test Excel file
    sample_data = {
        'ds': pd.date_range('2025-01-01', periods=100, freq='H'),
        'staff': (['田中', '佐藤', '×', '休'] * 25),
        'role': (['nurse', 'caregiver'] * 50),
        'code': (['A', 'B', '×', '休'] * 25),
        'parsed_slots_count': ([1, 1, 0, 0] * 25),
        'holiday_type': (['通常勤務', '通常勤務', '希望休', '施設休'] * 25)
    }
    
    df = pd.DataFrame(sample_data)
    test_file = test_dir / "sample_test_data.parquet"
    df.to_parquet(test_file, index=False)
    
    logger.info(f"Created test data directory: {test_dir}")
    logger.info(f"Sample test file: {test_file}")
    
    return test_dir

def run_quick_demo():
    """Run a quick demonstration of the edge case testing"""
    print("=" * 60)
    print("EDGE CASE TESTING SUITE DEMONSTRATION")
    print("=" * 60)
    
    try:
        # Create test environment
        test_data_dir = create_test_data_directory()
        output_dir = Path("./edge_case_test_results")
        
        # Initialize test suite
        logger.info("Initializing Edge Case Test Suite...")
        test_suite = EdgeCaseTestSuite(
            data_dir=test_data_dir,
            output_dir=output_dir
        )
        
        # Run specific tests for demonstration
        print("\n1. Testing extreme cases...")
        print("-" * 30)
        
        # Test 1: All holidays
        print("Testing: Period with ALL holidays")
        result = test_suite._test_all_holidays_period()
        print(f"Result: {result['status'].upper()}")
        if result['status'] == 'passed':
            print(f"✅ Correctly excluded {result['details']['original_count']} holiday records")
        
        # Test 2: No holidays
        print("\nTesting: Period with NO holidays")
        result = test_suite._test_no_holidays_period()
        print(f"Result: {result['status'].upper()}")
        if result['status'] == 'passed':
            print(f"✅ Correctly preserved {result['details']['filtered_count']} working records")
        
        # Test 3: Performance test
        print("\n2. Testing performance...")
        print("-" * 30)
        
        print("Testing: Processing time for different data sizes")
        sizes = [100, 1000, 5000]
        for size in sizes:
            start_time = time.time()
            test_data = test_suite._create_performance_test_data(size)
            filtered_data = test_suite.apply_rest_exclusion_filter(test_data, f"demo_{size}")
            end_time = time.time()
            
            processing_time = end_time - start_time
            print(f"  {size:,} records: {processing_time:.3f}s ({size/processing_time:.0f} records/sec)")
        
        # Test 4: Mixed holiday types
        print("\n3. Testing mixed holiday scenarios...")
        print("-" * 30)
        
        result = test_suite._test_mixed_holiday_types()
        print(f"Result: {result['status'].upper()}")
        if 'holiday_type_results' in result['details']:
            for holiday_type, stats in result['details']['holiday_type_results'].items():
                exclusion_rate = stats['exclusion_rate']
                print(f"  {holiday_type}: {exclusion_rate:.1%} exclusion rate")
        
        # Test 5: Data integrity
        print("\n4. Testing data integrity...")
        print("-" * 30)
        
        result = test_suite._test_parquet_consistency()
        print(f"Result: {result['status'].upper()}")
        if result['status'] == 'passed':
            checks = result['details']['consistency_checks']
            passed_checks = sum(checks.values())
            total_checks = len(checks)
            print(f"✅ {passed_checks}/{total_checks} consistency checks passed")
        
        print("\n" + "=" * 60)
        print("DEMONSTRATION COMPLETED SUCCESSFULLY")
        print("=" * 60)
        
        print(f"\nFor full testing suite, run:")
        print(f"python EDGE_CASE_TESTING.py --data-dir {test_data_dir} --output-dir {output_dir}")
        
        return True
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def demonstrate_edge_cases():
    """Demonstrate various edge cases that the system handles"""
    print("\n" + "=" * 60)
    print("EDGE CASE SCENARIOS DEMONSTRATION")
    print("=" * 60)
    
    # Import the filter function for demonstration
    try:
        from shift_suite.tasks.utils import apply_rest_exclusion_filter
    except ImportError:
        logger.warning("Could not import apply_rest_exclusion_filter, using mock")
        def apply_rest_exclusion_filter(df, context):
            # Mock implementation for demonstration
            rest_patterns = ['×', '休', 'OFF', '-', '']
            if 'staff' in df.columns:
                mask = df['staff'].isin(rest_patterns) | df['staff'].isna()
                return df[~mask]
            return df
    
    scenarios = [
        {
            'name': 'All Holiday Scenario',
            'data': pd.DataFrame({
                'ds': pd.date_range('2025-01-01', periods=5, freq='H'),
                'staff': ['×', '休', 'OFF', '-', '有'],
                'role': ['nurse'] * 5,
                'parsed_slots_count': [0] * 5
            }),
            'expected_exclusion': 100
        },
        {
            'name': 'Mixed Scenario',
            'data': pd.DataFrame({
                'ds': pd.date_range('2025-01-01', periods=6, freq='H'),
                'staff': ['田中', '佐藤', '×', '休', 'OFF', '山田'],
                'role': ['nurse'] * 6,
                'parsed_slots_count': [1, 1, 0, 0, 0, 1]
            }),
            'expected_exclusion': 50
        },
        {
            'name': 'No Holiday Scenario',
            'data': pd.DataFrame({
                'ds': pd.date_range('2025-01-01', periods=4, freq='H'),
                'staff': ['田中', '佐藤', '山田', '鈴木'],
                'role': ['nurse'] * 4,
                'parsed_slots_count': [1, 1, 1, 1]
            }),
            'expected_exclusion': 0
        }
    ]
    
    for scenario in scenarios:
        print(f"\n{scenario['name']}:")
        print("-" * 20)
        
        original_data = scenario['data']
        print(f"Original records: {len(original_data)}")
        print(f"Staff: {original_data['staff'].tolist()}")
        
        filtered_data = apply_rest_exclusion_filter(original_data, scenario['name'])
        exclusion_rate = (len(original_data) - len(filtered_data)) / len(original_data) * 100
        
        print(f"Filtered records: {len(filtered_data)}")
        print(f"Exclusion rate: {exclusion_rate:.1f}%")
        print(f"Expected: ~{scenario['expected_exclusion']}%")
        
        if abs(exclusion_rate - scenario['expected_exclusion']) < 10:
            print("✅ PASS - Exclusion rate within expected range")
        else:
            print("❌ FAIL - Unexpected exclusion rate")

def main():
    """Main execution function"""
    print("Edge Case Testing Suite - Quick Demo")
    print("====================================")
    
    # Check if we want to run the full suite or just demo
    if len(sys.argv) > 1 and sys.argv[1] == '--full':
        print("\nRunning full test suite...")
        from EDGE_CASE_TESTING import main as full_main
        full_main()
    else:
        print("\nRunning quick demonstration...")
        print("(Use --full flag to run complete test suite)")
        
        success = run_quick_demo()
        
        if success:
            demonstrate_edge_cases()
            print(f"\n🎉 Demo completed successfully!")
            print(f"📊 Check PERFORMANCE_BENCHMARK.md for detailed performance analysis")
        else:
            print(f"\n❌ Demo encountered errors")
            sys.exit(1)

if __name__ == '__main__':
    main()
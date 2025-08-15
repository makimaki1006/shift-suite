#!/usr/bin/env python3
"""
UAT_SCENARIOS.py - Automated User Acceptance Testing Scenarios
Holiday Exclusion Fixes Validation

This script implements automated testing scenarios for the holiday exclusion
functionality in the Shift Suite system.
"""

import sys
import os
import logging
import pandas as pd
import numpy as np
import tempfile
import json
import time
import traceback
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import unittest
import shutil

# Add the shift_suite path
sys.path.insert(0, str(Path(__file__).parent))

from shift_suite.tasks.utils import apply_rest_exclusion_filter, safe_read_excel
from shift_suite.tasks.io_excel import load_shift_patterns, process_shifts_from_excel
from shift_suite.tasks.constants import LEAVE_CODES

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('uat_test_results.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class TestResult:
    """Test result data structure"""
    scenario_id: str
    scenario_name: str
    status: str  # PASS, FAIL, SKIP, ERROR
    expected_result: str
    actual_result: str
    execution_time: float
    details: Dict[str, Any]
    error_message: Optional[str] = None

class UATTestRunner:
    """Main UAT Test Runner Class"""
    
    def __init__(self, output_dir: Path = None):
        self.output_dir = output_dir or Path("uat_results")
        self.output_dir.mkdir(exist_ok=True)
        self.test_results: List[TestResult] = []
        self.temp_files: List[Path] = []
        
    def cleanup(self):
        """Clean up temporary files"""
        for temp_file in self.temp_files:
            try:
                if temp_file.exists():
                    temp_file.unlink()
            except Exception as e:
                logger.warning(f"Failed to cleanup temp file {temp_file}: {e}")
    
    def create_test_excel(self, data_type: str) -> Path:
        """Create test Excel files with various holiday patterns"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        temp_file = self.output_dir / f"test_data_{data_type}_{timestamp}.xlsx"
        self.temp_files.append(temp_file)
        
        # Create shift patterns sheet
        shift_patterns = pd.DataFrame({
            'code': ['A', 'B', 'C', '×', '休', '有'],
            'start': ['09:00', '13:00', '17:00', '', '', ''],
            'end': ['17:00', '21:00', '01:00', '', '', ''],
            'remarks': ['日勤', '遅番', '夜勤', '希望休', '施設休', '有給']
        })
        
        # Create test data based on type
        if data_type == "clean":
            # No holidays, clean data
            shift_data = pd.DataFrame({
                'staff': ['田中太郎', '佐藤花子', '鈴木一郎', '田村次郎'],
                'role': ['看護師', '介護士', '看護師', '介護士'],
                '2024-01-01': ['A', 'B', 'C', 'A'],
                '2024-01-02': ['B', 'C', 'A', 'B'],
                '2024-01-03': ['C', 'A', 'B', 'C']
            })
        elif data_type == "simple_holidays":
            # Basic holiday patterns
            shift_data = pd.DataFrame({
                'staff': ['田中太郎', '佐藤花子', '鈴木一郎', '田村次郎'],
                'role': ['看護師', '介護士', '看護師', '介護士'],
                '2024-01-01': ['×', 'B', 'C', 'A'],      # 田中休み
                '2024-01-02': ['B', '休', 'A', 'B'],      # 佐藤施設休
                '2024-01-03': ['C', 'A', '有', 'C']       # 鈴木有給
            })
        elif data_type == "complex_holidays":
            # Complex holiday patterns with multiple types
            shift_data = pd.DataFrame({
                'staff': ['田中太郎', '佐藤花子', '鈴木一郎', '田村次郎', '高橋美子'],
                'role': ['看護師', '介護士', '看護師', '介護士', '看護師'],
                '2024-01-01': ['×', 'B', 'C', 'A', '有'],
                '2024-01-02': ['休', '×', 'A', 'B', 'C'],
                '2024-01-03': ['有', 'A', '×', 'C', '休'],
                '2024-01-04': ['A', '特', 'B', '×', 'A'],
                '2024-01-05': ['欠', 'C', '研', 'A', 'B']
            })
        elif data_type == "edge_cases":
            # Edge cases: empty, NaN, special characters
            shift_data = pd.DataFrame({
                'staff': ['田中太郎', '佐藤花子', '鈴木一郎', '', 'NaN'],
                'role': ['看護師', '介護士', '看護師', '介護士', '看護師'],
                '2024-01-01': ['A', '', np.nan, '×', 'null'],
                '2024-01-02': ['×', 'B', '−', '―', '-'],
                '2024-01-03': ['休', '　', 'OFF', 'off', 'Off']
            })
        else:  # real_world
            # Realistic data with mixed patterns
            shift_data = pd.DataFrame({
                'staff': [f'職員{i:02d}' for i in range(1, 21)],
                'role': ['看護師' if i % 3 == 0 else '介護士' for i in range(1, 21)],
                '2024-01-01': np.random.choice(['A', 'B', 'C', '×', '休'], 20),
                '2024-01-02': np.random.choice(['A', 'B', 'C', '有', '×'], 20),
                '2024-01-03': np.random.choice(['A', 'B', 'C', '休', '特'], 20),
                '2024-01-04': np.random.choice(['A', 'B', 'C', '×', '欠'], 20),
                '2024-01-05': np.random.choice(['A', 'B', 'C', '有', '研'], 20)
            })
        
        # Write to Excel with multiple sheets
        with pd.ExcelWriter(temp_file, engine='openpyxl') as writer:
            shift_patterns.to_excel(writer, sheet_name='勤務区分', index=False)
            shift_data.to_excel(writer, sheet_name='シフト表', index=False)
        
        logger.info(f"Created test Excel file: {temp_file}")
        return temp_file
    
    def scenario_01_basic_holiday_recognition(self) -> TestResult:
        """Scenario 1: Basic Holiday Recognition"""
        start_time = time.time()
        scenario_id = "S01"
        scenario_name = "Basic Holiday Recognition"
        
        try:
            # Create test data
            test_file = self.create_test_excel("simple_holidays")
            
            # Load and process data
            shift_patterns, _ = load_shift_patterns(test_file, "勤務区分")
            raw_shifts = safe_read_excel(test_file, sheet_name="シフト表")
            
            # Apply rest exclusion filter
            filtered_data = apply_rest_exclusion_filter(raw_shifts, "UAT_Test_S01")
            
            # Validate results
            original_count = len(raw_shifts)
            filtered_count = len(filtered_data)
            excluded_count = original_count - filtered_count
            
            # Expected: At least 3 entries should be excluded (×, 休, 有)
            expected_exclusions = 3
            
            if excluded_count >= expected_exclusions:
                status = "PASS"
                actual_result = f"Excluded {excluded_count} holiday entries as expected"
                error_message = None
            else:
                status = "FAIL"
                actual_result = f"Only excluded {excluded_count} entries, expected at least {expected_exclusions}"
                error_message = "Insufficient holiday exclusions"
            
            execution_time = time.time() - start_time
            
            return TestResult(
                scenario_id=scenario_id,
                scenario_name=scenario_name,
                status=status,
                expected_result=f"At least {expected_exclusions} holiday entries excluded",
                actual_result=actual_result,
                execution_time=execution_time,
                details={
                    "original_count": original_count,
                    "filtered_count": filtered_count,
                    "excluded_count": excluded_count
                },
                error_message=error_message
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            return TestResult(
                scenario_id=scenario_id,
                scenario_name=scenario_name,
                status="ERROR",
                expected_result="Successful holiday recognition",
                actual_result=f"Exception occurred: {str(e)}",
                execution_time=execution_time,
                details={},
                error_message=str(e)
            )
    
    def scenario_04_shortage_calculation_accuracy(self) -> TestResult:
        """Scenario 4: Shortage Calculation Accuracy"""
        start_time = time.time()
        scenario_id = "S04"
        scenario_name = "Shortage Calculation Accuracy"
        
        try:
            # Create controlled test data
            test_data = pd.DataFrame({
                'staff': ['職員1', '職員2', '職員3', '職員4', '職員5'],
                'role': ['看護師'] * 5,
                'parsed_slots_count': [8, 8, 8, 0, 0],  # Last two are holidays (0 slots)
                'staff_count': [1, 1, 1, 0, 0]  # Last two are holidays (0 count)
            })
            
            # Apply exclusion filter
            filtered_data = apply_rest_exclusion_filter(test_data, "UAT_Test_S04")
            
            # Manual calculation: 3 staff should remain
            expected_staff_count = 3
            actual_staff_count = len(filtered_data)
            
            # Verify total slots
            expected_total_slots = 24  # 3 staff * 8 slots each
            actual_total_slots = filtered_data['parsed_slots_count'].sum()
            
            if actual_staff_count == expected_staff_count and actual_total_slots == expected_total_slots:
                status = "PASS"
                actual_result = f"Correct calculation: {actual_staff_count} staff, {actual_total_slots} total slots"
                error_message = None
            else:
                status = "FAIL"
                actual_result = f"Incorrect calculation: {actual_staff_count} staff (expected {expected_staff_count}), {actual_total_slots} slots (expected {expected_total_slots})"
                error_message = "Calculation mismatch"
            
            execution_time = time.time() - start_time
            
            return TestResult(
                scenario_id=scenario_id,
                scenario_name=scenario_name,
                status=status,
                expected_result=f"{expected_staff_count} staff, {expected_total_slots} total slots",
                actual_result=actual_result,
                execution_time=execution_time,
                details={
                    "expected_staff": expected_staff_count,
                    "actual_staff": actual_staff_count,
                    "expected_slots": expected_total_slots,
                    "actual_slots": actual_total_slots
                },
                error_message=error_message
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            return TestResult(
                scenario_id=scenario_id,
                scenario_name=scenario_name,
                status="ERROR",
                expected_result="Accurate shortage calculation",
                actual_result=f"Exception occurred: {str(e)}",
                execution_time=execution_time,
                details={},
                error_message=str(e)
            )
    
    def scenario_07_heatmap_accuracy(self) -> TestResult:
        """Scenario 7: Heatmap Accuracy"""
        start_time = time.time()
        scenario_id = "S07"
        scenario_name = "Heatmap Data Accuracy"
        
        try:
            # Create test data with known holiday patterns
            test_file = self.create_test_excel("complex_holidays")
            
            # Simulate heatmap data processing
            raw_data = safe_read_excel(test_file, sheet_name="シフト表")
            
            # Count holidays by date column
            date_columns = [col for col in raw_data.columns if col not in ['staff', 'role']]
            holiday_counts = {}
            
            for date_col in date_columns:
                holiday_count = 0
                for value in raw_data[date_col]:
                    if str(value).strip() in ['×', '休', '有', '特', '欠', '研']:
                        holiday_count += 1
                holiday_counts[date_col] = holiday_count
            
            # Apply exclusion and verify reduction in staff counts
            filtered_data = apply_rest_exclusion_filter(raw_data, "UAT_Test_S07")
            
            # Validate that exclusion affects the data appropriately
            original_entries = len(raw_data)
            filtered_entries = len(filtered_data)
            exclusion_occurred = original_entries > filtered_entries
            
            if exclusion_occurred:
                status = "PASS"
                actual_result = f"Heatmap data properly filtered: {original_entries} -> {filtered_entries}"
                error_message = None
            else:
                status = "FAIL"
                actual_result = f"No exclusion occurred in heatmap data processing"
                error_message = "Heatmap filtering not working"
            
            execution_time = time.time() - start_time
            
            return TestResult(
                scenario_id=scenario_id,
                scenario_name=scenario_name,
                status=status,
                expected_result="Holiday entries excluded from heatmap data",
                actual_result=actual_result,
                execution_time=execution_time,
                details={
                    "original_entries": original_entries,
                    "filtered_entries": filtered_entries,
                    "holiday_counts_by_date": holiday_counts
                },
                error_message=error_message
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            return TestResult(
                scenario_id=scenario_id,
                scenario_name=scenario_name,
                status="ERROR",
                expected_result="Accurate heatmap processing",
                actual_result=f"Exception occurred: {str(e)}",
                execution_time=execution_time,
                details={},
                error_message=str(e)
            )
    
    def scenario_12_regression_testing(self) -> TestResult:
        """Scenario 12: Existing Functionality Preservation"""
        start_time = time.time()
        scenario_id = "S12"
        scenario_name = "Regression Testing - Existing Functionality"
        
        try:
            # Test with clean data (no holidays)
            test_file = self.create_test_excel("clean")
            raw_data = safe_read_excel(test_file, sheet_name="シフト表")
            
            # Apply exclusion filter
            filtered_data = apply_rest_exclusion_filter(raw_data, "UAT_Test_S12")
            
            # For clean data, no entries should be excluded
            original_count = len(raw_data)
            filtered_count = len(filtered_data)
            
            if original_count == filtered_count:
                status = "PASS"
                actual_result = f"Clean data processed correctly: {original_count} entries preserved"
                error_message = None
            else:
                status = "FAIL"
                actual_result = f"Clean data incorrectly filtered: {original_count} -> {filtered_count}"
                error_message = "Regression detected in clean data processing"
            
            execution_time = time.time() - start_time
            
            return TestResult(
                scenario_id=scenario_id,
                scenario_name=scenario_name,
                status=status,
                expected_result="Clean data processing unchanged",
                actual_result=actual_result,
                execution_time=execution_time,
                details={
                    "original_count": original_count,
                    "filtered_count": filtered_count,
                    "data_identical": original_count == filtered_count
                },
                error_message=error_message
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            return TestResult(
                scenario_id=scenario_id,
                scenario_name=scenario_name,
                status="ERROR",
                expected_result="No regression in existing functionality",
                actual_result=f"Exception occurred: {str(e)}",
                execution_time=execution_time,
                details={},
                error_message=str(e)
            )
    
    def scenario_19_performance_testing(self) -> TestResult:
        """Scenario 19: Large Dataset Performance"""
        start_time = time.time()
        scenario_id = "S19"
        scenario_name = "Large Dataset Performance Testing"
        
        try:
            # Create large dataset (1000 entries)
            large_data = pd.DataFrame({
                'staff': [f'職員{i:04d}' for i in range(1000)],
                'role': np.random.choice(['看護師', '介護士', 'その他'], 1000),
                'parsed_slots_count': np.random.choice([0, 8], 1000, p=[0.3, 0.7]),  # 30% holidays
                'staff_count': np.random.choice([0, 1], 1000, p=[0.3, 0.7])
            })
            
            # Apply exclusion filter and measure time
            process_start = time.time()
            filtered_data = apply_rest_exclusion_filter(large_data, "UAT_Test_S19_Performance")
            process_time = time.time() - process_start
            
            # Performance threshold: should complete within 30 seconds
            performance_threshold = 30.0
            original_count = len(large_data)
            filtered_count = len(filtered_data)
            
            if process_time < performance_threshold:
                status = "PASS"
                actual_result = f"Processed {original_count} entries in {process_time:.2f}s (< {performance_threshold}s)"
                error_message = None
            else:
                status = "FAIL"
                actual_result = f"Processing took {process_time:.2f}s, exceeded {performance_threshold}s threshold"
                error_message = "Performance threshold exceeded"
            
            execution_time = time.time() - start_time
            
            return TestResult(
                scenario_id=scenario_id,
                scenario_name=scenario_name,
                status=status,
                expected_result=f"Processing completes within {performance_threshold}s",
                actual_result=actual_result,
                execution_time=execution_time,
                details={
                    "dataset_size": original_count,
                    "filtered_size": filtered_count,
                    "processing_time": process_time,
                    "performance_threshold": performance_threshold
                },
                error_message=error_message
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            return TestResult(
                scenario_id=scenario_id,
                scenario_name=scenario_name,
                status="ERROR",
                expected_result="Acceptable performance with large dataset",
                actual_result=f"Exception occurred: {str(e)}",
                execution_time=execution_time,
                details={},
                error_message=str(e)
            )
    
    def run_all_scenarios(self) -> List[TestResult]:
        """Run all UAT scenarios"""
        logger.info("Starting UAT Scenario Execution")
        
        scenarios = [
            self.scenario_01_basic_holiday_recognition,
            self.scenario_04_shortage_calculation_accuracy,
            self.scenario_07_heatmap_accuracy,
            self.scenario_12_regression_testing,
            self.scenario_19_performance_testing
        ]
        
        results = []
        for scenario_func in scenarios:
            logger.info(f"Running {scenario_func.__name__}")
            try:
                result = scenario_func()
                results.append(result)
                logger.info(f"Scenario {result.scenario_id}: {result.status}")
                if result.error_message:
                    logger.error(f"Error in {result.scenario_id}: {result.error_message}")
            except Exception as e:
                logger.error(f"Critical error in {scenario_func.__name__}: {e}")
                logger.error(traceback.format_exc())
        
        self.test_results = results
        return results
    
    def generate_summary_report(self) -> Dict[str, Any]:
        """Generate comprehensive test summary report"""
        if not self.test_results:
            return {"error": "No test results available"}
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r.status == "PASS")
        failed_tests = sum(1 for r in self.test_results if r.status == "FAIL")
        error_tests = sum(1 for r in self.test_results if r.status == "ERROR")
        skipped_tests = sum(1 for r in self.test_results if r.status == "SKIP")
        
        pass_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        summary = {
            "test_execution_summary": {
                "total_tests": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "errors": error_tests,
                "skipped": skipped_tests,
                "pass_rate": round(pass_rate, 2)
            },
            "execution_timestamp": datetime.now().isoformat(),
            "overall_status": "PASS" if pass_rate >= 95 else "FAIL",
            "detailed_results": []
        }
        
        for result in self.test_results:
            summary["detailed_results"].append({
                "scenario_id": result.scenario_id,
                "scenario_name": result.scenario_name,
                "status": result.status,
                "execution_time": round(result.execution_time, 3),
                "expected_result": result.expected_result,
                "actual_result": result.actual_result,
                "error_message": result.error_message,
                "details": result.details
            })
        
        return summary
    
    def save_results(self, filename: str = None):
        """Save test results to file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"uat_results_{timestamp}.json"
        
        filepath = self.output_dir / filename
        summary = self.generate_summary_report()
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Test results saved to: {filepath}")
        return filepath

def main():
    """Main execution function"""
    print("=" * 60)
    print("UAT Scenarios - Holiday Exclusion Fixes Validation")
    print("=" * 60)
    
    # Initialize test runner
    runner = UATTestRunner()
    
    try:
        # Run all scenarios
        results = runner.run_all_scenarios()
        
        # Generate and save report
        results_file = runner.save_results()
        summary = runner.generate_summary_report()
        
        # Display summary
        print("\n" + "=" * 60)
        print("UAT EXECUTION SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {summary['test_execution_summary']['total_tests']}")
        print(f"Passed: {summary['test_execution_summary']['passed']}")
        print(f"Failed: {summary['test_execution_summary']['failed']}")
        print(f"Errors: {summary['test_execution_summary']['errors']}")
        print(f"Pass Rate: {summary['test_execution_summary']['pass_rate']}%")
        print(f"Overall Status: {summary['overall_status']}")
        print(f"Results saved to: {results_file}")
        
        # Display individual results
        print("\nDETAILED RESULTS:")
        print("-" * 60)
        for result in results:
            status_symbol = "✓" if result.status == "PASS" else "✗" if result.status == "FAIL" else "⚠"
            print(f"{status_symbol} {result.scenario_id}: {result.scenario_name} [{result.status}]")
            if result.error_message:
                print(f"   Error: {result.error_message}")
            print(f"   Time: {result.execution_time:.3f}s")
        
        print("\n" + "=" * 60)
        
        return 0 if summary['overall_status'] == "PASS" else 1
        
    except Exception as e:
        logger.error(f"Critical error during UAT execution: {e}")
        logger.error(traceback.format_exc())
        return 2
        
    finally:
        # Cleanup temporary files
        runner.cleanup()

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
#!/usr/bin/env python3
"""
Validation script to verify role-specific need aggregation in shortage analysis.
This script checks if role-specific need values are properly aggregated and
compares them with the total need file.
"""

import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import json
from typing import Dict, List, Tuple, Optional

class NeedAggregationValidator:
    def __init__(self, data_dir: str = None):
        """Initialize validator with data directory."""
        self.data_dir = data_dir or os.getcwd()
        # If data_dir contains parquet files directly, use it; otherwise look for parquet subdirectory
        if data_dir and any(f.endswith('.parquet') for f in os.listdir(data_dir) if os.path.isfile(os.path.join(data_dir, f))):
            self.parquet_dir = self.data_dir
        else:
            self.parquet_dir = os.path.join(self.data_dir, 'parquet')
        self.report_lines = []
        self.validation_results = {
            'role_files_found': [],
            'role_files_missing': [],
            'discrepancies': [],
            'aggregation_status': 'UNKNOWN',
            'total_records_checked': 0,
            'records_with_discrepancy': 0
        }
    
    def log(self, message: str, level: str = "INFO"):
        """Log message to report."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"[{timestamp}] [{level}] {message}"
        self.report_lines.append(log_line)
        print(log_line)
    
    def find_role_specific_files(self) -> List[Tuple[str, str]]:
        """Find all role-specific need files."""
        role_files = []
        
        if not os.path.exists(self.parquet_dir):
            self.log(f"Parquet directory not found: {self.parquet_dir}", "ERROR")
            return role_files
        
        # Pattern for role-specific need files
        for file in os.listdir(self.parquet_dir):
            if file.startswith('need_per_date_slot_role_') and file.endswith('.parquet'):
                role = file.replace('need_per_date_slot_role_', '').replace('.parquet', '')
                file_path = os.path.join(self.parquet_dir, file)
                role_files.append((role, file_path))
                self.validation_results['role_files_found'].append(role)
        
        self.log(f"Found {len(role_files)} role-specific need files")
        for role, path in role_files:
            self.log(f"  - Role: {role} -> {os.path.basename(path)}")
        
        return role_files
    
    def load_total_need_file(self) -> Optional[pd.DataFrame]:
        """Load the total need file."""
        total_file = os.path.join(self.parquet_dir, 'need_per_date_slot.parquet')
        
        if not os.path.exists(total_file):
            self.log(f"Total need file not found: {total_file}", "ERROR")
            return None
        
        try:
            df = pd.read_parquet(total_file)
            self.log(f"Loaded total need file: {total_file}")
            self.log(f"  - Shape: {df.shape}")
            self.log(f"  - Columns: {list(df.columns)}")
            return df
        except Exception as e:
            self.log(f"Error loading total need file: {str(e)}", "ERROR")
            return None
    
    def load_role_specific_file(self, file_path: str) -> Optional[pd.DataFrame]:
        """Load a role-specific need file."""
        try:
            df = pd.read_parquet(file_path)
            return df
        except Exception as e:
            self.log(f"Error loading file {file_path}: {str(e)}", "ERROR")
            return None
    
    def aggregate_role_files(self, role_files: List[Tuple[str, str]]) -> Optional[pd.DataFrame]:
        """Aggregate all role-specific files."""
        if not role_files:
            self.log("No role files to aggregate", "WARNING")
            return None
        
        aggregated_df = None
        
        for role, file_path in role_files:
            df = self.load_role_specific_file(file_path)
            if df is None:
                continue
            
            self.log(f"Loading role {role}: shape {df.shape}")
            
            # Add role column if not present
            if 'role' not in df.columns:
                df['role'] = role
            
            if aggregated_df is None:
                aggregated_df = df.copy()
            else:
                aggregated_df = pd.concat([aggregated_df, df], ignore_index=True)
        
        if aggregated_df is not None:
            self.log(f"Aggregated data shape: {aggregated_df.shape}")
            
            # Group by date and slot to sum needs across roles
            if 'date' in aggregated_df.columns and 'slot' in aggregated_df.columns:
                grouped = aggregated_df.groupby(['date', 'slot']).agg({
                    'need': 'sum'
                }).reset_index()
                self.log(f"Grouped aggregated data shape: {grouped.shape}")
                return grouped
            else:
                self.log("Required columns (date, slot) not found in aggregated data", "ERROR")
        
        return aggregated_df
    
    def compare_dataframes(self, total_df: pd.DataFrame, aggregated_df: pd.DataFrame) -> Dict:
        """Compare total need with aggregated role-specific needs."""
        comparison_results = {
            'exact_match': True,
            'discrepancy_count': 0,
            'discrepancies': [],
            'max_absolute_diff': 0,
            'max_relative_diff': 0
        }
        
        # Ensure both dataframes have the same columns for comparison
        common_cols = ['date', 'slot', 'need']
        
        # Check if required columns exist
        for col in common_cols:
            if col not in total_df.columns:
                self.log(f"Column '{col}' not found in total dataframe", "ERROR")
                return comparison_results
            if col not in aggregated_df.columns:
                self.log(f"Column '{col}' not found in aggregated dataframe", "ERROR")
                return comparison_results
        
        # Merge dataframes for comparison
        merged = pd.merge(
            total_df[common_cols],
            aggregated_df[common_cols],
            on=['date', 'slot'],
            how='outer',
            suffixes=('_total', '_aggregated')
        )
        
        # Fill NaN values with 0 for comparison
        merged['need_total'] = merged['need_total'].fillna(0)
        merged['need_aggregated'] = merged['need_aggregated'].fillna(0)
        
        # Calculate differences
        merged['diff'] = merged['need_total'] - merged['need_aggregated']
        merged['abs_diff'] = abs(merged['diff'])
        merged['relative_diff'] = merged.apply(
            lambda row: abs(row['diff'] / row['need_total']) if row['need_total'] != 0 else 0,
            axis=1
        )
        
        # Find discrepancies
        discrepancies = merged[merged['abs_diff'] > 0.001]  # Small tolerance for float comparison
        
        if len(discrepancies) > 0:
            comparison_results['exact_match'] = False
            comparison_results['discrepancy_count'] = len(discrepancies)
            comparison_results['max_absolute_diff'] = discrepancies['abs_diff'].max()
            comparison_results['max_relative_diff'] = discrepancies['relative_diff'].max()
            
            # Store top 10 discrepancies
            top_discrepancies = discrepancies.nlargest(10, 'abs_diff')
            for _, row in top_discrepancies.iterrows():
                self.validation_results['discrepancies'].append({
                    'date': str(row['date']),
                    'slot': row['slot'],
                    'total_need': row['need_total'],
                    'aggregated_need': row['need_aggregated'],
                    'difference': row['diff'],
                    'relative_diff': row['relative_diff']
                })
        
        self.validation_results['total_records_checked'] = len(merged)
        self.validation_results['records_with_discrepancy'] = comparison_results['discrepancy_count']
        
        return comparison_results
    
    def check_shortage_py_logic(self) -> Dict:
        """Check how shortage.py reads role-specific files."""
        shortage_py_path = os.path.join(self.data_dir, 'shift_suite', 'tasks', 'shortage.py')
        logic_check = {
            'file_exists': False,
            'reads_role_files': False,
            'aggregation_method': 'UNKNOWN',
            'relevant_code_snippets': []
        }
        
        if not os.path.exists(shortage_py_path):
            self.log(f"shortage.py not found at: {shortage_py_path}", "WARNING")
            return logic_check
        
        logic_check['file_exists'] = True
        
        try:
            with open(shortage_py_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
            
            # Look for patterns indicating role-specific file reading
            role_patterns = [
                'need_per_date_slot_role_',
                'role_specific_need',
                'aggregate.*role',
                'sum.*role.*need'
            ]
            
            for i, line in enumerate(lines):
                for pattern in role_patterns:
                    if pattern.lower() in line.lower():
                        logic_check['reads_role_files'] = True
                        # Get context (3 lines before and after)
                        start = max(0, i - 3)
                        end = min(len(lines), i + 4)
                        snippet = '\n'.join(f"{j}: {lines[j]}" for j in range(start, end))
                        logic_check['relevant_code_snippets'].append({
                            'line_number': i + 1,
                            'pattern_matched': pattern,
                            'context': snippet
                        })
            
            # Check for specific aggregation methods
            if 'groupby' in content and 'role' in content:
                logic_check['aggregation_method'] = 'GROUPBY'
            elif 'pivot' in content and 'role' in content:
                logic_check['aggregation_method'] = 'PIVOT'
            elif 'sum' in content and 'role' in content:
                logic_check['aggregation_method'] = 'SUM'
            
        except Exception as e:
            self.log(f"Error reading shortage.py: {str(e)}", "ERROR")
        
        return logic_check
    
    def generate_report(self, output_file: str = 'need_aggregation_validation_report.txt'):
        """Generate validation report."""
        report_path = os.path.join(self.data_dir, output_file)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("ROLE-SPECIFIC NEED AGGREGATION VALIDATION REPORT\n")
            f.write("=" * 80 + "\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Data Directory: {self.data_dir}\n")
            f.write("\n")
            
            # Summary
            f.write("SUMMARY\n")
            f.write("-" * 40 + "\n")
            f.write(f"Aggregation Status: {self.validation_results['aggregation_status']}\n")
            f.write(f"Role Files Found: {len(self.validation_results['role_files_found'])}\n")
            f.write(f"Total Records Checked: {self.validation_results['total_records_checked']}\n")
            f.write(f"Records with Discrepancy: {self.validation_results['records_with_discrepancy']}\n")
            f.write("\n")
            
            # Role files
            f.write("ROLE-SPECIFIC FILES\n")
            f.write("-" * 40 + "\n")
            if self.validation_results['role_files_found']:
                for role in self.validation_results['role_files_found']:
                    f.write(f"  ✓ {role}\n")
            else:
                f.write("  No role-specific files found\n")
            f.write("\n")
            
            # Discrepancies
            if self.validation_results['discrepancies']:
                f.write("TOP DISCREPANCIES\n")
                f.write("-" * 40 + "\n")
                for disc in self.validation_results['discrepancies']:
                    f.write(f"Date: {disc['date']}, Slot: {disc['slot']}\n")
                    f.write(f"  Total Need: {disc['total_need']:.2f}\n")
                    f.write(f"  Aggregated Need: {disc['aggregated_need']:.2f}\n")
                    f.write(f"  Difference: {disc['difference']:.2f} ({disc['relative_diff']:.1%})\n")
                    f.write("\n")
            
            # Detailed log
            f.write("\nDETAILED LOG\n")
            f.write("-" * 40 + "\n")
            for line in self.report_lines:
                f.write(line + "\n")
        
        # Also save as JSON for programmatic access
        json_path = os.path.join(self.data_dir, 'need_aggregation_validation_results.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(self.validation_results, f, indent=2, ensure_ascii=False)
        
        self.log(f"Report saved to: {report_path}")
        self.log(f"JSON results saved to: {json_path}")
        
        return report_path
    
    def run_validation(self):
        """Run the complete validation process."""
        self.log("Starting role-specific need aggregation validation")
        self.log(f"Working directory: {self.data_dir}")
        
        # Step 1: Find role-specific files
        role_files = self.find_role_specific_files()
        
        # Step 2: Load total need file
        total_df = self.load_total_need_file()
        
        if total_df is None:
            self.validation_results['aggregation_status'] = 'ERROR: No total need file'
            self.log("Validation failed: Could not load total need file", "ERROR")
            return False
        
        # Step 3: Aggregate role-specific files
        if role_files:
            aggregated_df = self.aggregate_role_files(role_files)
            
            if aggregated_df is not None:
                # Step 4: Compare results
                comparison = self.compare_dataframes(total_df, aggregated_df)
                
                if comparison['exact_match']:
                    self.validation_results['aggregation_status'] = 'VALID: Perfect match'
                    self.log("Validation PASSED: Role aggregation matches total need", "SUCCESS")
                else:
                    self.validation_results['aggregation_status'] = f'INVALID: {comparison["discrepancy_count"]} discrepancies'
                    self.log(f"Validation FAILED: Found {comparison['discrepancy_count']} discrepancies", "ERROR")
                    self.log(f"Max absolute difference: {comparison['max_absolute_diff']:.2f}", "ERROR")
                    self.log(f"Max relative difference: {comparison['max_relative_diff']:.1%}", "ERROR")
            else:
                self.validation_results['aggregation_status'] = 'ERROR: Could not aggregate role files'
                self.log("Could not aggregate role-specific files", "ERROR")
        else:
            self.validation_results['aggregation_status'] = 'WARNING: No role files found'
            self.log("No role-specific files found - checking if total file contains role data", "WARNING")
            
            # Check if total file has role column
            if 'role' in total_df.columns:
                unique_roles = total_df['role'].unique()
                self.log(f"Total file contains role data: {unique_roles}", "INFO")
                self.validation_results['aggregation_status'] = 'INFO: Roles in total file'
            else:
                self.log("Total file does not contain role column", "INFO")
        
        # Step 5: Check shortage.py logic
        self.log("\nChecking shortage.py implementation...")
        shortage_logic = self.check_shortage_py_logic()
        
        if shortage_logic['file_exists']:
            if shortage_logic['reads_role_files']:
                self.log("shortage.py appears to read role-specific files", "INFO")
                self.log(f"Aggregation method detected: {shortage_logic['aggregation_method']}", "INFO")
            else:
                self.log("shortage.py does not appear to read role-specific files", "WARNING")
        
        # Step 6: Generate report
        report_path = self.generate_report()
        
        return self.validation_results['aggregation_status'].startswith('VALID')


def main():
    """Main execution function."""
    # Check if custom data directory is provided
    data_dir = sys.argv[1] if len(sys.argv) > 1 else None
    
    validator = NeedAggregationValidator(data_dir)
    success = validator.run_validation()
    
    print("\n" + "=" * 60)
    print("VALIDATION COMPLETE")
    print("=" * 60)
    print(f"Status: {validator.validation_results['aggregation_status']}")
    print(f"Check the report for detailed results: need_aggregation_validation_report.txt")
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
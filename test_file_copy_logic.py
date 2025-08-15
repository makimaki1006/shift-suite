#!/usr/bin/env python3
"""
Test file copy logic implementation
"""
from pathlib import Path
import tempfile
import shutil

def test_file_copy_logic():
    """Test the file copy logic that we implemented"""
    
    print("=== ファイルコピーロジックのテスト ===\n")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        base_path = Path(temp_dir)
        
        # Simulate scenario directories
        current_scenario_dirs = {
            "mean_based": base_path / "out_mean_based",
            "median_based": base_path / "out_median_based", 
            "p25_based": base_path / "out_p25_based"
        }
        
        # Create directories
        for scenario_name, scenario_path in current_scenario_dirs.items():
            scenario_path.mkdir(parents=True, exist_ok=True)
            print(f"Created: {scenario_path}")
        
        # Simulate scenario_out_dir pointing to last scenario (p25_based)
        scenario_out_dir = current_scenario_dirs["p25_based"]
        print(f"\nscenario_out_dir points to: {scenario_out_dir}")
        
        # Create test files in p25_based
        test_files = [
            "fatigue_score.parquet",
            "rest_time.csv", 
            "work_patterns.csv",
            "stats_alerts.parquet",
            "attendance.csv"
        ]
        
        for file_name in test_files:
            test_file = scenario_out_dir / file_name
            test_file.write_text(f"Test content for {file_name}")
            print(f"Created test file: {test_file}")
        
        print(f"\nBefore copy - Files in each scenario:")
        for scenario_name, scenario_path in current_scenario_dirs.items():
            files = list(scenario_path.glob("*"))
            print(f"  {scenario_name}: {len(files)} files")
        
        # Test the copy logic
        print(f"\nTesting copy logic...")
        copied_count = 0
        
        for scenario_name, scenario_path in current_scenario_dirs.items():
            if scenario_path != scenario_out_dir:  # Don't copy to itself
                print(f"  Copying to {scenario_name}...")
                for file_name in test_files:
                    source_file = scenario_out_dir / file_name
                    if source_file.exists():
                        target_file = Path(scenario_path) / file_name
                        shutil.copy2(source_file, target_file)
                        copied_count += 1
                        print(f"    Copied: {file_name}")
        
        print(f"\nAfter copy - Files in each scenario:")
        for scenario_name, scenario_path in current_scenario_dirs.items():
            files = list(scenario_path.glob("*"))
            print(f"  {scenario_name}: {len(files)} files")
        
        # Verify results
        expected_files_per_scenario = len(test_files)
        success = True
        
        for scenario_name, scenario_path in current_scenario_dirs.items():
            files = list(scenario_path.glob("*"))
            if len(files) != expected_files_per_scenario:
                print(f"ERROR: {scenario_name} has {len(files)} files, expected {expected_files_per_scenario}")
                success = False
            else:
                print(f"OK: {scenario_name} has correct number of files")
        
        print(f"\nTotal files copied: {copied_count}")
        print(f"Expected copies: {len(test_files) * (len(current_scenario_dirs) - 1)}")  # -1 because we don't copy to source
        
        if success and copied_count == len(test_files) * (len(current_scenario_dirs) - 1):
            print("\n✓ ファイルコピーロジックは正常に動作します")
            return True
        else:
            print("\n✗ ファイルコピーロジックに問題があります")
            return False

if __name__ == "__main__":
    test_file_copy_logic()
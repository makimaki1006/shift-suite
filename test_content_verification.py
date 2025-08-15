#!/usr/bin/env python3
# Test content verification of need_per_date_slot files

import sys
import os
import tempfile
import zipfile
from pathlib import Path

# Add current directory to path
sys.path.insert(0, os.getcwd())

print("=== Content Verification Test ===")

try:
    import pandas as pd
    from shift_suite.tasks.io_excel import ingest_excel
    from shift_suite.tasks.heatmap import build_heatmap
    
    # Test data file
    excel_path = Path("デイ_テスト用データ_休日精緻.xlsx")
    
    # Get sheet info
    sheets = pd.ExcelFile(excel_path, engine="openpyxl").sheet_names
    master_sheet = next((s for s in sheets if "勤務" in s), None)
    shift_sheets = [s for s in sheets if s != master_sheet]
    
    # Create temporary work directory
    work_root = Path(tempfile.mkdtemp())
    out_dir = work_root / "out"
    out_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Output directory: {out_dir}")
    
    # Generate new files
    print("Step 1: Generate new files...")
    long_df, wt_df, unknown_codes = ingest_excel(
        excel_path,
        shift_sheets=shift_sheets,
        header_row=3
    )
    
    build_heatmap(long_df, wt_df, out_dir, 30, min_method="p25")
    
    # List generated need files
    new_need_files = list(out_dir.glob("need_per_date_slot*.parquet"))
    print(f"Generated {len(new_need_files)} need files")
    
    # Extract motogi_day.zip to compare
    motogi_zip = Path("motogi_day.zip")
    if motogi_zip.exists():
        print("\nStep 2: Extract motogi_day.zip...")
        extract_dir = work_root / "motogi_extracted"
        extract_dir.mkdir(exist_ok=True)
        
        with zipfile.ZipFile(motogi_zip, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
        
        # Find the analysis results directory
        analysis_dirs = list(extract_dir.glob("**/out_p25_based"))
        if analysis_dirs:
            motogi_out_dir = analysis_dirs[0]
            print(f"Found motogi output directory: {motogi_out_dir}")
            
            # List original need files
            original_need_files = list(motogi_out_dir.glob("need_per_date_slot*.parquet"))
            print(f"Original files: {len(original_need_files)}")
            
            # Compare file counts
            print(f"\nFile count comparison:")
            print(f"  New files: {len(new_need_files)}")
            print(f"  Original files: {len(original_need_files)}")
            
            # Compare specific files
            print(f"\nContent comparison:")
            
            # Check if general need_per_date_slot.parquet exists in both
            new_general = out_dir / "need_per_date_slot.parquet"
            original_general = motogi_out_dir / "need_per_date_slot.parquet"
            
            if new_general.exists() and original_general.exists():
                print("Comparing need_per_date_slot.parquet (general)...")
                new_df = pd.read_parquet(new_general)
                original_df = pd.read_parquet(original_general)
                
                print(f"  New shape: {new_df.shape}")
                print(f"  Original shape: {original_df.shape}")
                
                if new_df.shape == original_df.shape:
                    # Compare values
                    are_equal = new_df.equals(original_df)
                    print(f"  Content identical: {are_equal}")
                    
                    if not are_equal:
                        # Check differences
                        diff_mask = (new_df != original_df).any(axis=1)
                        if diff_mask.any():
                            print(f"  Differences found in {diff_mask.sum()} rows")
                            # Show first few differences
                            diff_rows = new_df[diff_mask].head(3)
                            print("  Sample differences:")
                            print(diff_rows)
                        else:
                            print("  No numerical differences found")
                else:
                    print("  ❌ Different shapes!")
            else:
                print("  ❌ General need_per_date_slot.parquet missing in one or both")
            
            # Check role-specific files
            role_files_new = [f for f in new_need_files if "role_" in f.name]
            role_files_original = [f for f in original_need_files if "role_" in f.name]
            
            print(f"\nRole-specific files:")
            print(f"  New: {len(role_files_new)}")
            print(f"  Original: {len(role_files_original)}")
            
            # Check employment-specific files
            emp_files_new = [f for f in new_need_files if "emp_" in f.name]
            emp_files_original = [f for f in original_need_files if "emp_" in f.name]
            
            print(f"\nEmployment-specific files:")
            print(f"  New: {len(emp_files_new)}")
            print(f"  Original: {len(emp_files_original)}")
            
            # List all files for comparison
            print(f"\nDetailed file comparison:")
            
            new_names = {f.name for f in new_need_files}
            original_names = {f.name for f in original_need_files}
            
            print(f"New files:")
            for name in sorted(new_names):
                print(f"  ✓ {name}")
            
            print(f"Original files:")
            for name in sorted(original_names):
                print(f"  ✓ {name}")
            
            missing_in_new = original_names - new_names
            extra_in_new = new_names - original_names
            
            if missing_in_new:
                print(f"\nMissing in new generation:")
                for name in sorted(missing_in_new):
                    print(f"  ❌ {name}")
            
            if extra_in_new:
                print(f"\nExtra in new generation:")
                for name in sorted(extra_in_new):
                    print(f"  ➕ {name}")
            
            if not missing_in_new and not extra_in_new:
                print(f"\n✅ All expected files generated!")
            else:
                print(f"\n⚠️  File mismatch detected")
            
        else:
            print("❌ Could not find analysis results directory in motogi_day.zip")
    else:
        print("❌ motogi_day.zip not found")
    
    print(f"\nTest completed. Work directory: {work_root}")
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
#!/usr/bin/env python3
"""
Copy and extract analysis results
"""
import shutil
import zipfile
import os
from pathlib import Path

def copy_and_extract_results():
    """分析結果のコピーと展開"""
    
    source_zip = r"C:\Users\fuji1\Downloads\analysis_results (2).zip"
    target_zip = "downloaded_analysis_results.zip"
    extract_dir = "downloaded_analysis_results"
    
    try:
        # Step 1: Copy zip file
        print("Step 1: Copying analysis results zip file...")
        if os.path.exists(source_zip):
            shutil.copy2(source_zip, target_zip)
            print(f"SUCCESS: Copied {source_zip} to {target_zip}")
        else:
            print(f"ERROR: Source file not found: {source_zip}")
            return False
        
        # Step 2: Extract zip file
        print("Step 2: Extracting zip contents...")
        if os.path.exists(target_zip):
            # Create extraction directory
            if os.path.exists(extract_dir):
                shutil.rmtree(extract_dir)
            os.makedirs(extract_dir)
            
            # Extract
            with zipfile.ZipFile(target_zip, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            
            print(f"SUCCESS: Extracted to {extract_dir}")
            
            # List contents
            print("\nExtracted contents:")
            for root, dirs, files in os.walk(extract_dir):
                level = root.replace(extract_dir, '').count(os.sep)
                indent = ' ' * 2 * level
                print(f"{indent}{os.path.basename(root)}/")
                subindent = ' ' * 2 * (level + 1)
                for file in files:
                    file_path = os.path.join(root, file)
                    file_size = os.path.getsize(file_path)
                    print(f"{subindent}{file} ({file_size} bytes)")
            
            return True
        else:
            print(f"ERROR: Target zip file not found: {target_zip}")
            return False
            
    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    copy_and_extract_results()
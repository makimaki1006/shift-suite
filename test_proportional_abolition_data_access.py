#!/usr/bin/env python3
"""
按分廃止データアクセステスト
"""

import sys
sys.path.append('.')
from pathlib import Path
import pandas as pd

def test_direct_file_access():
    """直接ファイルアクセステスト"""
    
    print("=== 直接ファイルアクセステスト ===")
    
    # テスト1: ファイル存在確認
    role_file = Path('proportional_abolition_role_summary.parquet')
    org_file = Path('proportional_abolition_organization_summary.parquet')
    metadata_file = Path('proportional_abolition_metadata.json')
    
    print(f"Role summary file exists: {role_file.exists()}")
    print(f"Organization summary file exists: {org_file.exists()}")  
    print(f"Metadata file exists: {metadata_file.exists()}")
    
    if role_file.exists():
        try:
            df = pd.read_parquet(role_file)
            print(f"Role summary - Shape: {df.shape}")
            print(f"Role summary - Columns: {list(df.columns)}")
            print("Role summary - Sample data:")
            print(df.head())
        except Exception as e:
            print(f"Error reading role file: {e}")
    
    if org_file.exists():
        try:
            df = pd.read_parquet(org_file)
            print(f"\nOrg summary - Shape: {df.shape}")
            print(f"Org summary - Columns: {list(df.columns)}")
            print("Org summary - Sample data:")
            print(df.head())
        except Exception as e:
            print(f"Error reading org file: {e}")

def test_data_get_function():
    """data_get関数テスト"""
    
    print("\n=== data_get関数テスト ===")
    
    try:
        # dash_appから必要な関数をインポート
        from dash_app import data_get
        
        # 按分廃止データの読み込みテスト
        print("Testing proportional_abolition_role_summary...")
        df_role = data_get('proportional_abolition_role_summary')
        
        if df_role is not None and not df_role.empty:
            print(f"✓ Role data loaded: {df_role.shape}")
            print(f"Columns: {list(df_role.columns)}")
        else:
            print("✗ Role data not found or empty")
        
        print("\nTesting proportional_abolition_organization_summary...")
        df_org = data_get('proportional_abolition_organization_summary')
        
        if df_org is not None and not df_org.empty:
            print(f"✓ Org data loaded: {df_org.shape}")
            print(f"Columns: {list(df_org.columns)}")
        else:
            print("✗ Org data not found or empty")
            
    except Exception as e:
        print(f"Error testing data_get function: {e}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    test_direct_file_access()
    test_data_get_function()
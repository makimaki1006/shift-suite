#!/usr/bin/env python3
"""
結果.zipの中の休暇データを確認
"""

import zipfile
from pathlib import Path

def check_leave_in_zip():
    """結果.zipの中身を確認"""
    zip_path = Path("結果.zip")
    
    if not zip_path.exists():
        print("❌ 結果.zipが見つかりません")
        return
    
    print(f"=== {zip_path} の内容確認 ===")
    
    with zipfile.ZipFile(zip_path, 'r') as zf:
        files = zf.namelist()
        
        # 休暇関連のファイルを探す
        leave_files = [f for f in files if any(
            keyword in f.lower() for keyword in ['leave', 'holiday', '休暇', 'absence']
        )]
        
        if leave_files:
            print(f"休暇関連ファイル: {leave_files}")
        else:
            print("❌ 休暇関連ファイルが見つかりません")
        
        # long_df.parquetの存在確認
        long_df_files = [f for f in files if 'long_df' in f]
        if long_df_files:
            print(f"long_dfファイル: {long_df_files}")
        
        # すべてのparquetファイルをリスト
        parquet_files = [f for f in files if f.endswith('.parquet')]
        print(f"\nParquetファイル一覧 ({len(parquet_files)}個):")
        for pf in sorted(parquet_files)[:20]:  # 最初の20個
            print(f"  - {pf}")

check_leave_in_zip()
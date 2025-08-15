#!/usr/bin/env python3
"""
勤務区分シートに未定義の'休'コードを追加
"""

import pandas as pd
from pathlib import Path
import shutil

def add_missing_holiday_code():
    """勤務区分シートに'休'コードを追加"""
    
    print("=== Adding Missing Holiday Code ===")
    
    original_file = Path("デイ_テスト用データ_休日精緻.xlsx")
    backup_file = Path("デイ_テスト用データ_休日精緻_backup.xlsx")
    
    try:
        # バックアップ作成
        shutil.copy2(original_file, backup_file)
        print(f"Backup created: {backup_file}")
        
        # 勤務区分シート読み込み
        df_worktype = pd.read_excel(original_file, sheet_name="勤務区分", dtype=str).fillna("")
        
        print(f"Current worktype definitions: {len(df_worktype)} rows")
        print("Existing codes:", df_worktype.iloc[:, 0].tolist())
        
        # '休'コードが既に存在するかチェック
        existing_codes = df_worktype.iloc[:, 0].tolist()
        if '休' in existing_codes:
            print("'休' code already exists!")
            return
        
        # 新しい行を追加
        new_row = pd.DataFrame({
            df_worktype.columns[0]: ['休'],           # コード
            df_worktype.columns[1]: [''],             # 開始時刻（空）
            df_worktype.columns[2]: [''],             # 終了時刻（空）
            df_worktype.columns[3]: ['施設休業日']     # 備考
        })
        
        # データフレームに追加
        df_worktype_updated = pd.concat([df_worktype, new_row], ignore_index=True)
        
        print(f"Updated worktype definitions: {len(df_worktype_updated)} rows")
        print("New codes:", df_worktype_updated.iloc[:, 0].tolist())
        
        # 他のシートも読み込み
        with pd.ExcelFile(original_file) as xls:
            all_sheets = {}
            for sheet_name in xls.sheet_names:
                if sheet_name == "勤務区分":
                    all_sheets[sheet_name] = df_worktype_updated
                else:
                    all_sheets[sheet_name] = pd.read_excel(xls, sheet_name=sheet_name)
        
        # 更新されたExcelファイルを書き込み
        with pd.ExcelWriter(original_file, engine='openpyxl') as writer:
            for sheet_name, df in all_sheets.items():
                df.to_excel(writer, sheet_name=sheet_name, index=False)
        
        print(f"✓ Successfully added '休' code to worktype sheet")
        print(f"✓ File updated: {original_file}")
        print(f"✓ Backup available: {backup_file}")
        
        # 追加確認
        df_verify = pd.read_excel(original_file, sheet_name="勤務区分", dtype=str).fillna("")
        verify_codes = df_verify.iloc[:, 0].tolist()
        
        if '休' in verify_codes:
            print("✓ Verification successful: '休' code found in updated file")
        else:
            print("✗ Verification failed: '休' code not found in updated file")
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        
        # エラー時はバックアップから復元
        if backup_file.exists():
            shutil.copy2(backup_file, original_file)
            print(f"Restored from backup: {original_file}")

if __name__ == "__main__":
    add_missing_holiday_code()
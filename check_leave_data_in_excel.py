#!/usr/bin/env python3
"""
Excelファイルに休暇データが含まれているか確認
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from shift_suite.tasks.utils import safe_read_excel
import pandas as pd

def check_leave_data(file_path):
    """Excelファイルの休暇データをチェック"""
    print(f"\n=== {file_path.name} の休暇データチェック ===")
    
    try:
        df = safe_read_excel(file_path)
        if df is None or df.empty:
            print(f"❌ ファイルが読み込めません")
            return
        
        print(f"✅ データ読み込み成功: {len(df)}行")
        
        # カラム名を確認
        print(f"カラム: {list(df.columns)[:10]}...")  # 最初の10個
        
        # 休暇関連の列を探す
        leave_columns = []
        for col in df.columns:
            col_lower = str(col).lower()
            if any(keyword in col_lower for keyword in ['休', 'leave', 'holiday', '有給', '希望', '特別']):
                leave_columns.append(col)
        
        if leave_columns:
            print(f"休暇関連の列を発見: {leave_columns}")
            
            # 各列の値を確認
            for col in leave_columns[:3]:  # 最初の3列まで
                unique_values = df[col].dropna().unique()[:10]  # 最初の10個のユニーク値
                print(f"  {col}: {list(unique_values)}")
        else:
            print("❌ 休暇関連の列が見つかりません")
        
        # データの中身から休暇を判定（parsed_slots_count=0 の場合など）
        if 'parsed_slots_count' in df.columns:
            zero_slots = df[df['parsed_slots_count'] == 0]
            print(f"parsed_slots_count=0 のレコード: {len(zero_slots)}件")
        
        # シフトコードやworktypeから休暇を推定
        for col in ['code', 'worktype', 'shift_code', 'シフト', '勤務']:
            if col in df.columns:
                values = df[col].dropna().unique()[:20]
                print(f"{col}の値: {list(values)}")
                
                # 休暇らしきコードを探す
                leave_codes = [v for v in values if any(
                    keyword in str(v) for keyword in ['休', '有', '希', '特', 'OFF', 'off', '×']
                )]
                if leave_codes:
                    print(f"  → 休暇関連コード候補: {leave_codes}")
    
    except Exception as e:
        print(f"❌ エラー: {e}")

# メインのExcelファイルをチェック
excel_files = [
    "ショート_テスト用データ.xlsx",
    "デイ_テスト用データ_休日精緻.xlsx",
    "勤務表　勤務時間_トライアル.xlsx"
]

for file_name in excel_files:
    file_path = Path(file_name)
    if file_path.exists():
        check_leave_data(file_path)
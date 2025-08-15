#!/usr/bin/env python3
"""
修正後の検証テスト
三つの値が一致することを確認
"""

import sys
import os
sys.path.insert(0, os.getcwd())

from proportional_shortage_helper import generate_proportional_shortage_data, validate_dashboard_consistency
from pathlib import Path

def verify_fix():
    """修正後の数値一致を検証"""
    print("=== 修正後の検証テスト ===")
    
    excel_path = "ショート_テスト用データ.xlsx"
    
    if not Path(excel_path).exists():
        print("テストファイルが見つかりません")
        return
    
    # 按分方式データ生成
    result = generate_proportional_shortage_data(excel_path, "median")
    
    if not result:
        print("データ生成失敗")
        return
    
    # 全体不足時間
    total_shortage = result['total_shortage_hours']
    print(f"全体不足時間: {total_shortage:.2f}時間")
    
    # 職種別合計
    role_df = result['shortage_role_summary']
    role_sum = role_df[role_df['role'] != '全体']['shortage_hours'].sum() if not role_df.empty else 0
    print(f"職種別合計: {role_sum:.2f}時間")
    
    # 雇用形態別合計  
    emp_df = result['shortage_employment_summary']
    emp_sum = emp_df[emp_df['employment'] != '全体']['shortage_hours'].sum() if not emp_df.empty else 0
    print(f"雇用形態別合計: {emp_sum:.2f}時間")
    
    # 一致確認
    tolerance = 0.01
    role_match = abs(total_shortage - role_sum) < tolerance
    emp_match = abs(total_shortage - emp_sum) < tolerance
    
    print(f"\n=== 一致確認 ===")
    print(f"全体 vs 職種別: {'✓ 一致' if role_match else '✗ 不一致'} (差: {abs(total_shortage - role_sum):.6f})")
    print(f"全体 vs 雇用形態別: {'✓ 一致' if emp_match else '✗ 不一致'} (差: {abs(total_shortage - emp_sum):.6f})")
    
    if role_match and emp_match:
        print("✓ 修正成功: 三つの値が完全に一致しました")
    else:
        print("✗ まだ不一致があります")
    
    # 詳細検証
    validation = validate_dashboard_consistency(result)
    print(f"\n詳細検証結果: {validation}")

if __name__ == "__main__":
    verify_fix()
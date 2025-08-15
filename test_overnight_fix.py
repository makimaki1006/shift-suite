#!/usr/bin/env python3
"""
明け番シフトの0:00以降表示問題の修正テスト
"""

import sys
import os
from pathlib import Path

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from shift_suite.tasks.utils import gen_labels

def test_gen_labels():
    """gen_labels関数のテスト"""
    print("=== gen_labels関数テスト ===")
    
    # 標準24時間
    standard_labels = gen_labels(30, extended_hours=False)
    print(f"標準24時間ラベル数: {len(standard_labels)}")
    print(f"最初の5個: {standard_labels[:5]}")
    print(f"最後の5個: {standard_labels[-5:]}")
    
    # 拡張32時間（明け番対応）
    extended_labels = gen_labels(30, extended_hours=True)
    print(f"\n拡張32時間ラベル数: {len(extended_labels)}")
    print(f"最初の5個: {extended_labels[:5]}")
    print(f"最後の5個: {extended_labels[-5:]}")
    
    # 0:00台の確認
    midnight_labels = [label for label in extended_labels if label.startswith("0")]
    print(f"\n0:xx時間帯ラベル数: {len(midnight_labels)}")
    print(f"0:xx時間帯: {midnight_labels}")
    
    # 7:xx台の確認
    seven_labels = [label for label in extended_labels if label.startswith("07")]
    print(f"\n07:xx時間帯ラベル数: {len(seven_labels)}")
    print(f"07:xx時間帯: {seven_labels}")

def test_heatmap_integration():
    """heatmap.pyとの統合テスト"""
    print("\n=== heatmap.py統合テスト ===")
    
    # 実際にheatmap.pyをインポートしてテスト用データでテスト
    try:
        from shift_suite.tasks.heatmap import calculate_pattern_based_need
        import pandas as pd
        import datetime as dt
        
        # テスト用の明け番データを作成
        test_long_df = pd.DataFrame({
            'ds': [dt.datetime(2025, 6, 1, 16, 0), dt.datetime(2025, 6, 1, 0, 0), dt.datetime(2025, 6, 1, 8, 0)],
            'staff': ['スタッフA', 'スタッフA', 'スタッフA'],
            'role': ['介護', '介護', '介護'],
            'code': ['明', '明', '明'],
            'holiday_type': ['通常勤務', '通常勤務', '通常勤務']
        })
        
        # テスト用の実績データを作成
        time_labels = gen_labels(30, extended_hours=True)
        test_actual_staff = pd.DataFrame(
            0, 
            index=time_labels, 
            columns=[dt.date(2025, 6, 1)]
        )
        test_actual_staff.loc['16:00', dt.date(2025, 6, 1)] = 1
        test_actual_staff.loc['00:00', dt.date(2025, 6, 1)] = 1
        test_actual_staff.loc['08:00', dt.date(2025, 6, 1)] = 1
        
        print("テスト用データ作成完了")
        print(f"時間ラベル数: {len(time_labels)}")
        print(f"実績データ形状: {test_actual_staff.shape}")
        print(f"0:00の値: {test_actual_staff.loc['00:00', dt.date(2025, 6, 1)]}")
        
    except ImportError as e:
        print(f"heatmap.pyのインポートエラー: {e}")
    except Exception as e:
        print(f"統合テストエラー: {e}")

if __name__ == "__main__":
    test_gen_labels()
    test_heatmap_integration()
    print("\n=== テスト完了 ===")
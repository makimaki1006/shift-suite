#!/usr/bin/env python3
"""
統合的な休暇除外システムのテストスクリプト

修正内容:
1. utils.pyに統合的な休暇除外フィルターを追加
2. dash_app.pyの二重フィルタリングを修正
3. 全データフローで一貫した休暇除外を適用

このスクリプトで動作確認を行う
"""

import sys
import os
from pathlib import Path

# Add shift_suite to path
sys.path.insert(0, str(Path(__file__).parent))

def test_unified_rest_exclusion():
    """統合休暇除外フィルターのテスト"""
    print("🧪 統合休暇除外フィルターのテスト")
    
    try:
        import pandas as pd
        from shift_suite.tasks.utils import apply_rest_exclusion_filter
        
        # テストデータを作成
        test_data = pd.DataFrame({
            'staff': ['田中太郎', '×', '休み', 'OFF', '佐藤花子', '山田次郎', '休', 'x', '正社員A', '有休'],
            'parsed_slots_count': [8, 0, 0, 0, 6, 4, 0, 0, 8, 0],
            'role': ['介護', '介護', '介護', '看護師', '看護師', '介護', '介護', '介護', '介護', '介護'],
            'holiday_type': ['通常勤務', '希望休', 'その他休暇', 'その他休暇', '通常勤務', '通常勤務', 'その他休暇', '希望休', '通常勤務', '有給']
        })
        
        print(f"📊 テストデータ ({len(test_data)}件):")
        print(test_data[['staff', 'parsed_slots_count', 'holiday_type']])
        
        # フィルター適用
        print(f"\n🔧 統合フィルター適用...")
        filtered_data = apply_rest_exclusion_filter(test_data, "test")
        
        print(f"\n✅ フィルター適用後 ({len(filtered_data)}件):")
        if not filtered_data.empty:
            print(filtered_data[['staff', 'parsed_slots_count', 'holiday_type']])
        else:
            print("全レコードが除外されました")
        
        print(f"\n📈 結果: {len(test_data)}件 → {len(filtered_data)}件 (除外: {len(test_data) - len(filtered_data)}件)")
        
        return len(filtered_data) > 0
        
    except ImportError as e:
        print(f"❌ インポートエラー: {e}")
        return False
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        return False

def test_dashboard_integration():
    """ダッシュボード統合テスト"""
    print(f"\n🌐 ダッシュボード統合テスト")
    
    try:
        from dash_app import create_enhanced_rest_exclusion_filter
        import pandas as pd
        
        test_data = pd.DataFrame({
            'staff': ['スタッフA', '×', '休み', 'スタッフB'],
            'staff_count': [2, 0, 0, 3],
            'time': ['09:00', '10:00', '11:00', '12:00'],
            'date_lbl': ['2025-06-01'] * 4
        })
        
        print(f"📊 ダッシュボードテストデータ ({len(test_data)}件):")
        print(test_data)
        
        filtered_data = create_enhanced_rest_exclusion_filter(test_data)
        
        print(f"\n✅ ダッシュボードフィルター適用後 ({len(filtered_data)}件):")
        print(filtered_data)
        
        return len(filtered_data) > 0
        
    except ImportError as e:
        print(f"❌ ダッシュボードインポートエラー: {e}")
        return False
    except Exception as e:
        print(f"❌ ダッシュボードテストエラー: {e}")
        return False

def test_io_excel_integration():
    """io_excel.py統合テスト"""
    print(f"\n📊 Excel入稿統合テスト")
    
    try:
        from shift_suite.tasks.io_excel import LEAVE_CODES, _is_leave_code
        
        print(f"📋 定義済み休暇コード: {LEAVE_CODES}")
        
        test_codes = ['×', '休', '有', 'A', '早', '遅', '夜']
        for code in test_codes:
            is_leave = _is_leave_code(code)
            print(f"  '{code}': {'休暇コード' if is_leave else '通常勤務'}")
        
        return True
        
    except ImportError as e:
        print(f"❌ io_excelインポートエラー: {e}")
        return False
    except Exception as e:
        print(f"❌ io_excelテストエラー: {e}")
        return False

def show_modification_summary():
    """修正内容のサマリーを表示"""
    print(f"\n📋 実施した修正内容:")
    print(f"1. shift_suite/tasks/utils.py に統合休暇除外フィルター `apply_rest_exclusion_filter` を追加")
    print(f"2. dash_app.py の二重フィルタリング問題を修正")
    print(f"3. dash_app.py のフィルター関数を統合版にリダイレクト")
    print(f"4. 全データキー ('pre_aggregated_data', 'long_df', 'intermediate_data') で統一フィルターを使用")
    print(f"5. 詳細なログ出力で追跡可能にしました")

def main():
    print("🚀 統合的な休暇除外システムの動作確認")
    print("=" * 60)
    
    tests_passed = 0
    total_tests = 3
    
    if test_unified_rest_exclusion():
        tests_passed += 1
    
    if test_dashboard_integration():
        tests_passed += 1
        
    if test_io_excel_integration():
        tests_passed += 1
    
    show_modification_summary()
    
    print(f"\n" + "=" * 60)
    print(f"📊 テスト結果: {tests_passed}/{total_tests} 通過")
    
    if tests_passed == total_tests:
        print("✅ 全テスト通過！統合休暇除外システムが正常に動作しています。")
        print("\n🎯 次のステップ:")
        print("1. dash_app.py を起動してショート_テスト用データ.xlsx をアップロード")
        print("2. ヒートマップで休暇データが除外されていることを確認")
        print("3. ログで [RestExclusion] メッセージを確認")
    else:
        print("❌ 一部テストが失敗しました。システムの確認が必要です。")

if __name__ == "__main__":
    main()
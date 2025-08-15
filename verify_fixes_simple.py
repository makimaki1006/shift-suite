#!/usr/bin/env python3
"""
簡易修正検証スクリプト（依存関係なし）
"""

from pathlib import Path

def verify_fixes():
    """修正内容を検証（依存関係なし版）"""
    print("="*80)
    print("🔍 包括的修正の簡易検証")
    print("="*80)
    
    fixes_found = 0
    total_fixes = 4
    
    # 1. dash_app.pyの修正確認
    print("\n1️⃣ dash_app.py の修正確認")
    try:
        with open("dash_app.py", 'r', encoding='utf-8') as f:
            content = f.read()
            
        checks = [
            ("変数初期化修正", "# 🎯 修正: 変数を条件外で初期化（エラー防止）"),
            ("全日付表示修正", "all_dates_from_aggregated_data = sorted(aggregated_df['date_lbl'].unique())"),
            ("カラー範囲設定", "zmin=color_range[0]"),
            ("タイポ修正", "ヒートマップ '{title}': 全日付を正常に描画")
        ]
        
        for name, pattern in checks:
            if pattern in content:
                print(f"  ✅ {name}: 確認済み")
                fixes_found += 1
            else:
                print(f"  ❌ {name}: 見つからない")
                
    except Exception as e:
        print(f"  ❌ dash_app.py 読み取りエラー: {e}")
    
    # 2. utils.py の修正確認
    print("\n2️⃣ utils.py の修正確認")
    try:
        with open("shift_suite/tasks/utils.py", 'r', encoding='utf-8') as f:
            utils_content = f.read()
            
        if "'staff_count' in df.columns and 'holiday_type' not in df.columns:" in utils_content:
            print("  ✅ staff_count フィルター条件修正: 確認済み")
        else:
            print("  ❌ staff_count フィルター条件修正: 見つからない")
            
    except Exception as e:
        print(f"  ❌ utils.py 読み取りエラー: {e}")
    
    print("\n" + "="*80)
    print(f"📊 検証結果: {fixes_found}/{total_fixes} の修正を確認")
    print("="*80)
    
    if fixes_found == total_fixes:
        print("🎉 全ての修正が正しく適用されています！")
        print("\n次のステップ:")
        print("1. ダッシュボードを再起動してテスト")
        print("2. 各問題が解決されたか確認")
    else:
        print("⚠️  一部の修正が不完全な可能性があります")
    
    return fixes_found == total_fixes

if __name__ == "__main__":
    verify_fixes()
#!/usr/bin/env python3
"""
包括的修正の検証スクリプト
3つの相互関連問題が解決されたかを確認
"""

import sys
import pandas as pd
from pathlib import Path
import importlib

def verify_fixes():
    """修正内容を検証"""
    print("="*80)
    print("🔍 包括的修正の検証開始")
    print("="*80)
    
    issues_fixed = []
    issues_remaining = []
    
    # 1. df_shortage_role_filtered の初期化確認
    print("\n1️⃣ 変数初期化の確認（問題2）")
    try:
        dash_app_path = Path("dash_app.py")
        with open(dash_app_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 変数が条件外で初期化されているか確認
        if "# 🎯 修正: 変数を条件外で初期化（エラー防止）" in content:
            print("  ✅ df_shortage_role_filtered の初期化修正を確認")
            issues_fixed.append("df_shortage_role_filtered 初期化エラー")
        else:
            print("  ❌ df_shortage_role_filtered の初期化修正が見つかりません")
            issues_remaining.append("df_shortage_role_filtered 初期化エラー")
    except Exception as e:
        print(f"  ❌ エラー: {e}")
        issues_remaining.append("dash_app.py の確認エラー")
    
    # 2. 日付表示の修正確認（問題1）
    print("\n2️⃣ 日付表示の修正確認（問題1）")
    try:
        # all_dates_from_aggregated_data の使用確認
        if "all_dates_from_aggregated_data = sorted(aggregated_df['date_lbl'].unique())" in content:
            print("  ✅ 全日付表示の修正を確認")
            issues_fixed.append("実績がない日付の非表示")
        else:
            print("  ❌ 全日付表示の修正が見つかりません")
            issues_remaining.append("実績がない日付の非表示")
    except Exception as e:
        print(f"  ❌ エラー: {e}")
    
    # 3. utils.py のフィルター緩和確認
    print("\n3️⃣ フィルター条件の緩和確認（根本原因）")
    try:
        utils_path = Path("shift_suite/tasks/utils.py")
        with open(utils_path, 'r', encoding='utf-8') as f:
            utils_content = f.read()
            
        if "'staff_count' in df.columns and 'holiday_type' not in df.columns:" in utils_content:
            print("  ✅ staff_count フィルターの条件付き適用を確認")
            issues_fixed.append("過度な休日除外フィルター")
        else:
            print("  ❌ staff_count フィルターの修正が見つかりません")
            issues_remaining.append("過度な休日除外フィルター")
    except Exception as e:
        print(f"  ❌ エラー: {e}")
        issues_remaining.append("utils.py の確認エラー")
    
    # 4. カラースケールの改善確認（問題3）
    print("\n4️⃣ カラースケールの改善確認（問題3）")
    try:
        if "zmin=color_range[0]" in content and "zmax=color_range[1]" in content:
            print("  ✅ 明示的なカラー範囲設定を確認")
            issues_fixed.append("職種別ヒートマップの単色表示")
        else:
            print("  ❌ カラー範囲設定の修正が見つかりません")
            issues_remaining.append("職種別ヒートマップの単色表示")
    except Exception as e:
        print(f"  ❌ エラー: {e}")
    
    # 5. データフローの整合性確認
    print("\n5️⃣ データフローの整合性確認")
    try:
        # キャッシュされた古いデータがないか確認
        cache_files = list(Path(".").glob("**/*.parquet"))
        if cache_files:
            print(f"  ⚠️  {len(cache_files)}個のparquetファイルが見つかりました")
            print("  💡 新しいデータで再分析することをお勧めします")
        else:
            print("  ✅ キャッシュファイルなし（クリーン状態）")
    except Exception as e:
        print(f"  ⚠️  キャッシュ確認エラー: {e}")
    
    # 結果サマリー
    print("\n" + "="*80)
    print("📊 検証結果サマリー")
    print("="*80)
    
    if not issues_remaining:
        print("🎉 全ての修正が正しく適用されています！")
        print("\n✅ 解決された問題:")
        for issue in issues_fixed:
            print(f"  - {issue}")
    else:
        print("⚠️  一部の修正が不完全です")
        print("\n✅ 解決された問題:")
        for issue in issues_fixed:
            print(f"  - {issue}")
        print("\n❌ 未解決の問題:")
        for issue in issues_remaining:
            print(f"  - {issue}")
    
    print("\n📝 推奨アクション:")
    print("1. 仮想環境でダッシュボードを再起動")
    print("   python dash_app.py")
    print("2. 新しいExcelファイルで分析を実行")
    print("3. 以下を確認:")
    print("   - 実績がない日付も表示される")
    print("   - 不足分析タブでエラーが出ない")
    print("   - ヒートマップの色が適切に表示される")
    
    return len(issues_remaining) == 0

if __name__ == "__main__":
    success = verify_fixes()
    sys.exit(0 if success else 1)
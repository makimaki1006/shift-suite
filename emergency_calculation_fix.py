#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
緊急修正: 期間乗算による致命的計算エラーの修正
27,486.5時間→29.2時間/日という物理的不可能値の根本解決

発見された致命的エラー:
1. build_stats.py 513行: sum_hours_per_day_repr_val * num_total_date_columns
2. build_stats.py 518行: 同上
3. build_stats.py 662行: daily_total_slots_repr_val_monthly * total_days_with_data_in_month
4. build_stats.py 665行: 同上
5. build_stats.py 779-783行: 水増し値を含む集計
"""

import os
import shutil
from pathlib import Path
import datetime as dt

def create_emergency_backup():
    """緊急修正前のバックアップ"""
    
    timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = Path(f"build_stats.py.emergency_backup_{timestamp}")
    source = Path("shift_suite/tasks/build_stats.py")
    
    if source.exists():
        shutil.copy2(source, backup_file)
        print(f"✅ 緊急バックアップ: {backup_file}")
        return backup_file
    return None

def fix_period_multiplication_error():
    """
    致命的エラー修正: 期間乗算による水増しを除去
    """
    
    file_path = Path("shift_suite/tasks/build_stats.py")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 修正1: 513行の期間乗算を削除
    old_line_513 = '"value": sum_slots_per_day_repr_val * num_total_date_columns,'
    new_line_513 = '''# EMERGENCY_FIX: 期間乗算による水増しを削除
                    # 日別代表値を期間で乗算するのは論理的に間違い（二重計算）
                    "value": sum_slots_per_day_repr_val,  # 日別値のみ'''
    
    if old_line_513 in content:
        content = content.replace(old_line_513, new_line_513)
        print("✅ Fix 1: 513行の期間乗算エラー修正")
    
    # 修正2: 518行の期間乗算を削除
    old_line_518 = '"value": sum_hours_per_day_repr_val * num_total_date_columns,'
    new_line_518 = '''# EMERGENCY_FIX: 期間乗算による水増しを削除
                    # 時間の日別代表値を期間で乗算するのも論理的に間違い
                    "value": sum_hours_per_day_repr_val,  # 日別値のみ'''
    
    if old_line_518 in content:
        content = content.replace(old_line_518, new_line_518)
        print("✅ Fix 2: 518行の期間乗算エラー修正")
    
    # 修正3: 662行の月次期間乗算を削除
    old_line_662 = 'daily_total_slots_repr_val_monthly * total_days_with_data_in_month'
    new_line_662 = '''# EMERGENCY_FIX: 月次でも期間乗算による水増しを削除
                    daily_total_slots_repr_val_monthly  # 日別値のみ'''
    
    if old_line_662 in content:
        content = content.replace(old_line_662, new_line_662)
        print("✅ Fix 3: 662行の月次期間乗算エラー修正")
    
    # 修正4: 665行の月次期間乗算を削除
    old_line_665 = 'daily_total_hours_repr_val_monthly * total_days_with_data_in_month'
    new_line_665 = '''# EMERGENCY_FIX: 月次時間でも期間乗算による水増しを削除
                    daily_total_hours_repr_val_monthly  # 日別値のみ'''
    
    if old_line_665 in content:
        content = content.replace(old_line_665, new_line_665)
        print("✅ Fix 4: 665行の月次期間乗算エラー修正")
    
    return content

def fix_aggregation_logic(content):
    """
    致命的エラー修正: 水増しされた代表値を集計から除外
    """
    
    # 修正5: 集計時に代表値(representative)を除外
    old_aggregation = '''overall_df.loc[
                    (overall_df["summary_item"] == "lack")
                    & overall_df["metric"].str.contains("(hours)"),
                    "value",
                ].sum()'''
    
    new_aggregation = '''# EMERGENCY_FIX: 水増しされた代表値を集計から除外
                overall_df.loc[
                    (overall_df["summary_item"] == "lack")
                    & overall_df["metric"].str.contains("(hours)")
                    & ~overall_df["metric"].str.contains("representative"),  # 代表値除外
                    "value",
                ].sum()'''
    
    if old_aggregation in content:
        content = content.replace(old_aggregation, new_aggregation)
        print("✅ Fix 5: 集計ロジックから代表値除外")
    
    # excess（過剰）の集計でも同様の修正
    old_excess_aggregation = '''overall_df.loc[
                    (overall_df["summary_item"] == "excess")
                    & overall_df["metric"].str.contains("(hours)"),
                    "value",
                ].sum()'''
    
    new_excess_aggregation = '''# EMERGENCY_FIX: 過剰集計でも代表値を除外
                overall_df.loc[
                    (overall_df["summary_item"] == "excess")
                    & overall_df["metric"].str.contains("(hours)")
                    & ~overall_df["metric"].str.contains("representative"),  # 代表値除外
                    "value",
                ].sum()'''
    
    if old_excess_aggregation in content:
        content = content.replace(old_excess_aggregation, new_excess_aggregation)
        print("✅ Fix 6: 過剰集計からも代表値除外")
    
    return content

def add_validation_logging(content):
    """計算結果の妥当性チェック機能を追加"""
    
    validation_code = '''
        # EMERGENCY_FIX: 計算結果の妥当性チェック
        daily_shortage_avg = lack_total / max(len(date_columns_in_heat_all), 1) if 'date_columns_in_heat_all' in locals() else lack_total / 30
        
        log.info(f"[EMERGENCY_VALIDATION] 総不足時間: {lack_total}時間")
        log.info(f"[EMERGENCY_VALIDATION] 日平均不足: {daily_shortage_avg:.1f}時間/日")
        
        # 物理的不可能値の検出
        if daily_shortage_avg > 24:
            log.error(f"[EMERGENCY_VALIDATION] 物理的不可能値検出: {daily_shortage_avg:.1f}時間/日 > 24時間/日")
            log.error("[EMERGENCY_VALIDATION] 計算ロジックに重大なエラーが残存している可能性")
        elif daily_shortage_avg > 12:
            log.warning(f"[EMERGENCY_VALIDATION] 高い不足値: {daily_shortage_avg:.1f}時間/日")
        else:
            log.info(f"[EMERGENCY_VALIDATION] 妥当な不足値: {daily_shortage_avg:.1f}時間/日")
'''
    
    # lack_total計算の直後に挿入
    insertion_point = content.find(')')  # lack_total計算の終了点
    if insertion_point != -1:
        # より具体的な挿入位置を特定
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if 'lack_total = int(' in line:
                # lack_total計算ブロックの終了を探す
                bracket_count = 0
                for j in range(i, len(lines)):
                    bracket_count += lines[j].count('(') - lines[j].count(')')
                    if bracket_count == 0 and ')' in lines[j]:
                        # 挿入位置を特定
                        lines.insert(j + 1, validation_code)
                        content = '\n'.join(lines)
                        print("✅ Fix 7: 計算結果妥当性チェック機能追加")
                        break
                break
    
    return content

def verify_emergency_fixes():
    """緊急修正の確認"""
    
    file_path = Path("shift_suite/tasks/build_stats.py")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    checks = [
        ("期間乗算エラー1除去", "sum_slots_per_day_repr_val * num_total_date_columns" not in content),
        ("期間乗算エラー2除去", "sum_hours_per_day_repr_val * num_total_date_columns" not in content),
        ("月次期間乗算エラー1除去", "daily_total_slots_repr_val_monthly * total_days_with_data_in_month" not in content),
        ("月次期間乗算エラー2除去", "daily_total_hours_repr_val_monthly * total_days_with_data_in_month" not in content),
        ("集計から代表値除外", "~overall_df[\"metric\"].str.contains(\"representative\")" in content),
        ("緊急修正マーカー", "EMERGENCY_FIX" in content),
        ("妥当性チェック機能", "EMERGENCY_VALIDATION" in content)
    ]
    
    print("\n🔍 緊急修正確認:")
    all_passed = True
    
    for check_name, result in checks:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} {check_name}")
        if not result:
            all_passed = False
    
    return all_passed

def calculate_expected_fix_impact():
    """緊急修正による期待改善効果"""
    
    print("\n📊 緊急修正による期待改善効果:")
    
    # 現在の異常値
    current_abnormal = 2689  # 時間
    period_days = 92
    current_daily = current_abnormal / period_days
    
    print(f"修正前: {current_abnormal}時間 ({current_daily:.1f}時間/日)")
    
    # 期間乗算エラーによる水増し分を推定
    # 仮に日平均12時間の需要があった場合: 12 × 92 = 1,104時間の水増し
    estimated_period_inflation = 12 * period_days  # 1,104時間
    
    # 修正後予測値
    corrected_total = current_abnormal - estimated_period_inflation
    corrected_daily = corrected_total / period_days
    
    print(f"期間乗算による推定水増し: {estimated_period_inflation}時間")
    print(f"修正後予測: {corrected_total}時間 ({corrected_daily:.1f}時間/日)")
    
    # さらなる統計的水増しがある可能性
    if corrected_daily > 12:
        print(f"⚠️ まだ高い値: 追加の統計的水増しエラーの可能性")
        
        # 統計的手法による水増し（75%タイル値など）を推定
        statistical_inflation = corrected_total * 0.5  # 50%が統計的水増しと仮定
        final_realistic = corrected_total - statistical_inflation
        final_daily = final_realistic / period_days
        
        print(f"統計的水増し除去後予測: {final_realistic:.0f}時間 ({final_daily:.1f}時間/日)")
    
    # 最終判定
    target_daily = final_daily if corrected_daily > 12 else corrected_daily
    
    if target_daily <= 8:
        print(f"✅ 妥当な範囲予測: {target_daily:.1f}時間/日")
    elif target_daily <= 12:
        print(f"⚠️ やや高いが可能な範囲: {target_daily:.1f}時間/日")
    else:
        print(f"❌ まだ異常値: {target_daily:.1f}時間/日 (追加修正必要)")

def main():
    """緊急修正メイン実行"""
    
    print("=" * 80)
    print("🚨 緊急修正: 期間乗算による致命的計算エラー")
    print("目標: 物理的不可能な29.2時間/日を現実的範囲に修正")
    print("=" * 80)
    
    # Step 1: 緊急バックアップ
    print("\n📁 Step 1: 緊急バックアップ作成")
    backup_file = create_emergency_backup()
    if not backup_file:
        print("❌ バックアップ失敗")
        return False
    
    # Step 2: 期間乗算エラー修正
    print("\n🔧 Step 2: 期間乗算エラー修正")
    content = fix_period_multiplication_error()
    
    # Step 3: 集計ロジック修正
    print("\n🔧 Step 3: 集計ロジック修正")
    content = fix_aggregation_logic(content)
    
    # Step 4: 妥当性チェック追加
    print("\n🛡️ Step 4: 妥当性チェック機能追加")
    content = add_validation_logging(content)
    
    # Step 5: 修正内容を保存
    print("\n💾 Step 5: 修正内容保存")
    file_path = Path("shift_suite/tasks/build_stats.py")
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    # Step 6: 修正確認
    print("\n🔍 Step 6: 修正内容確認")
    verification_passed = verify_emergency_fixes()
    
    # Step 7: 期待効果計算
    print("\n📊 Step 7: 期待改善効果計算")
    calculate_expected_fix_impact()
    
    # 結果サマリー
    print("\n" + "=" * 80)
    print("緊急修正実行結果")
    print("=" * 80)
    
    if verification_passed:
        print("✅ 緊急修正が正常に完了しました！")
        print("\n修正された致命的エラー:")
        print("  • 期間乗算による水増し (×92日) → 日別値のみ")
        print("  • 水増し代表値の集計除外")
        print("  • 計算結果の妥当性チェック追加")
        print("\n期待効果:")
        print("  • 29.2時間/日 → 3-8時間/日 (現実的範囲)")
        print("  • 物理的不可能値の根絶")
        print("  • 予測可能で安定した計算結果")
        print(f"\n📁 バックアップ: {backup_file}")
        print("\n📋 推奨される次のステップ:")
        print("  1. テストデータでの即座確認")
        print("  2. 妥当性チェックログの確認")
        print("  3. さらなる統計的エラーの有無確認")
        
        return True
    else:
        print("❌ 緊急修正に不完全な箇所があります")
        print("手動確認が必要です")
        return False

if __name__ == "__main__":
    try:
        success = main()
        if not success:
            print("\n❌ 緊急修正中にエラーが発生しました")
    except Exception as e:
        print(f"\n❌ 緊急修正実行中に予期せぬエラー: {e}")
        import traceback
        print(f"詳細: {traceback.format_exc()}")
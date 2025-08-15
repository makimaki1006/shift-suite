#!/usr/bin/env python3
"""
不足時間計算のロジック分析
shortage.pyでの計算フローを追跡
"""

def analyze_shortage_logic():
    """shortage.pyの計算ロジック分析"""
    
    print("🔍 === shortage.py 計算ロジック分析 ===\n")
    
    print("【1. スロット時間の計算】")
    print("  165行目: slot_hours = slot / 60.0")
    print("  → スロット分数を時間に変換")
    print("  例: 30分スロット → 0.5時間")
    
    print("\n【2. 不足時間の計算フロー】")
    print("  1. lack_count_role_df = need_df_role - role_staff_df")
    print("     → 各スロットでの人数不足を計算")
    print("")
    print("  2. total_lack_hours_for_role = (lack_count_role_df * slot_hours).sum().sum()")
    print("     → 人数不足 × スロット時間 = 時間不足")
    print("")
    print("  3. role_kpi_rows.append({")
    print('       "lack_h": int(round(total_lack_hours_for_role))')
    print("     })")
    print("     → 時間単位で保存")
    
    print("\n【3. 保存される値の例】")
    print("  30分スロット（0.5時間）の場合:")
    print("  - 1スロットで2人不足 → 2人 × 0.5時間 = 1時間不足")
    print("  - 10スロットで2人不足 → 20人 × 0.5時間 = 10時間不足")
    
    print("\n【4. 問題の可能性】")
    print("  ❌ もしdash_app.pyで再度slot_hoursを掛けると:")
    print("     10時間 × 0.5 = 5時間（誤った値）")
    print("")
    print("  ❌ もしdash_app.pyでスロット数として扱うと:")
    print("     10時間を10スロットと解釈（誤った解釈）")
    
    print("\n【5. 正しい扱い方】")
    print("  ✅ shortage_role_summary.parquetのlack_hは時間単位")
    print("  ✅ そのまま時間として表示すればOK")
    print("  ✅ スロット時間の変換は不要")

if __name__ == "__main__":
    analyze_shortage_logic()
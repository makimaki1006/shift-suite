#!/usr/bin/env python3
"""
不足時間の値をデバッグ
両方の計算方法での値を比較
"""

def analyze_shortage_calculation():
    """不足時間計算の分析"""
    
    print("🔍 === 不足時間計算の詳細分析 ===\n")
    
    print("【dash_app.pyでの2つの計算方法】\n")
    
    print("1️⃣ **概要タブ表示用（2642-2664行）**")
    print("   shortage_time.parquet（スロット数）から計算")
    print("   計算式: lack_h = total_shortage_slots * slot_hours")
    print("   例: 1000スロット × 0.5時間 = 500時間")
    print("")
    
    print("2️⃣ **KPI収集関数（573行）**")
    print("   shortage_role_summary.parquet（lack_h列）から直接取得")
    print("   計算式: total_shortage_hours = df['lack_h'].sum()")
    print("   例: 各職種のlack_h合計 = 500時間")
    print("")
    
    print("【問題の可能性】\n")
    
    print("❓ **可能性1: データの不整合**")
    print("   - shortage_time.parquetとshortage_role_summary.parquetで値が異なる")
    print("   - 原因: 計算タイミングや集計方法の違い")
    print("")
    
    print("❓ **可能性2: shortage.pyでの計算ミス**")
    print("   - lack_hが誤って大きな値で保存されている")
    print("   - 原因: slot_hoursの重複適用やデータ型の問題")
    print("")
    
    print("❓ **可能性3: 表示時の変換ミス**")
    print("   - 表示時に追加の変換が行われている")
    print("   - 原因: 単位変換の重複")
    print("")
    
    print("【推奨デバッグ手順】\n")
    
    print("1. **実データの確認**")
    print("   - shortage_time.parquetの総スロット数")
    print("   - shortage_role_summary.parquetのlack_h合計")
    print("   - 両者の比較")
    print("")
    
    print("2. **計算過程の追跡**")
    print("   - shortage.pyでのlack_h計算部分にログ追加")
    print("   - slot_hoursの値を確認")
    print("   - 中間値の確認")
    print("")
    
    print("3. **表示値の検証**")
    print("   - dash_app.pyでの最終表示値")
    print("   - どちらの計算方法が使われているか")
    print("   - 値の妥当性チェック")

if __name__ == "__main__":
    analyze_shortage_calculation()